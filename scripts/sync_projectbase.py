#!/usr/bin/env python3
"""Copy the RDN project register (rdn-projectbase) into this website.

Runs automatically before every `quarto render` (see `pre-render` in _quarto.yml).
It writes the generated pages to projectbase/, which is not committed to git.

The project data, the validation and the page generator all stay in the
rdn-projectbase repository, which keeps handling form submissions and pull
requests and keeps publishing its own site. This script only reuses them.

Where the register comes from, in order:
  1. the folder named by the environment variable RDN_PROJECTBASE_DIR
  2. a sibling folder ../rdn-projectbase (handy when editing locally)
  3. a fresh shallow clone of the public GitHub repo into .projectbase-src/
     (what happens on GitHub Actions)
Set RDN_PROJECTBASE_CLONE=1 to skip 1 and 2 and always use the GitHub copy.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_URL = "https://github.com/ResponseDiversityNetwork/rdn-projectbase.git"
WEBSITE = Path(__file__).resolve().parent.parent
OUT = WEBSITE / "projectbase"
CLONE_DIR = WEBSITE / ".projectbase-src"

# Hand-written pages copied from rdn-projectbase/site/. Their links to each other
# (tags.qmd, submit.qmd, about.qmd#what-we-ask) keep working because the folder
# layout is the same: pages at the top, one page per project in projects/.
PAGES = ["index.qmd", "submit.qmd", "about.qmd"]

NAV = [
    ("Browse projects", "index.qmd"),
    ("Tags", "tags.qmd"),
    ("Share a project", "submit.qmd"),
    ("About & guidelines", "about.qmd"),
]


def find_source() -> Path:
    if os.environ.get("RDN_PROJECTBASE_CLONE") != "1":
        env = os.environ.get("RDN_PROJECTBASE_DIR")
        if env:
            return Path(env).expanduser().resolve()
        sibling = WEBSITE.parent / "rdn-projectbase"
        if (sibling / "scripts" / "build_site.py").exists():
            return sibling
    if CLONE_DIR.exists():
        shutil.rmtree(CLONE_DIR)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", REPO_URL, str(CLONE_DIR)], check=True
    )
    return CLONE_DIR


def load_builder(src: Path):
    spec = importlib.util.spec_from_file_location("build_site", src / "scripts" / "build_site.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def split_front_matter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n.*?\n---\n", text, flags=re.S)
    return (text[: m.end()], text[m.end():]) if m else ("", text)


def nav_block(prefix: str = "") -> str:
    links = " · ".join(f"[{label}]({prefix}{href})" for label, href in NAV)
    return f"::: {{.projectbase-nav}}\n{links}\n:::\n"


def add_nav(text: str, prefix: str = "") -> str:
    fm, body = split_front_matter(text)
    return f"{fm}\n{nav_block(prefix)}\n{body.lstrip()}"


def fill_vars(text: str, variables: dict) -> str:
    """Replace {{< var name >}} with values from rdn-projectbase/site/_variables.yml."""
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in variables:
            raise KeyError(f"unknown variable '{key}' in a projectbase page")
        return str(variables[key])
    return re.sub(r"\{\{<\s*var\s+([\w-]+)\s*>\}\}", sub, text)


def main() -> int:
    src = find_source()
    builder = load_builder(src)

    projects = builder.load_projects()
    errors = builder.validate(projects)
    if errors:
        print("rdn-projectbase validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    variables = yaml.safe_load((src / "site" / "_variables.yml").read_text(encoding="utf-8")) or {}
    contact_email = variables.get("curator_email", "")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "projects").mkdir(parents=True)
    (OUT / "data").mkdir()

    for name in PAGES:
        text = (src / "site" / name).read_text(encoding="utf-8")
        (OUT / name).write_text(add_nav(fill_vars(text, variables)), encoding="utf-8")

    public = [p for _, p in projects]
    for p in public:
        page = builder.render_page(p, contact_email)
        (OUT / "projects" / f"{p['id']}.qmd").write_text(add_nav(page, "../"), encoding="utf-8")

    tags_md, tag_rows = builder.render_tags_page(public)
    (OUT / "tags.qmd").write_text(add_nav(tags_md), encoding="utf-8")
    (OUT / "data" / "tags.json").write_text(
        json.dumps(tag_rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "data" / "projects.json").write_text(
        json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Styles used only on these pages (copied from rdn-projectbase, plus the nav strip).
    css = (src / "site" / "styles.css").read_text(encoding="utf-8")
    css += "\n.projectbase-nav { margin-bottom: 1.5rem; font-size: 0.95rem; }\n"
    (OUT / "projectbase.css").write_text(css, encoding="utf-8")
    (OUT / "_metadata.yml").write_text(
        "# Generated by scripts/sync_projectbase.py. Do not edit.\n"
        "format:\n  html:\n    css: projectbase.css\n",
        encoding="utf-8",
    )

    print(f"projectbase: {len(public)} project(s) copied from {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
