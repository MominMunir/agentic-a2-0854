"""Publish the technical write-up as a standalone personal-blog page."""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inline(value):
    value = html.escape(value)
    value = re.sub(r"\[([^\]]+)\]\((https://[^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)


def main():
    source = (ROOT / "docs/Technical_Writeup.md").read_text(encoding="utf-8")
    count = len(source.split())
    assert 1200 <= count <= 1800, count
    blocks = []
    title = source.splitlines()[0].removeprefix("# ")
    for block in source.strip().split("\n\n"):
        if block.startswith("# "):
            continue
        if block.startswith("## "):
            blocks.append("<h2>" + inline(block[3:]) + "</h2>")
        elif block.startswith("- "):
            blocks.append("<ul>" + "".join("<li>" + inline(v[2:]) + "</li>" for v in block.splitlines()) + "</ul>")
        else:
            blocks.append("<p>" + inline(" ".join(block.splitlines())) + "</p>")
    body = "\n".join(blocks)
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="What six retrieval variants taught me while building GigBid for AI-4016.">
<title>{html.escape(title)} | Muhammad Momin Munir</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#fafbf8;color:#253b38;font:18px/1.8 system-ui,sans-serif}}
header,main,footer{{max-width:810px;margin:auto;padding:26px}}header{{border-bottom:1px solid #dce3dc}}
a{{color:#195d4b;text-underline-offset:4px}}h1{{font-size:clamp(32px,5vw,46px);line-height:1.2;margin:36px 0 18px}}
h2{{font-size:26px;line-height:1.3;margin:38px 0 14px}}p{{margin:0 0 20px}}.byline,footer{{font-size:15px;color:#5b6d63}}
code{{font-size:.9em;background:#edf2ed;padding:2px 4px;overflow-wrap:anywhere}}footer{{border-top:1px solid #dce3dc;margin-top:36px}}
</style></head><body>
<header><a href="/blog/gigbid">Muhammad Momin Munir</a> / Engineering notes</header>
<main><article><h1>{html.escape(title)}</h1><p class="byline">Muhammad Momin Munir · 15 November 2026 · {count:,} words</p>
{body}
</article></main><footer><p>Project: <a href="https://gigbid-wr80.onrender.com">GigBid</a> ·
<a href="https://github.com/MominMunir/agentic-a2-0854">Source and reproducible results</a></p>
<p>AI-4016 Assignment 02. Evaluation uses labeled synthetic fixtures; limitations are described in the article.</p></footer>
</body></html>'''
    target = ROOT / "apps/web/public/writeup.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    print(f"Personal-blog article built: {count} words.")


if __name__ == "__main__":
    main()
