#!/bin/bash
# Axeng Next.js UI Setup Script

set -e

echo "🚀 Setting up Axeng Next.js UI..."
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    echo "Install it with: brew install node"
    exit 1
fi

echo "✅ Node.js $(node --version) found"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found!"
    exit 1
fi

echo "✅ npm $(npm --version) found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the UI:"
echo "  1. Start the API backend:  npm run api"
echo "  2. Start the Next.js dev server:  npm run dev"
echo "  3. Open http://localhost:3000"
echo ""
echo "Or use the convenience scripts:"
echo "  ./start.sh    - Start both API and UI"
echo "  ./dev.sh      - Development mode"
