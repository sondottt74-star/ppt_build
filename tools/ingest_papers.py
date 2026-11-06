#!/usr/bin/env python3
"""Ingest papers given as LaTeX source and index everything a deck needs.

    python tools/ingest_papers.py <talk_dir>/papers \\
        scaffold-gs=~/dl/arXiv-2312.00109v1.tar.gz \\
        octree-gs=~/dl/arXiv-2403.17898v2/ \\
        proxy-gs=2509.24421v5            # bare arXiv id -> download the e-print source

Each source may be a .tar.gz / .tgz / .tar / .zip, an extracted directory, a single .tex, or an arXiv id.
For every paper <key> this writes

    papers/<key>/src/                  LaTeX source (directories are symlinked, archives extracted)
    papers/<key>/index.md              title, abstract, sections, figures (F#), tables (T#), equations (E#)
    papers/<key>/flat.tex              main file with \\input/\\include inlined and comments stripped
    papers/<key>/figures.json          machine-readable figure list
    papers/<key>/figures_sheet_N.png   labelled thumbnails of every figure file (look at these to choose)

Re-running on an existing key re-indexes without re-downloading.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import tarfile
import urllib.request
import zipfile
from pathlib import Path

IMG_EXTS = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps"]
ARXIV_RE = re.compile(r"^(?:arxiv[:\-_]?)?(\d{4}\.\d{4,5}(?:v\d+)?)$", re.I)


# ------------------------------------------------------------------ fetching / unpacking
def unpack(spec, dest):
    """Materialize `spec` as a source directory at dest (papers/<key>/src)."""
    if dest.exists() or dest.is_symlink():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    p = Path(os.path.expanduser(spec))
    m = ARXIV_RE.match(spec.strip()) or ARXIV_RE.match(p.name.replace(".tar.gz", ""))
    if p.is_dir():
        dest.symlink_to(p.resolve(), target_is_directory=True)
        return dest
    if p.is_file():
        data = p.read_bytes()
        name = p.name
    elif m:
        url = f"https://arxiv.org/e-print/{m.group(1)}"
        print(f"  downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "ppt_build/1.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        name = m.group(1)
    else:
        raise SystemExit(f"cannot interpret source '{spec}' (path, archive or arXiv id)")
    dest.mkdir(parents=True)
    if name.endswith(".zip"):
        zipfile.ZipFile(io.BytesIO(data)).extractall(dest)
    elif name.endswith(".tex"):
        (dest / name).write_bytes(data)
    else:
        raw = gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data
        try:
            with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
                tf.extractall(dest)
        except tarfile.ReadError:
            (dest / "main.tex").write_bytes(raw)  # arXiv single-file submissions are a gzipped .tex
    return dest


# ------------------------------------------------------------------ LaTeX helpers
def strip_comments(text):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def braced(text, start):
    """Content of the {...} group whose '{' is at or after `start`; returns (content, end_index)."""
    i = text.find("{", start)
    if i < 0:
        return "", start
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c == "\\":
            continue
        if c == "{" and text[j - 1] != "\\":
            depth += 1
        elif c == "}" and text[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
    return text[i + 1:], len(text)


def command_args(text, cmd):
    """All brace arguments of \\cmd{...} (skipping an optional [..])."""
    out = []
    for m in re.finditer(r"\\" + cmd + r"\*?\s*(\[[^\]]*\])?\s*\{", text):
        arg, _ = braced(text, m.end() - 1)
        out.append(arg)
    return out


def find_main(src):
    best, score = None, -1e9
    for f in src.rglob("*.tex"):
        try:
            t = f.read_text(errors="ignore")
        except OSError:
            continue
        if "\\documentclass" not in t:
            continue
        s = ("\\begin{document}" in t) * 10 + ("\\title" in t) * 5 + len(t) / 1e5
        s += 5 * (f.stem.lower() in ("main", "ms", "paper", "arxiv"))
        s -= 20 * bool(re.search(r"rebuttal|response|supp|appendix|cover", f.stem, re.I))
        if s > score:
            best, score = f, s
    if best is None:
        raise SystemExit(f"no main .tex with \\documentclass under {src}")
    return best


def flatten(path, root, depth=0):
    text = strip_comments(path.read_text(errors="ignore"))
    if depth > 8:
        return text

    def repl(m):
        name = m.group(2).strip()
        for cand in (root / name, root / f"{name}.tex", path.parent / name, path.parent / f"{name}.tex"):
            if cand.is_file():
                return flatten(cand, root, depth + 1)
        return m.group(0)

    return re.sub(r"\\(input|include|subfile)\s*\{([^}]+)\}", repl, text)


def simple_macros(text):
    """Zero-argument \\newcommand / \\def macros, for expanding inside equations and captions."""
    macros = {}
    for m in re.finditer(r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\s*(\[\d\])?", text):
        if m.group(2):
            continue
        body, _ = braced(text, m.end())
        macros[m.group(1)] = body
    for m in re.finditer(r"\\def\\([A-Za-z]+)\s*\{", text):
        body, _ = braced(text, m.end() - 1)
        macros.setdefault(m.group(1), body)
    return macros


def expand(text, macros, rounds=3):
    for _ in range(rounds):
        new = re.sub(r"\\([A-Za-z]+)(?![A-Za-z])", lambda m: macros.get(m.group(1), m.group(0)), text)
        if new == text:
            break
        text = new
    return text


def clean_inline(text, macros):
    """Caption / title text to readable plain text (math kept)."""
    t = expand(text, macros)
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = re.sub(r"\\(cite[tp]?|ref|eqref|autoref|cref|Cref)\{([^}]*)\}", r"[\2]", t)
    for _ in range(3):
        t = re.sub(r"\\(textbf|textit|emph|textrm|textsc|texttt|underline|mbox|text)\{([^{}]*)\}", r"\2", t)
    t = re.sub(r"\\(vspace|hspace)\*?\{[^}]*\}", "", t)
    t = re.sub(r"\\(small|footnotesize|scriptsize|centering|noindent|bf|it|xspace)\b", "", t)
    t = t.replace("~", " ").replace("\\\\", " ").replace("\\,", " ").replace("\\&", "&").replace("\\%", "%")
    return " ".join(t.split())


def environments(text, names):
    pat = re.compile(r"\\begin\{(" + "|".join(names) + r")(\*?)\}(.*?)\\end\{\1\2\}", re.S)
    for m in pat.finditer(text):
        yield m.group(1) + m.group(2), m.group(3), m.start()


def graphicspaths(text):
    dirs = []
    for arg in command_args(text, "graphicspath"):
        dirs += re.findall(r"\{([^}]*)\}", arg)
    return dirs


def resolve(src, name, gdirs):
    name = name.strip()
    bases = [src] + [src / d for d in gdirs]
    for b in bases:
        p = b / name
        if p.suffix.lower() in IMG_EXTS and p.is_file():
            return p
        for ext in IMG_EXTS:
            q = b / f"{name}{ext}"
            if q.is_file():
                return q
    hits = [p for p in src.rglob(Path(name).name + "*") if p.suffix.lower() in IMG_EXTS]
    return hits[0] if hits else None


# ------------------------------------------------------------------ tables
TAB_ENV = r"(tabular\*?|tabularx|longtable|tabulary)"
_G = r"((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)"  # brace group content, two levels of nesting


def _skip_spec(t, env):
    """Drop the optional [pos] and the column spec (tabular*/tabularx also take a width)."""
    t = re.sub(r"^\s*\[[^\]]*\]", "", t)
    for _ in range(2 if env in ("tabular*", "tabularx", "tabulary") else 1):
        _, end = braced(t, 0)
        t = t[end:]
    return t


def outer_tabular(body):
    m = re.search(r"\\begin\{" + TAB_ENV + r"\}", body)
    if not m:
        return None
    depth = 0
    for k in re.finditer(r"\\(begin|end)\{" + TAB_ENV + r"\}", body[m.start():]):
        depth += 1 if k.group(1) == "begin" else -1
        if depth == 0:
            inner = body[m.end(): m.start() + k.start()]
            return _skip_spec(inner, m.group(1))
    return None


def clean_cell(c):
    c = re.sub(r"~?\\cite[tp]?\{[^}]*\}", "", c)
    c = re.sub(r"\\color(\[[^\]]*\])?\{[^}]*\}", "", c)
    c = re.sub(r"\\textcolor(\[[^\]]*\])?\{[^}]*\}\{([^{}]*)\}", r"\2", c)
    c = re.sub(r"\\(Checkmark|CheckmarkBold|cmark|checkmark)\b", "✓", c)
    c = re.sub(r"\\(XSolidBrush|XSolid|xmark|ding\{55\})", "✗", c)
    c = c.replace("\\(", "").replace("\\)", "")
    c = re.sub(r"(?<!\\)[{}]", "", c)
    for a, b in (("$\\uparrow$", "↑"), ("$\\downarrow$", "↓"), ("\\uparrow", "↑"), ("\\downarrow", "↓"),
                 ("$\\times$", "×"), ("\\times", "×"), ("$\\pm$", "±"), ("\\%", "%"), ("\\&", "&"),
                 ("\\,", " "), ("~", " "), ("\\checkmark", "✓"), ("\\xmark", "✗"), ("\\ding{55}", "✗"),
                 ("\\ding{51}", "✓")):
        c = c.replace(a, b)
    return " ".join(c.split())


def tabular_rows(body, macros):
    """Rows of the outermost tabular. Bold -> **x**, underline -> __x__, \\cellcolor{c} -> x ‹c›."""
    t = outer_tabular(body)
    if t is None:
        return []
    t = expand(t, macros)
    for _ in range(3):  # collapse nested tabulars (multi-line header cells)
        t = re.sub(r"\\begin\{tabular\}(\[[^\]]*\])?\{" + _G + r"\}((?:(?!\\begin\{tabular\}).)*?)\\end\{tabular\}",
                   lambda m: " ".join(re.split(r"\\\\", m.group(3))), t, flags=re.S)
    t = t.replace("\\&", "\x00AMP\x00")
    t = re.sub(r"\\(hline|toprule|midrule|bottomrule|specialrule|hdashline|addlinespace)(\[[^\]]*\]|\{[^}]*\})*", "", t)
    t = re.sub(r"\\(cmidrule|cline)(\([^)]*\))?\{[^}]*\}", "", t)
    t = re.sub(r"\\rowcolor(\[[^\]]*\])?\{[^}]*\}", "", t)
    t = re.sub(r"\\cellcolor(\[[^\]]*\])?\{([^}]*)\}([^&\\]*)", lambda m: f"{m.group(3).strip()} ‹{m.group(2)}›", t)
    for _ in range(3):
        t = re.sub(r"\\multi(column|row)\{[^}]*\}\{[^}]*\}\{" + _G + r"\}", r"\2", t)
        t = re.sub(r"\\(textbf|mathbf|bf|first|best|tbf|bestresult)\{" + _G + r"\}", r"**\2**", t)
        t = re.sub(r"\\(underline|uline|second|secondbest)\{" + _G + r"\}", r"__\2__", t)
        t = re.sub(r"\\(textit|emph|textrm|text|mathrm|textsc|makecell|shortstack)(\[[^\]]*\])?\{" + _G + r"\}",
                   r"\3", t)
    t = re.sub(r"\\(small|footnotesize|scriptsize|centering|bf|it|tiny|bfseries|normalsize)\b", "", t)
    rows = []
    for line in re.split(r"\\\\(?:\s*\[[^\]]*\])?|\\tabularnewline", t):
        cells = [clean_cell(c.replace("\x00AMP\x00", "&")) for c in line.split("&")]
        if any(cells):
            rows.append(cells)
    return rows


# ------------------------------------------------------------------ thumbnails
def thumb(path, size=260):
    from PIL import Image
    try:
        if path.suffix.lower() == ".pdf":
            import fitz
            doc = fitz.open(str(path))
            page = doc[0]
            zoom = size * 1.6 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            doc.close()
        else:
            im = Image.open(path)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGB", im.size, "white")
                bg.paste(im, mask=im.split()[-1])
                im = bg
            im = im.convert("RGB")
        im.thumbnail((size, size))
        return im
    except Exception:
        return None


def contact_sheets(figs, out_dir, cols=5, cell=260):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    except Exception:
        font = ImageFont.load_default()
    items = [(f["id"], Path(f["file"]).name, f["file"]) for fig in figs for f in fig["files_info"]]
    for old in out_dir.glob("figures_sheet_*.png"):
        old.unlink()
    per = cols * 4
    sheets = []
    for s in range(0, len(items), per):
        chunk = items[s:s + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (cell + 12) + 12, rows * (cell + 40) + 12), (226, 230, 236))
        d = ImageDraw.Draw(sheet)
        for k, (fid, name, file) in enumerate(chunk):
            x, y = 12 + (k % cols) * (cell + 12), 12 + (k // cols) * (cell + 40)
            d.rectangle([x, y, x + cell, y + cell + 28], fill="white")
            im = thumb(Path(file), cell - 8)
            if im:
                sheet.paste(im, (x + (cell - im.width) // 2, y + 4 + (cell - 8 - im.height) // 2))
            d.text((x + 4, y + cell + 6), f"{fid}  {name[:30]}", fill=(31, 58, 95), font=font)
        p = out_dir / f"figures_sheet_{s // per + 1}.png"
        sheet.save(p)
        sheets.append(p)
    return sheets


# ------------------------------------------------------------------ index
def index_paper(key, src, out_dir):
    main = find_main(src)
    flat = flatten(main, main.parent)
    (out_dir / "flat.tex").write_text(flat)
    macros = simple_macros(flat)
    gdirs = graphicspaths(flat)
    doc = flat.split("\\begin{document}", 1)[-1]

    title = clean_inline((command_args(flat, "title") or [""])[0], macros)
    abstract = ""
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", doc, re.S)
    if m:
        abstract = clean_inline(m.group(1), macros)
    sections = []
    for m in re.finditer(r"\\(section|subsection|paragraph)\*?\s*\{", doc):
        arg, _ = braced(doc, m.end() - 1)
        sections.append((m.group(1), clean_inline(arg, macros)))

    figs, used = [], set()
    for env, body, pos in environments(doc, ["figure", "teaserfigure", "wrapfigure"]):
        figs.append((pos, env, body))
    # teasers are often an \includegraphics inside \twocolumn[...] or a custom block outside figure envs
    covered = [(p, p + len(b) + 40) for p, _, b in figs]
    for m in re.finditer(r"\\includegraphics", doc):
        if not any(a <= m.start() <= b for a, b in covered):
            seg = doc[max(0, m.start() - 200): m.start() + 1200]
            figs.append((m.start(), "loose", seg))
    figs.sort()

    fig_list, fid = [], 0
    for n, (pos, env, body) in enumerate(figs, 1):
        caps = command_args(body, "caption")
        for m in re.finditer(r"\\captionof\{figure\}\s*(\[[^\]]*\])?\s*\{", body):
            caps.append(braced(body, m.end() - 1)[0])
        labels = re.findall(r"\\label\{([^}]+)\}", body)
        files = []
        for g in command_args(body, "includegraphics"):
            p = resolve(src, g, gdirs)
            if p is None or p in used:
                continue
            used.add(p)
            fid += 1
            files.append({"id": f"F{fid}", "file": str(p), "rel": str(p.relative_to(src.resolve()))
                          if str(p).startswith(str(src.resolve())) else str(p)})
        if not files and env == "loose":
            continue
        fig_list.append({"n": n, "env": env, "labels": labels, "caption": clean_inline(caps[-1], macros) if caps else "",
                         "subcaptions": [clean_inline(c, macros) for c in caps[:-1]], "files_info": files})

    tables = []
    for env, body, _ in environments(doc, ["table"]):
        caps = command_args(body, "caption")
        tables.append({"labels": re.findall(r"\\label\{([^}]+)\}", body),
                       "caption": clean_inline(caps[0], macros) if caps else "", "rows": tabular_rows(body, macros)})

    eqs = []
    for env, body, _ in environments(doc, ["equation", "align", "eqnarray", "gather", "multline"]):
        labels = re.findall(r"\\label\{([^}]+)\}", body)
        tex = expand(re.sub(r"\\label\{[^}]*\}|\\nonumber|\\notag", "", body), macros)
        eqs.append({"env": env, "labels": labels, "tex": " ".join(tex.split())})
    for m in re.finditer(r"\\\[(.*?)\\\]", doc, re.S):
        eqs.append({"env": "display", "labels": [], "tex": " ".join(expand(m.group(1), macros).split())})

    # ---------------------------------------------------------- write
    src_root = src.resolve()
    L = [f"# {key}: {title}", "", f"- main tex: `{main.relative_to(src_root) if str(main).startswith(str(src_root)) else main}`",
         f"- flattened source: `flat.tex` ({len(flat) // 1000} k chars) — read this for method details and numbers",
         f"- figure thumbnails: `figures_sheet_*.png`", "", "## Abstract", "", abstract or "(none found)", "",
         "## Sections", ""]
    for lvl, t in sections:
        L.append(("- " if lvl == "section" else "  - " if lvl == "subsection" else "    - ") + t)
    L += ["", "## Figures", "",
          "Use with `A.fig(name, PAPERS / '<key>/src/<rel>')`. Multi-panel figures can be cropped with clip=(x0, y0, x1, y1) in PDF points.", ""]
    for f in fig_list:
        lab = f" `{', '.join(f['labels'])}`" if f["labels"] else ""
        L.append(f"### Figure {f['n']} ({f['env']}){lab}")
        for fi in f["files_info"]:
            L.append(f"- **{fi['id']}** `{fi['rel']}`")
        if f["subcaptions"]:
            L.append("- sub: " + " | ".join(f["subcaptions"]))
        L += [f"- caption: {f['caption']}", ""]
    L += ["## Tables", ""]
    for k, t in enumerate(tables, 1):
        lab = f" `{', '.join(t['labels'])}`" if t["labels"] else ""
        L += [f"### T{k}{lab}", f"caption: {t['caption']}", ""]
        if t["rows"]:
            w = max(len(r) for r in t["rows"])
            for i, r in enumerate(t["rows"]):
                L.append("| " + " | ".join(r + [""] * (w - len(r))) + " |")
                if i == 0:
                    L.append("|" + "---|" * w)
        L.append("")
    L += ["## Equations", "", "Macros already expanded. Port to mathtext with `pptkit.assets.sanitize_tex` in mind.", ""]
    for k, e in enumerate(eqs, 1):
        lab = f" `{', '.join(e['labels'])}`" if e["labels"] else ""
        L += [f"- **E{k}** ({e['env']}){lab}: `{e['tex']}`"]
    (out_dir / "index.md").write_text("\n".join(L) + "\n")
    (out_dir / "figures.json").write_text(json.dumps(fig_list, ensure_ascii=False, indent=1))
    sheets = contact_sheets(fig_list, out_dir)
    nfiles = sum(len(f["files_info"]) for f in fig_list)
    print(f"  {key}: '{title[:60]}'  figures {len(fig_list)} ({nfiles} files)  tables {len(tables)}  "
          f"equations {len(eqs)}  sheets {len(sheets)}")
    return out_dir / "index.md"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("papers_dir", type=Path, help="usually <talk_dir>/papers")
    ap.add_argument("specs", nargs="+", help="key=source (archive, directory, .tex, or arXiv id)")
    args = ap.parse_args()
    args.papers_dir.mkdir(parents=True, exist_ok=True)
    for spec in args.specs:
        if "=" not in spec:
            raise SystemExit(f"expected key=source, got '{spec}'")
        key, source = spec.split("=", 1)
        out = args.papers_dir / key
        out.mkdir(exist_ok=True)
        src = unpack(source, out / "src")
        index_paper(key, src.resolve(), out)
    print(f"done -> {args.papers_dir}/<key>/index.md")


if __name__ == "__main__":
    main()
