import json
import os
from pathlib import Path

PRODUCTS = [
    ("ps5", "B0CKZGY5B6"),
    ("stanley", "B0CJZMP7L1"),
    ("jordans", "B0DJ9SVTB6"),
]

OUTPUT_DIR = Path("data/descriptions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for slug, asin in PRODUCTS:
    path = Path("data/raw") / f"{asin}_product.json"
    if not path.exists():
        print(f"[WARN] Missing {path}")
        continue
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lines = []
    title = data.get("title")
    if title:
        lines.append(title)
        lines.append("")

    bullets = data.get("bullet_points") or []
    if bullets:
        lines.append("Key Features:")
        for bp in bullets:
            lines.append(f"- {bp}")
        lines.append("")

    desc = data.get("description")
    if desc:
        lines.append("Description:")
        lines.append(desc)

    text = "\n".join(lines).strip()
    out_path = OUTPUT_DIR / f"{slug}.txt"
    out_path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {out_path}")


