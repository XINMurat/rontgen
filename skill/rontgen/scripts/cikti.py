#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- extra output formats: what this machine can produce, and the
producing. Markdown is always the source; every other format is optional.

WHY THIS EXISTS
---------------
The owner's decision: Markdown is always written; Word, PDF, LaTeX and
images are offered, never required, and the skill says which ones this
environment can make before asking. A format that silently fails, or a
diagram that silently drops out of a document, is worse than no format.

  --yokla            one line per format: "uretilebilir" or "uretilemez: eksik X"
  --svg / --png      the block diagram from yapi.json: [K] solid, [H] dashed.
                     SVG needs nothing; PNG needs Pillow.
  --docx             the document set as one .docx, written with the standard
                     library (zip + XML): headings, lists, tables, code. Mermaid
                     blocks stay as source text with a "not drawn here" note,
                     unless a PNG of the block diagram was made, which is embedded.
  --tex              one compilable .tex source; compiled only if LaTeX exists.
  --pdf              through LaTeX or LibreOffice when present; otherwise refused
                     with the missing tool named.

USAGE
-----
    python cikti.py --yokla
    python cikti.py --docs rontgen-out --svg --png --docx --tex --pdf
    python cikti.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ORDER = ["okuma-sirasi.md", "mimari.md", "sozluk.md", "riskler.md"]


def yokla():
    def has_mod(m):
        try:
            __import__(m)
            return True
        except ImportError:
            return False
    pil = has_mod("PIL")
    latex = shutil.which("xelatex") or shutil.which("pdflatex") or shutil.which("lualatex")
    office = shutil.which("soffice") or shutil.which("libreoffice")
    mmdc = shutil.which("mmdc")
    word = None
    if os.name == "nt" and shutil.which("powershell"):
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "[bool][type]::GetTypeFromProgID('Word.Application')"], capture_output=True, text=True)
        word = "Word" if r.stdout.strip() == "True" else None
    office = office or word
    return {
        "md": (True, None), "svg": (True, None), "png": (pil, None if pil else "Pillow"),
        "docx": (True, None), "tex": (True, None),
        "pdf": (bool(latex or office), None if (latex or office) else "LaTeX (xelatex/pdflatex), LibreOffice ya da Word"),
        "mermaid": (bool(mmdc), None if mmdc else "mmdc (Mermaid CLI); sema kaynak metin olarak kalir"),
    }, {"latex": latex, "office": office, "mmdc": mmdc}


def layout(y, limit=14):
    """-> (nodes {name: (x, y)}, edges [(a, b, tier)]): strongest modules, layered by longest [K] path."""
    edges = [(e["from"], e["to"], e["tier"], e["files"]) for e in y.get("edges", []) if not e.get("weak")]
    weight = {}
    for a, b, _, n in edges:
        weight[a] = weight.get(a, 0) + n
        weight[b] = weight.get(b, 0) + n
    keep = set(sorted(weight, key=lambda m: -weight[m])[:limit])
    edges = [(a, b, t) for a, b, t, _ in edges if a in keep and b in keep and a != b]
    # A cycle pushed every member to the cap: 13 boxes in one row under an empty page (a 175k-file Lean release).
    # Break cycles first: a [K] edge back onto the DFS stack is drawn but does not layer.
    out = {m: [] for m in keep}
    for a, b, t in edges:
        if t == "K":
            out[a].append(b)
    back, state = set(), {}

    def dfs(m):
        state[m] = 1
        for n in sorted(out[m], key=lambda n: -weight[n]):
            if state.get(n) == 1:
                back.add((m, n))
            elif n not in state:
                dfs(n)
        state[m] = 2
    for m in sorted(keep, key=lambda m: -weight[m]):
        if m not in state:
            dfs(m)
    level = {m: 0 for m in keep}
    for _ in range(len(keep)):
        changed = False
        for a, b, t in edges:
            if t == "K" and (a, b) not in back and level[b] < level[a] + 1:
                level[b] = level[a] + 1; changed = True
        if not changed:
            break
    rows, r = {}, 0
    for lv in sorted(set(level.values())):
        ms = sorted((m for m in keep if level[m] == lv), key=lambda m: -weight[m])
        for i in range(0, len(ms), ROW):     # a wide layer wraps instead of running off the page
            rows[r] = ms[i:i + ROW]; r += 1
    pos = {}
    for r, ms in rows.items():
        for i, m in enumerate(ms):
            pos[m] = (40 + i * 230, 40 + r * 110)
    return pos, edges


ROW = 5


def label(m: str) -> str:
    """The last two path parts if they fit, else the last one: `Development/WeilBound`, never `elopment/...`."""
    for s in ("/".join(m.split("/")[-2:]), m.split("/")[-1]):    # parent too, when it fits; never a cut word
        if len(s) <= 30:
            return s
    return "…" + s[-29:]


def svg(y):
    pos, edges = layout(y)
    w = max([x for x, _ in pos.values()] + [0]) + 240
    h = max([v for _, v in pos.values()] + [0]) + 100
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="sans-serif" font-size="12">',
         '<defs><marker id="o" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0L10,5L0,10z"/></marker></defs>']
    for a, b, t in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        dash = "" if t == "K" else ' stroke-dasharray="6,4"'
        o.append(f'<line x1="{x1 + 100}" y1="{y1 + 44}" x2="{x2 + 100}" y2="{y2}" stroke="#333"{dash} marker-end="url(#o)"/>')
    for m, (x, yy) in pos.items():
        o.append(f'<rect x="{x}" y="{yy}" width="200" height="44" rx="6" fill="#f4f4f4" stroke="#333"/>')
        o.append(f'<text x="{x + 100}" y="{yy + 27}" text-anchor="middle">{html.escape(label(m))}</text>')
    o.append(f'<text x="10" y="{h - 10}" fill="#555">[K] duz cizgi: beyan edilmis bag. [H] kesik: ad eslesmesi. '
             f'{len(pos)} modul gosterildi; tam grafik yapi.json.</text></svg>')
    return "\n".join(o) + "\n"


def png(y, path):
    from PIL import Image, ImageDraw
    pos, edges = layout(y)
    w = max([x for x, _ in pos.values()] + [0]) + 240
    h = max([v for _, v in pos.values()] + [0]) + 100
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    for a, b, t in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        p1, p2 = (x1 + 100, y1 + 44), (x2 + 100, y2)
        if t == "K":
            d.line([p1, p2], fill="#333", width=2)
        else:
            n = 12
            for i in range(0, n, 2):
                d.line([(p1[0] + (p2[0] - p1[0]) * i / n, p1[1] + (p2[1] - p1[1]) * i / n),
                        (p1[0] + (p2[0] - p1[0]) * (i + 1) / n, p1[1] + (p2[1] - p1[1]) * (i + 1) / n)], fill="#333", width=2)
        d.ellipse([p2[0] - 4, p2[1] - 4, p2[0] + 4, p2[1] + 4], fill="#333")
    for m, (x, yy) in pos.items():
        d.rounded_rectangle([x, yy, x + 200, yy + 44], 6, fill="#f4f4f4", outline="#333")
        d.text((x + 8, yy + 15), label(m), fill="black")
    d.text((10, h - 20), "[K] duz cizgi, [H] kesik; tam grafik yapi.json", fill="#555")
    im.save(path)


def doc_files(docs):
    found = [os.path.join(docs, n) for n in ORDER if os.path.exists(os.path.join(docs, n))]
    for sub in ("moduller", "akislar"):
        found += sorted(glob.glob(os.path.join(docs, sub, "*.md")))
    return found


def blocks(text):
    """Markdown -> [(kind, payload)]: h1..h3, li, table(rows), code(lang, text), p."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        s = lines[i]
        if s.startswith("```"):
            lang, j = s[3:].strip(), i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append(("code", (lang, "\n".join(lines[i + 1:j])))); i = j + 1; continue
        if s.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            out.append(("table", rows)); continue
        m = re.match(r"^(#{1,3})\s+(.*)", s)
        if m:
            out.append((f"h{len(m.group(1))}", m.group(2)))
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s+", s):
            out.append(("li", re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", s)))
        elif s.strip():
            out.append(("p", s.strip()))
        i += 1
    return out


def plain(s):
    return re.sub(r"\*\*|__|\*", "", s)


def x(s):
    return html.escape(s, quote=False)


def runs(s):
    parts, o = re.split(r"(`[^`]+`)", plain(s)), []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            o.append(f'<w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr><w:t xml:space="preserve">{x(p[1:-1])}</w:t></w:r>')
        elif p:
            o.append(f'<w:r><w:t xml:space="preserve">{x(p)}</w:t></w:r>')
    return "".join(o)


def para(s, style=None):
    st = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{st}{runs(s)}</w:p>"


def docx(docs, out, image=None, note=""):
    body = [para("Rontgen belge seti", "Title"), para(note or "Kaynak: Markdown belgeleri; atiflar oldugu gibi korunur.")]
    for f in doc_files(docs):
        with io.open(f, encoding="utf-8") as fh:
            for kind, p in blocks(fh.read()):
                if kind in ("h1", "h2", "h3"):
                    body.append(para(p, {"h1": "Heading1", "h2": "Heading2", "h3": "Heading3"}[kind]))
                elif kind == "li":
                    body.append(para("• " + p))
                elif kind == "p":
                    body.append(para(p))
                elif kind == "table" and p:
                    rows = "".join("<w:tr>" + "".join(f"<w:tc>{para(c)}</w:tc>" for c in r) + "</w:tr>" for r in p)
                    body.append('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
                                '<w:tblBorders><w:top w:val="single" w:sz="4"/><w:bottom w:val="single" w:sz="4"/>'
                                '<w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/></w:tblBorders>'
                                f"</w:tblPr>{rows}</w:tbl>")
                elif kind == "code":
                    lang, text = p
                    if lang == "mermaid":
                        body.append(para("[Diyagram bu ortamda cizilemedi: eksik mmdc (Mermaid CLI). Kaynak metin asagida.]"))
                    for line in text.splitlines() or [""]:
                        body.append(f'<w:p><w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/></w:rPr>'
                                    f'<w:t xml:space="preserve">{x(line)}</w:t></w:r></w:p>')
    rels = ""
    if image:
        body.insert(2, para("Blok semasi (yapi.json, [K] duz / [H] kesik)", "Heading1"))
        body.insert(3, '<w:p><w:r><w:drawing><wp:inline><wp:extent cx="5400000" cy="3000000"/><wp:docPr id="1" name="blok"/>'
                       '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData '
                       'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/'
                       'drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="1" name="blok.png"/><pic:cNvPicPr/></pic:nvPicPr>'
                       '<pic:blipFill><a:blip r:embed="rImg"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr>'
                       '<a:xfrm><a:off x="0" y="0"/><a:ext cx="5400000" cy="3000000"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>'
                       '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
        rels = '<Relationship Id="rImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/blok.png"/>'
    ns = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"')
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/'
              'wordprocessingml/2006/main">' + "".join(
                  f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:pPr><w:outlineLvl w:val="{lvl}"/></w:pPr>'
                  f'<w:rPr><w:b/><w:sz w:val="{sz}"/></w:rPr></w:style>'
                  for sid, name, lvl, sz in (("Title", "Title", 0, 40), ("Heading1", "heading 1", 0, 32),
                                             ("Heading2", "heading 2", 1, 28), ("Heading3", "heading 3", 2, 24)))
              + '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/></w:style></w:styles>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
                   'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" '
                   'ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
                   'officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType='
                   '"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                   'relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/_rels/document.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship Id="rSt" Type="http://schemas.openxmlformats.org/'
                   f'officeDocument/2006/relationships/styles" Target="styles.xml"/>{rels}</Relationships>')
        z.writestr("word/styles.xml", styles)
        z.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {ns}><w:body>'
                   + "".join(body) + "<w:sectPr/></w:body></w:document>")
        if image:
            z.write(image, "word/media/blok.png")


TEX_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def tx(s):
    return "".join(TEX_ESC.get(c, c) for c in plain(s)).replace("`", "")


def tex(docs):
    o = [r"\documentclass{article}", r"\usepackage{fontspec}", r"\usepackage{longtable}", r"\usepackage{fancyvrb}",
         r"\begin{document}", r"\title{Rontgen belge seti}", r"\maketitle", r"\tableofcontents"]
    for f in doc_files(docs):
        with io.open(f, encoding="utf-8") as fh:
            for kind, p in blocks(fh.read()):
                if kind in ("h1", "h2", "h3"):
                    o.append({"h1": r"\section{%s}", "h2": r"\subsection{%s}", "h3": r"\subsubsection{%s}"}[kind] % tx(p))
                elif kind in ("p", "li"):
                    o.append(("\\noindent$\\bullet$ " if kind == "li" else "") + tx(p) + "\n")
                elif kind == "table" and p:
                    n = max(len(r) for r in p)
                    o.append(r"\begin{longtable}{%s}" % ("|p{%.2f\\linewidth}" % (0.9 / n) * n + "|") + r"\hline")
                    o += [" & ".join(tx(c) for c in r + [""] * (n - len(r))) + r" \\ \hline" for r in p]
                    o.append(r"\end{longtable}")
                elif kind == "code":
                    o += [r"\begin{Verbatim}[fontsize=\small]", p[1], r"\end{Verbatim}"]
    o.append(r"\end{document}")
    return "\n".join(o) + "\n"


def self_test() -> int:
    ok = []

    def t(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    caps, _ = yokla()
    t("yokla: her bicim icin bir satir, md ve svg her zaman", set(caps) >= {"md", "svg", "png", "docx", "tex", "pdf"}
      and caps["md"][0] and caps["svg"][0] and all(ok_ or why for ok_, why in caps.values()))
    y = {"edges": [{"from": "a", "to": "b", "tier": "K", "files": 3}, {"from": "b", "to": "c", "tier": "H", "files": 1},
                   {"from": "c", "to": "d", "tier": "H", "files": 1, "weak": True}]}
    s = svg(y)
    t("svg: [K] duz, [H] kesik, zayif bag cizilmez", s.count("<line") == 2 and s.count("stroke-dasharray") == 1 and ">d<" not in s)
    pos, _ = layout(y)
    t("yerlesim: [K] bag katman atlatir", pos["b"][1] > pos["a"][1])
    ring = {"edges": [{"from": f"m{i}", "to": f"m{(i + 1) % 8}", "tier": "K", "files": 9 - i} for i in range(8)]
            + [{"from": "m0", "to": f"m{i}", "tier": "K", "files": 1} for i in range(2, 8)]}
    pos, _ = layout(ring)
    rows = {}
    for x_, y_ in pos.values():
        rows[y_] = rows.get(y_, 0) + 1
    t("yerlesim: dongu tek satira yigilmaz, ust satir bos kalmaz, satir en cok ROW kutu",
      min(rows) == 40 and len(rows) >= 2 and max(rows.values()) <= ROW)
    t("etiket: son iki parca, bastan kesilir", label("src/Development/WeilBound") == "Development/WeilBound"
      and label("src/Development/AbelianVarietyTheory") == "AbelianVarietyTheory"
      and label("a/" + "x" * 40).startswith("…") and len(label("a/" + "x" * 40)) == 30)
    with tempfile.TemporaryDirectory() as d:
        with io.open(os.path.join(d, "mimari.md"), "w", encoding="utf-8") as f:
            f.write("# Mimari\n\nMetin `a.rs:1` & <x>.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```mermaid\nflowchart LR\n```\n- madde\n")
        p = os.path.join(d, "o.docx")
        docx(d, p)
        with zipfile.ZipFile(p) as z:
            doc = z.read("word/document.xml").decode("utf-8")
        t("docx: gecerli zip, baslik, tablo, kacisli metin, atif korunur", "Heading1" in doc and "<w:tbl>" in doc
          and "&amp; &lt;x&gt;" in doc and "a.rs:1" in doc)
        t("docx: mermaid sessizce dusmez, not + kaynak", "cizilemedi" in doc and "flowchart LR" in doc)
        tt = tex(d)
        t("tex: bolum, tablo, kacis", r"\section{Mimari}" in tt and r"\begin{longtable}" in tt and r"\&" in tt)
        if caps["png"][0]:
            png(y, os.path.join(d, "b.png"))
            t("png: Pillow ile dosya yazilir", os.path.getsize(os.path.join(d, "b.png")) > 100)
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--docs", default="rontgen-out")
    for f in ("yokla", "svg", "png", "docx", "tex", "pdf", "self-test"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    caps, tools = yokla()
    if a.yokla:
        for k, (ok_, why) in caps.items():
            print(f"{k:8} " + ("uretilebilir" if ok_ else f"uretilemez: eksik {why}"))
        return 0
    rc = 0
    y = None
    if a.svg or a.png or a.docx:
        try:
            with io.open(os.path.join(a.docs, "yapi.json"), encoding="utf-8") as f:
                y = json.load(f)
        except OSError:
            print("olculmedi: yapi.json yok; blok semasi cizilmedi")
    img = None
    if y and a.svg:
        with io.open(os.path.join(a.docs, "blok.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(y))
        print("yazildi: blok.svg")
    if y and (a.png or a.docx) and caps["png"][0]:
        img = os.path.join(a.docs, "blok.png"); png(y, img); print("yazildi: blok.png")
    elif a.png:
        print(f"uretilemez png: eksik {caps['png'][1]}"); rc = 2
    if a.docx:
        docx(a.docs, os.path.join(a.docs, "rontgen.docx"), img,
             "Uretim: cikti.py (standart kutuphane, zip + XML)" + (", sema Pillow ile" if img else ", sema yok (Pillow eksik)") + ".")
        print("yazildi: rontgen.docx")
    if a.tex or a.pdf:
        p = os.path.join(a.docs, "rontgen.tex")
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(tex(a.docs))
        print("yazildi: rontgen.tex" + ("" if tools["latex"] else " (LaTeX yok: derlenmedi, yalniz kaynak)"))
    if a.pdf:
        if tools["latex"]:
            r = subprocess.run([tools["latex"], "-interaction=nonstopmode", "rontgen.tex"], cwd=a.docs, capture_output=True)
            print("yazildi: rontgen.pdf (LaTeX: " + os.path.basename(tools["latex"]) + ")" if r.returncode == 0 else "pdf: LaTeX hata verdi")
        elif tools["office"]:
            src = os.path.abspath(os.path.join(a.docs, "rontgen.docx"))
            if not os.path.exists(src):
                docx(a.docs, src, img)
            if tools["office"] == "Word":
                ps = (f"$w=New-Object -ComObject Word.Application;$w.Visible=$false;$d=$w.Documents.Open('{src}',$false,$true);"
                      f"$d.SaveAs2('{src[:-5]}.pdf',17);$d.Close($false);$w.Quit()")
                subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
            else:
                subprocess.run([tools["office"], "--headless", "--convert-to", "pdf", "rontgen.docx"], cwd=a.docs, capture_output=True)
            ok_ = os.path.exists(src[:-5] + ".pdf")
            print(f"{'yazildi' if ok_ else 'uretilemedi'}: rontgen.pdf (yol: {os.path.basename(tools['office'])}, rontgen.docx uzerinden)")
            rc = rc if ok_ else 2
        else:
            print(f"uretilemez pdf: eksik {caps['pdf'][1]}"); rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
