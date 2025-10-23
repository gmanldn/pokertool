class Pokertool < Formula
  desc "AI-Powered Poker Analysis Tool"
  homepage "https://github.com/gmanldn/pokertool"
  url "https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "" # TODO: Add SHA256 checksum
  license "MIT"
  head "https://github.com/gmanldn/pokertool.git", branch: "main"

  depends_on "python@3.12"
  depends_on "postgresql@15" => :optional
  depends_on "redis" => :optional

  def install
    # Create virtual environment
    venv = virtualenv_create(libexec, "python3.12")
    
    # Install Python dependencies
    system libexec/"bin/pip", "install", "--no-cache-dir", "-r", "requirements.txt"
    
    # Install application
    venv.pip_install_and_link buildpath
    
    # Install configuration
    (etc/"pokertool").install "poker_config.example.json" => "poker_config.json"
    
    # Install data files
    (share/"pokertool").install "model_calibration_data"
    (share/"pokertool").install "ranges"
    (share/"pokertool").install "assets"
  end

  def post_install
    # Create necessary directories
    (var/"log/pokertool").mkpath
    (var/"lib/pokertool").mkpath
  end

  service do
    run [opt_bin/"pokertool", "server"]
    keep_alive true
    log_path var/"log/pokertool/output.log"
    error_log_path var/"log/pokertool/error.log"
    environment_variables PATH: std_service_path_env
  end

  test do
    system bin/"pokertool", "--version"
    assert_match "PokerTool", shell_output("#{bin}/pokertool --help")
  end
end
