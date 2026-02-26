#!/usr/bin/env python3
"""
generate.py — Génère docs/dist/index.html depuis README.md
Extrait automatiquement : titre, badges, images, contenu Markdown
"""

import re
import os
import markdown
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent          # Racine du repo
README   = ROOT / "README.md"
TEMPLATE = ROOT / "template.html"
DIST     = ROOT / "dist" / "about"
DIST.mkdir(parents=True, exist_ok=True)
OUTPUT   = DIST / "index.html"

# ── Lecture du README ─────────────────────────────────────────────────────────
raw = README.read_text(encoding="utf-8")
lines = raw.splitlines()

# ── Extraction des images GitHub ──────────────────────────────────────────────
IMG_PATTERN = re.compile(
    r'(?:<img[^>]+src="([^"]+)"[^>]*>|!\[[^\]]*\]\(([^)]+)\))'
)
images = []
for line in lines:
    for m in IMG_PATTERN.finditer(line):
        url = m.group(1) or m.group(2)
        if url and url.startswith("http"):
            images.append(url)

# Dédupliquer en gardant l'ordre
seen = set()
images = [u for u in images if not (u in seen or seen.add(u))]

banner_img   = images[0] if len(images) > 0 else ""
hero_imgs    = images[1:3]   # 1ère et 2ème captures plein-écran
grid_imgs    = images[3:]    # Le reste en grille

# ── Extraction du titre et sous-titre ─────────────────────────────────────────
title    = "McIntosh Reference Digital Audio Player"
subtitle = ""
for line in lines:
    if line.startswith("# "):
        title = line[2:].strip()
    elif line.startswith("## Inspired"):
        subtitle = line[3:].strip()
    if title and subtitle:
        break

# ── Extraction des badges ─────────────────────────────────────────────────────
BADGE_PATTERN = re.compile(r'!\[([^\]]+)\]\(https://img\.shields\.io/badge/([^)]+)\)')
badges_html = ""
for line in lines:
    for m in BADGE_PATTERN.finditer(line):
        label_raw = m.group(2)          # ex: "status-active-success"
        parts = label_raw.split("-")
        if len(parts) >= 3:
            name  = parts[0].upper()
            value = "-".join(parts[1:-1]).upper()
            color_key = parts[-1]       # success / green / blue
            css_class = {
                "success": "badge-green",
                "green":   "badge-green",
                "blue":    "badge-blue",
                "gold":    "badge-gold",
            }.get(color_key, "badge-gold")
            badges_html += f'<span class="badge {css_class}">{name}: {value}</span>\n'

# ── Conversion Markdown → HTML (corps principal) ───────────────────────────────
# On retire les lignes d'images pures et les badges pour ne garder que le texte
clean_lines = []
skip_next = False
for line in lines:
    # Sauter les images standalone
    if re.match(r'^!\[', line) or re.match(r'^<img\s', line):
        continue
    # Sauter les lignes de badges shields.io
    if "img.shields.io/badge" in line:
        continue
    # Sauter le titre H1 et le sous-titre H2 "Inspired" (déjà dans le hero)
    if line.startswith("# "):
        continue
    if line.startswith("## Inspired"):
        continue
    clean_lines.append(line)

md_content = "\n".join(clean_lines)

# Convertir en HTML
md = markdown.Markdown(
    extensions=[
        "fenced_code",
        "tables",
        "toc",
        "attr_list",
        "nl2br",
    ]
)
body_html = md.convert(md_content)

# Post-traitement : adapter les classes HTML au style McIntosh
body_html = body_html.replace("<h2>", '<h2 class="md-h2">')
body_html = body_html.replace("<h3>", '<h3 class="md-h3">')
body_html = body_html.replace("<h4>", '<h4 class="md-h4">')
body_html = body_html.replace("<p>",  '<p class="md-p">')
body_html = body_html.replace("<ul>", '<ul class="md-ul">')
body_html = body_html.replace("<ol>", '<ol class="md-ol">')
body_html = body_html.replace("<li>", '<li class="md-li">')
body_html = body_html.replace("<pre>", '<pre class="md-pre">')
body_html = body_html.replace("<blockquote>", '<blockquote class="md-blockquote">')
body_html = body_html.replace("<hr>",  '<div class="divider"></div>')
body_html = body_html.replace("<table>", '<table class="md-table">')

# ── Génération des blocs d'images ─────────────────────────────────────────────
def img_tag(url, alt="Screenshot"):
    return f'<img src="{url}" alt="{alt}" loading="lazy">'

screenshots_html = ""
if hero_imgs:
    for url in hero_imgs:
        screenshots_html += f'<div class="ss-full">{img_tag(url)}</div>\n'
if grid_imgs:
    screenshots_html += '<div class="ss-grid">\n'
    for url in grid_imgs:
        screenshots_html += f'  {img_tag(url)}\n'
    screenshots_html += '</div>\n'

# ── Injection dans le template ─────────────────────────────────────────────────
template = TEMPLATE.read_text(encoding="utf-8")

html = (template
    .replace("{{TITLE}}",       title)
    .replace("{{SUBTITLE}}",    subtitle)
    .replace("{{BANNER_IMG}}",  banner_img)
    .replace("{{BADGES}}",      badges_html)
    .replace("{{SCREENSHOTS}}", screenshots_html)
    .replace("{{CONTENT}}",     body_html)
)

OUTPUT.write_text(html, encoding="utf-8")
print(f"✅  Generated: {OUTPUT}")
print(f"   Title   : {title}")
print(f"   Images  : {len(images)} found")
