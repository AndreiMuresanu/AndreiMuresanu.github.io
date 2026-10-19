"""Subset the Font Awesome webfonts to the icons listed in _sass/vendor/font-awesome/subset.scss.

The full, unsubset fonts are read from git history (the commit that added Font Awesome 6.5.2),
so this can be re-run whenever an icon is added to the lists in subset.scss.

Requires: pip install fonttools brotli
Usage:    python scripts/subset_fontawesome.py
"""

import io
import re
import subprocess
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SASS_DIR = ROOT / "_sass" / "vendor" / "font-awesome"
WEBFONTS = ROOT / "assets" / "webfonts"
FULL_FONTS_COMMIT = "d84c5b5"  # "FA bump to 6.5.2"


def scss_list(source, name):
    body = re.search(r"\$" + name + r":\s*\((.*?)\);", source, re.S).group(1)
    return re.findall(r'"([^"]+)"', body)


def codepoints(icon_names):
    variables = (SASS_DIR / "_variables.scss").read_text(encoding="utf-8")
    result = []
    for name in icon_names:
        match = re.search(r"^\$fa-var-" + re.escape(name) + r":\s*\\([0-9a-f]+);", variables, re.M)
        if not match:
            raise SystemExit(f"Unknown icon: {name}")
        result.append(int(match.group(1), 16))
    return result


def subset_font(font_name, unicodes):
    original = subprocess.run(
        ["git", "show", f"{FULL_FONTS_COMMIT}:assets/webfonts/{font_name}.ttf"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout

    options = subset.Options()
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True

    for flavor, ext in ((None, "ttf"), ("woff2", "woff2")):
        font = TTFont(io.BytesIO(original))
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=unicodes)
        subsetter.subset(font)
        font.flavor = flavor
        out = WEBFONTS / f"{font_name}.{ext}"
        font.save(out)
        print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1024:.1f} KiB")


def main():
    source = (SASS_DIR / "subset.scss").read_text(encoding="utf-8")
    subset_font("fa-solid-900", codepoints(scss_list(source, "fa-solid-used")))
    subset_font("fa-brands-400", codepoints(scss_list(source, "fa-brands-used")))


if __name__ == "__main__":
    main()
