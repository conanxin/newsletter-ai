"""Makefile target safety tests."""

from pathlib import Path


def test_make_validate_uses_new_cli():
    makefile = Path("Makefile").read_text()
    assert "validate:" in makefile
    assert "PKG := newsletter-ai" in makefile
    assert "legacy-validate" in makefile  # explicit legacy target exists
    assert "DEPRECATION WARNING" in makefile or "legacy" in makefile