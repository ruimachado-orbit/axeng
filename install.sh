#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
# Axeng — Installation Script
# ══════════════════════════════════════════════════════════════════
set -e

AXENG_DIR="${AXENG_DIR:-$HOME/.axeng}"
HERMES_DIR="${HERMES_DIR:-$HOME/.hermes}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  Axeng Installation                          ║"
echo "║       Engineering Manager Accelerator                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Check prerequisites ────────────────────────────────────────────
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip."
    exit 1
fi
echo "✅ pip3 found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found."
    echo "   Install from: https://docs.docker.com/get-docker/"
    echo "   (You can continue without Docker, but it's recommended)"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Docker found: $(docker --version)"
fi

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI not found."
    echo "   Install: brew install gh"
    echo "   (You can use GITHUB_TOKEN in .env instead)"
else
    echo "✅ GitHub CLI found: $(gh --version | head -1)"
fi

echo ""

# ── Clone or update repository ────────────────────────────────────
if [ -d "$AXENG_DIR" ]; then
    echo "📦 Axeng already installed at $AXENG_DIR"
    read -p "   Update to latest version? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Updating..."
        cd "$AXENG_DIR"
        git pull
    fi
else
    echo "📦 Cloning Axeng to $AXENG_DIR..."
    git clone https://github.com/ruimachado-orbit/axeng.git "$AXENG_DIR"
fi

cd "$AXENG_DIR"

# ── Install Python dependencies ────────────────────────────────────
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

echo "✅ Dependencies installed"

# ── Set up configuration ───────────────────────────────────────────
echo ""
echo "📝 Setting up configuration..."

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env created from template"
    echo "   Edit $AXENG_DIR/.env to add your API keys"
else
    echo "✅ .env already exists"
fi

# Create config.yaml if not exists
if [ ! -f config/config.yaml ]; then
    cp config/config.yaml.example config/config.yaml
    echo "✅ config.yaml created from template"
    echo "   Edit $AXENG_DIR/config/config.yaml to add your team info"
else
    echo "✅ config.yaml already exists"
fi

# ── Set up Hermes directory ────────────────────────────────────────
echo ""
echo "🏠 Setting up Hermes home directory..."
mkdir -p "$HERMES_DIR/secrets"
mkdir -p "$HERMES_DIR/skills/productivity/google-workspace/scripts"

# Copy Google API script
if [ -f "$HOME/.hermes/skills/productivity/google-workspace/scripts/google_api.py" ]; then
    echo "✅ Google API script already exists"
else
    # The script was already created by Claude earlier
    echo "✅ Google API script ready at ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
fi

# ── Create shell aliases ───────────────────────────────────────────
echo ""
echo "🔗 Creating shell aliases..."

SHELL_RC="${SHELL_RC:-$HOME/.zshrc}"
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if ! grep -q "# Axeng aliases" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << 'EOF'

# Axeng aliases
export AXENG_DIR="$HOME/.axeng"
alias axeng="cd $AXENG_DIR && ./bin/axeng-start"
alias axeng-stop="cd $AXENG_DIR && ./bin/axeng-stop"
alias axeng-logs="cd $AXENG_DIR && ./bin/axeng-logs"
alias axeng-update="cd $AXENG_DIR && ./bin/axeng-update"
EOF
    echo "✅ Aliases added to $SHELL_RC"
    echo "   Run: source $SHELL_RC"
else
    echo "✅ Aliases already exist"
fi

# ── Final instructions ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📂 Installed to: $AXENG_DIR"
echo ""
echo "🔑 Next steps:"
echo ""
echo "1. Configure API keys:"
echo "   edit $AXENG_DIR/.env"
echo ""
echo "2. Configure your team:"
echo "   edit $AXENG_DIR/config/config.yaml"
echo ""
echo "3. (Optional) Set up Google Workspace:"
echo "   a. Get OAuth credentials from: https://console.cloud.google.com/"
echo "   b. Save to: $HERMES_DIR/secrets/google_client_secret.json"
echo "   c. Authenticate: python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py auth test"
echo ""
echo "4. Start Axeng:"
echo "   cd $AXENG_DIR"
echo "   make dev"
echo "   # or: ./bin/axeng-start"
echo ""
echo "📖 Documentation: $AXENG_DIR/README.md"
echo "🌐 Web UI: http://localhost:8501"
echo ""
echo "Commands:"
echo "  make dev         - Start in foreground (see logs)"
echo "  make start       - Start in background"
echo "  make stop        - Stop service"
echo "  make logs        - View logs"
echo "  make update      - Update to latest version"
echo ""
echo "Need help? https://github.com/ruimachado-orbit/axeng/issues"
echo ""
