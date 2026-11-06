#!/usr/bin/env python3
"""Scaffold a talk folder from LaTeX sources.

    python tools/new_talk.py ~/research/my-talk --title "结构化 3D Gaussian Splatting" \\
        sc=~/dl/arXiv-2312.00109v1.tar.gz oc=~/dl/arXiv-2403.17898v2 px=2509.24421v5

Keys are short asset prefixes (sc_, oc_, px_), in talk order. Creates

    <talk>/papers/<key>/...        via ingest_papers.py (index.md, flat.tex, figures_sheet_*.png)
    <talk>/ppt/make_assets.py      FIGS pre-filled (all figures commented out; enable the ones you use)
    <talk>/ppt/build_ppt.py        runnable skeleton deck with placeholders
    <talk>/大纲.md, <talk>/逐字稿.md  from the skill templates
    <talk>/notes/                  per-paper reading notes go here

Existing files are never overwritten.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import ingest_papers  # noqa: E402

COLORS = ["C1", "C2", "C3", "C4", "C5"]


def write_new(path, text):
    if path.exists():
        print(f"  keep existing {path}")
        return
    path.write_text(text)
    print(f"  wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("talk_dir", type=Path)
    ap.add_argument("specs", nargs="+", help="key=source (archive, directory, .tex, or arXiv id)")
    ap.add_argument("--title", required=True, help="talk title (also the .pptx name)")
    args = ap.parse_args()
    if len(args.specs) > len(COLORS):
        raise SystemExit(f"at most {len(COLORS)} papers per deck")

    talk = args.talk_dir.expanduser().resolve()
    for d in ("papers", "ppt/assets", "notes", "check"):
        (talk / d).mkdir(parents=True, exist_ok=True)

    papers, fig_lines = [], []
    for spec, color in zip(args.specs, COLORS):
        key, source = spec.split("=", 1)
        out = talk / "papers" / key
        out.mkdir(exist_ok=True)
        src = ingest_papers.unpack(source, out / "src")
        ingest_papers.index_paper(key, src.resolve(), out)
        title = (out / "index.md").read_text().splitlines()[0].split(": ", 1)[-1]
        short = title.split(":")[0].strip() if ":" in title else key
        papers.append(f'    ("{key}", "{short}", "{title}", {color}),')
        fig_lines.append(f"    # ---- {short}")
        for fig in json.loads((out / "figures.json").read_text()):
            for f in fig["files_info"]:
                stem = Path(f["rel"]).stem.lower().replace("-", "_").replace(" ", "_")
                cap = fig["caption"][:70].replace("\n", " ")
                fig_lines.append(f'    # "{key}_{stem}": "{key}/src/{f["rel"]}",  # {f["id"]} {cap}')

    deck_name = f"{args.title}.pptx"
    subs = {"{{TITLE}}": args.title, "{{DECK}}": deck_name, "{{PPT_BUILD}}": str(REPO),
            "{{PAPERS}}": "\n".join(papers), "{{FIGS}}": "\n".join(fig_lines)}

    def fill(text):
        for a, b in subs.items():
            text = text.replace(a, b)
        return text

    tpl = REPO / "templates" / "project"
    write_new(talk / "ppt" / "make_assets.py", fill((tpl / "make_assets.py").read_text()))
    write_new(talk / "ppt" / "build_ppt.py", fill((tpl / "build_ppt.py").read_text()))
    skill = REPO / "skill" / "paper-ppt"
    write_new(talk / "大纲.md", fill((skill / "outline-template.md").read_text()))
    write_new(talk / "逐字稿.md", fill((skill / "script-template.md").read_text()))
    print(f"\nnext: read {talk}/papers/*/index.md and figures_sheet_*.png, write notes/, then 大纲.md")


if __name__ == "__main__":
    main()
