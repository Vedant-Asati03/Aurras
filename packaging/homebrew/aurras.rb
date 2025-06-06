class Aurras < Formula
  include Language::Python::Virtualenv

  desc "High-end command line music player with YouTube and Spotify integration"
  homepage "https://github.com/vedant-asati03/Aurras"
  url "https://files.pythonhosted.org/packages/source/a/aurras/aurras-1.1.1.tar.gz"
  sha256 "PLACEHOLDER_SHA256_HASH"  # Will be updated when published
  license "MIT"

  depends_on "python@3.12"
  depends_on "mpv"

  def install
    virtualenv_install_with_resources
  end

  test do
    # Test that the commands work
    assert_match "Aurras", shell_output("#{bin}/aurras --version")
  end
end
