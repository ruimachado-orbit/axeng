class Axeng < Formula
  desc "Engineering Manager Accelerator - AI chief of staff for dev teams"
  homepage "https://github.com/ruimachado-orbit/axeng"
  url "https://github.com/ruimachado-orbit/axeng/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256" # Update when creating release
  license "MIT"
  head "https://github.com/ruimachado-orbit/axeng.git", branch: "main"

  depends_on "python@3.12"
  depends_on "gh"
  depends_on "docker"

  def install
    # Create installation directory
    libexec.install Dir["*"]

    # Install Python dependencies
    system libexec/"bin/pip3", "install", "-r", libexec/"requirements.txt"

    # Create wrapper scripts
    (bin/"axeng").write <<~EOS
      #!/bin/bash
      export AXENG_HOME="#{libexec}"
      cd "#{libexec}" && exec "#{libexec}/bin/axeng-start" "$@"
    EOS

    (bin/"axeng-stop").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec "#{libexec}/bin/axeng-stop" "$@"
    EOS

    (bin/"axeng-logs").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec "#{libexec}/bin/axeng-logs" "$@"
    EOS

    (bin/"axeng-update").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec "#{libexec}/bin/axeng-update" "$@"
    EOS

    # Make scripts executable
    chmod 0755, bin/"axeng"
    chmod 0755, bin/"axeng-stop"
    chmod 0755, bin/"axeng-logs"
    chmod 0755, bin/"axeng-update"

    # Create config directories
    (var/"axeng/config").mkpath
    (var/"axeng/reports").mkpath

    # Copy example configs if not exists
    unless File.exist?("#{var}/axeng/.env")
      cp libexec/".env.example", "#{var}/axeng/.env"
    end

    unless File.exist?("#{var}/axeng/config/config.yaml")
      cp libexec/"config/config.yaml.example", "#{var}/axeng/config/config.yaml"
    end

    # Create symlinks for configs
    (libexec/".env").make_relative_symlink("#{var}/axeng/.env")
    (libexec/"config/config.yaml").make_relative_symlink("#{var}/axeng/config/config.yaml")

    # Set up Hermes directory for Google API
    hermes_dir = Pathname.new(ENV["HOME"])/"/.hermes"
    hermes_dir.mkpath
    (hermes_dir/"secrets").mkpath
    (hermes_dir/"skills/productivity/google-workspace/scripts").mkpath

    # Copy Google API script
    cp libexec/"src/tools/google_api.py", hermes_dir/"skills/productivity/google-workspace/scripts/google_api.py"
    chmod 0755, hermes_dir/"skills/productivity/google-workspace/scripts/google_api.py"
  end

  def post_install
    puts ""
    puts "✅ Axeng installed!"
    puts ""
    puts "Configuration files:"
    puts "  .env:        #{var}/axeng/.env"
    puts "  config.yaml: #{var}/axeng/config/config.yaml"
    puts ""
    puts "Next steps:"
    puts "  1. Edit your config: #{var}/axeng/.env"
    puts "  2. Add your API keys (GitHub, Linear, LLM provider)"
    puts "  3. Start Axeng: axeng"
    puts ""
    puts "Optional - Google Workspace (Calendar/Gmail):"
    puts "  1. Get OAuth credentials from Google Cloud Console"
    puts "  2. Save to: ~/.hermes/secrets/google_client_secret.json"
    puts "  3. Authenticate: python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py auth test"
    puts ""
    puts "Commands:"
    puts "  axeng         - Start the service"
    puts "  axeng-stop    - Stop the service"
    puts "  axeng-logs    - View logs"
    puts "  axeng-update  - Update to latest version"
    puts ""
  end

  def caveats
    <<~EOS
      Axeng requires Docker to be running.
      Install Docker Desktop from: https://docs.docker.com/get-docker/

      Configuration:
        .env:        #{var}/axeng/.env
        config.yaml: #{var}/axeng/config/config.yaml

      Access the web UI at: http://localhost:8501
    EOS
  end

  test do
    system "#{bin}/axeng", "--version"
  end
end
