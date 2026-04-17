#!/usr/bin/env python3
"""
Build a CV variant from JSON Resume data and a variant config file.

Usage:
    python scripts/build.py <variant-name>

Examples:
    python scripts/build.py industry-resume
    python scripts/build.py academic-cv
    python scripts/build.py targeted-acme-corp

Outputs (written to output/):
    <variant-name>.pdf   — rendered via RenderCV + Typst
    <variant-name>.html  — web version
    <variant-name>.md    — Markdown intermediate
    <variant-name>.docx  — generated from Markdown via pandoc (ATS upload use)
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
VARIANTS_DIR = ROOT / "variants"
OUTPUT_DIR = ROOT / "output"

_yaml = YAML()
_yaml.default_flow_style = False
_yaml.width = 10_000  # prevent ruamel from wrapping long strings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_date(date_str: str | None) -> str:
    """Normalise a JSON Resume date string to RenderCV format.

    JSON Resume accepts: YYYY-MM-DD, YYYY-MM, YYYY, "" (= ongoing)
    RenderCV accepts: YYYY-MM-DD, YYYY-MM, YYYY, "present"
    """
    if not date_str or date_str.lower() in ("present", "current", "now"):
        return "present"
    parts = date_str.split("-")
    # Keep up to YYYY-MM (strip day component — rendercv doesn't need it)
    return "-".join(parts[:2]) if len(parts) >= 2 else parts[0]


def _check_deps() -> None:
    if shutil.which("rendercv") is None:
        sys.exit(
            "Error: rendercv not found.\n"
            "Run: pip install -r requirements.txt"
        )
    if shutil.which("pandoc") is None:
        print(
            "Warning: pandoc not found — DOCX output will be skipped.\n"
            "Install with: brew install pandoc  (or apt-get install pandoc)",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Section builders — JSON Resume → RenderCV entry lists
# ---------------------------------------------------------------------------

def _build_experience(work: list) -> list:
    entries = []
    for j in work:
        entry: dict = {
            # JSON Resume uses "name" for the employer; older drafts used "company"
            "company": j.get("name") or j.get("company") or "",
            "position": j.get("position", ""),
            "start_date": _fmt_date(j.get("startDate")),
            "end_date": _fmt_date(j.get("endDate")),
        }
        if j.get("location"):
            entry["location"] = j["location"]
        highlights = list(j.get("highlights", []))
        if j.get("summary"):
            highlights = [j["summary"]] + highlights
        if highlights:
            entry["highlights"] = highlights
        entries.append(entry)
    return entries


def _build_education(education: list) -> list:
    entries = []
    for e in education:
        entry: dict = {
            "institution": e.get("institution", ""),
            "area": e.get("area", ""),
            "degree": e.get("studyType", ""),
            "start_date": _fmt_date(e.get("startDate")),
            "end_date": _fmt_date(e.get("endDate")),
        }
        if e.get("location"):
            entry["location"] = e["location"]
        highlights: list = []
        if e.get("score"):
            highlights.append(f"GPA: {e['score']}")
        if e.get("advisors"):
            highlights.append("Advisor(s): " + ", ".join(e["advisors"]))
        if e.get("courses"):
            highlights.append("Courses: " + ", ".join(e["courses"]))
        if highlights:
            entry["highlights"] = highlights
        entries.append(entry)
    return entries


def _build_publications(pubs: list) -> list:
    entries = []
    for p in pubs:
        entry: dict = {
            "title": p.get("name", ""),
            # authors is required by RenderCV's PublicationEntry schema
            "authors": p.get("authors") or ["—"],
            "date": _fmt_date(p.get("releaseDate")),
        }
        if p.get("doi"):
            entry["doi"] = p["doi"]
        if p.get("publisher"):
            entry["journal"] = p["publisher"]
        if p.get("url") and not p.get("doi"):
            # only include URL if there is no DOI (rendercv auto-links DOIs)
            entry["url"] = p["url"]
        entries.append(entry)
    return entries


def _build_skills(skills: list) -> list:
    entries = []
    for s in skills:
        details = (
            ", ".join(s["keywords"])
            if s.get("keywords")
            else s.get("level", "")
        )
        entries.append({"label": s.get("name", ""), "details": details})
    return entries


def _build_projects(projects: list) -> list:
    entries = []
    for p in projects:
        entry: dict = {"name": p.get("name", "")}
        if p.get("startDate"):
            entry["start_date"] = _fmt_date(p["startDate"])
            entry["end_date"] = _fmt_date(p.get("endDate"))
        highlights = list(p.get("highlights", []))
        if p.get("description"):
            highlights = [p["description"]] + highlights
        if p.get("url"):
            highlights.append(f"[Project link]({p['url']})")
        if highlights:
            entry["highlights"] = highlights
        entries.append(entry)
    return entries


def _build_awards(awards: list) -> list:
    entries = []
    for a in awards:
        entry: dict = {
            "name": a.get("title", ""),
            "date": _fmt_date(a.get("date")),
        }
        if a.get("awarder"):
            entry["location"] = a["awarder"]
        if a.get("summary"):
            entry["highlights"] = [a["summary"]]
        entries.append(entry)
    return entries


def _build_certificates(certs: list) -> list:
    entries = []
    for c in certs:
        entry: dict = {"name": c.get("name", "")}
        if c.get("date"):
            entry["date"] = _fmt_date(c["date"])
        if c.get("issuer"):
            entry["location"] = c["issuer"]
        if c.get("url"):
            entry["highlights"] = [f"[Credential]({c['url']})"]
        entries.append(entry)
    return entries


def _build_volunteering(volunteer: list) -> list:
    """Maps JSON Resume `volunteer[]` to experience-style entries.
    Useful for teaching, service, and community roles."""
    entries = []
    for v in volunteer:
        entry: dict = {
            "company": v.get("organization", ""),
            "position": v.get("position", ""),
            "start_date": _fmt_date(v.get("startDate")),
            "end_date": _fmt_date(v.get("endDate")),
        }
        if v.get("location"):
            entry["location"] = v["location"]
        highlights = list(v.get("highlights", []))
        if v.get("summary"):
            highlights = [v["summary"]] + highlights
        if highlights:
            entry["highlights"] = highlights
        entries.append(entry)
    return entries


def _build_languages(langs: list) -> list:
    if not langs:
        return []
    parts = []
    for lang in langs:
        s = lang.get("language", "")
        if lang.get("fluency"):
            s += f" ({lang['fluency']})"
        parts.append(s)
    return [{"label": "Languages", "details": ", ".join(parts)}]


def _build_interests(interests: list) -> list:
    entries = []
    for i in interests:
        details = ", ".join(i["keywords"]) if i.get("keywords") else ""
        entries.append({"label": i.get("name", ""), "details": details})
    return entries


def _build_references(refs: list) -> list:
    return [
        {"name": r.get("name", ""), "highlights": [r.get("reference", "")]}
        for r in refs
    ]


# Maps variant section key → (json_resume_top_level_key, builder_function)
_BUILDERS: dict[str, tuple[str, object]] = {
    "experience":   ("work",         _build_experience),
    "education":    ("education",    _build_education),
    "publications": ("publications", _build_publications),
    "skills":       ("skills",       _build_skills),
    "projects":     ("projects",     _build_projects),
    "awards":       ("awards",       _build_awards),
    "certificates": ("certificates", _build_certificates),
    "volunteering": ("volunteer",    _build_volunteering),
    "languages":    ("languages",    _build_languages),
    "interests":    ("interests",    _build_interests),
    "references":   ("references",   _build_references),
}


# ---------------------------------------------------------------------------
# Main conversion: JSON Resume → RenderCV YAML structure
# ---------------------------------------------------------------------------

def _build_rendercv_yaml(
    resume: dict,
    sections_to_include: list[str],
    section_titles: dict[str, str],
    design: dict,
) -> dict:
    basics = resume.get("basics", {})

    # Location string: "City, Region" (skip empty parts)
    loc_parts = [
        basics.get("location", {}).get("city", ""),
        basics.get("location", {}).get("region", ""),
    ]
    location_str = ", ".join(p for p in loc_parts if p)

    cv: dict = {"name": basics.get("name", "")}
    if location_str:
        cv["location"] = location_str
    if basics.get("email"):
        cv["email"] = basics["email"]
    if basics.get("phone"):
        cv["phone"] = basics["phone"]
    if basics.get("url"):
        cv["website"] = basics["url"]

    # Social networks (LinkedIn, GitHub, ORCID, etc.)
    networks = [
        {"network": p["network"], "username": p.get("username", "")}
        for p in basics.get("profiles", [])
        if p.get("network")
    ]
    if networks:
        cv["social_networks"] = networks

    # Build sections, applying optional title remapping
    sections: dict = {}
    for key in sections_to_include:
        # Use remapped title as the RenderCV section key if provided;
        # RenderCV uses the section key as the heading in the document.
        rendercv_key = section_titles.get(key, key)

        if key == "summary":
            summary = basics.get("summary", "")
            if summary:
                sections[rendercv_key] = [summary]
        elif key in _BUILDERS:
            json_key, builder = _BUILDERS[key]
            data = resume.get(json_key, [])
            entries = builder(data)
            if entries:
                sections[rendercv_key] = entries
        else:
            print(f"  Warning: unknown section key '{key}' — skipping.", file=sys.stderr)

    if sections:
        cv["sections"] = sections

    return {"cv": cv, "design": design}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <variant-name>", file=sys.stderr)
        sys.exit(1)

    variant_name = sys.argv[1]
    print(f"Building variant: {variant_name}")

    _check_deps()
    OUTPUT_DIR.mkdir(exist_ok=True)

    # --- Load inputs ---
    resume_path = CONTENT_DIR / "resume.json"
    if not resume_path.exists():
        sys.exit(f"Error: {resume_path} not found")
    with open(resume_path) as f:
        resume = json.load(f)

    variant_path = VARIANTS_DIR / f"{variant_name}.yaml"
    if not variant_path.exists():
        sys.exit(f"Error: variant file not found: {variant_path}")
    with open(variant_path) as f:
        variant = _yaml.load(f)

    sections        = list(variant.get("sections", []))
    section_titles  = dict(variant.get("section_titles", {}))
    design          = dict(variant.get("design", {"theme": "engineeringresumes"}))

    # --- Convert to RenderCV YAML ---
    rendercv_data = _build_rendercv_yaml(resume, sections, section_titles, design)

    tmp_yaml = OUTPUT_DIR / f"_tmp_{variant_name}.yaml"
    buf = io.StringIO()
    _yaml.dump(rendercv_data, buf)
    tmp_yaml.write_text(buf.getvalue(), encoding="utf-8")

    # --- Render with RenderCV ---
    pdf_out  = OUTPUT_DIR / f"{variant_name}.pdf"
    html_out = OUTPUT_DIR / f"{variant_name}.html"
    md_out   = OUTPUT_DIR / f"{variant_name}.md"

    result = subprocess.run(
        [
            "rendercv", "render", str(tmp_yaml),
            "--pdf-path",      str(pdf_out),
            "--html-path",     str(html_out),
            "--markdown-path", str(md_out),
        ],
        cwd=ROOT,
    )

    # Clean up temp YAML and any stray rendercv_output/ directory
    tmp_yaml.unlink(missing_ok=True)
    stray_dir = ROOT / "rendercv_output"
    if stray_dir.exists():
        shutil.rmtree(stray_dir)

    if result.returncode != 0:
        sys.exit(f"rendercv failed (exit {result.returncode})")

    print(f"  PDF:  {pdf_out.relative_to(ROOT)}")
    print(f"  HTML: {html_out.relative_to(ROOT)}")

    # --- DOCX via pandoc ---
    if shutil.which("pandoc"):
        docx_out = OUTPUT_DIR / f"{variant_name}.docx"
        pandoc = subprocess.run(
            ["pandoc", str(md_out), "-o", str(docx_out)],
            cwd=ROOT,
        )
        if pandoc.returncode == 0:
            print(f"  DOCX: {docx_out.relative_to(ROOT)}")
        else:
            print("  Warning: pandoc conversion failed — DOCX not generated.", file=sys.stderr)

    print(f"Done: {variant_name}")


if __name__ == "__main__":
    main()
