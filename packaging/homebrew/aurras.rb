class Aurras < Formula
  include Language::Python::Virtualenv

  desc "High-end command-line music player"
  homepage "https://github.com/vedant-asati03/Aurras"
  url "https://files.pythonhosted.org/packages/26/24/dbba92cb1733bcc4d52f291025888a085e7d27caa0175800fb3b823e0f80/aurras-2.0.2.tar.gz"
  sha256 "29d44100e708d0f087150ed3cfb98592865a5763034d93268209f18a6eb7165d"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "mpv"
  depends_on "python@3.13"

  def install
    virtualenv_create(libexec, "python@3.13")
    system libexec/"bin/pip", "install", *std_pip_args, "."
    bin.install_symlink libexec/"bin/aurras"
    bin.install_symlink libexec/"bin/aurras-tui"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/aurras --version 2>&1")

    output = shell_output("#{bin}/aurras theme minimal 2>&1")
    assert_match "Theme set to Minimal and saved as default", output
  end
end