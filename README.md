# cv

A version-controlled CV/resume system built around a single source of truth — one JSON file containing all career data — rendered into multiple professional PDF outputs via swappable templates, with zero data duplication across variants.

**Key properties:**
- Edit content once, generate many outputs (long academic CV, short industry resume, targeted applications)
- Swap visual themes with a one-line config change — no data re-entry
- Visual/designer PDFs for UX and design roles via a self-hosted web builder
- Fully reproducible: one `docker` prerequisite on the host, everything else runs inside a devcontainer
- CI auto-builds every PDF on push; GitHub Pages hosts the web CV

---

## Table of Contents

- [cv](#cv)
  - [Table of Contents](#table-of-contents)
  - [Architecture Overview](#architecture-overview)
  - [Repository Structure](#repository-structure)
  - [Toolchain](#toolchain)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [First-time setup](#first-time-setup)
    - [GitHub Codespaces](#github-codespaces)
  - [Filling In Your Data](#filling-in-your-data)
  - [Building CVs Locally](#building-cvs-locally)
  - [Variant System](#variant-system)
    - [Section keys](#section-keys)
    - [Renaming section headings](#renaming-section-headings)
    - [Switching themes](#switching-themes)
  - [Creating a Targeted Application](#creating-a-targeted-application)
  - [Visual CVs (Reactive Resume)](#visual-cvs-reactive-resume)
  - [CI/CD and GitHub Pages](#cicd-and-github-pages)
    - [Enabling GitHub Pages](#enabling-github-pages)
  - [Dependency Management](#dependency-management)
  - [Portability](#portability)
  - [Reference: Section Keys](#reference-section-keys)
  - [Reference: RenderCV Themes](#reference-rendercv-themes)

---

## Architecture Overview

```
content/resume.json          ← single source of truth (JSON Resume standard)
        │
        ├── scripts/build.py ──────────────────────────────────────────────────
        │   reads resume.json + variants/<name>.yaml                          │
        │   converts to RenderCV YAML                                          │
        │   calls rendercv render → PDF + HTML + MD                           │
        │   calls pandoc         → DOCX                                       │
        │                                                             output/  │
        │   ┌──────────────────────────────────────────────────────────────── ┘
        │   │  <variant>.pdf   — high-quality Typst-rendered PDF
        │   │  <variant>.html  — web version (deployed to GitHub Pages)
        │   │  <variant>.md    — Markdown intermediate
        │   └  <variant>.docx  — DOCX for ATS upload portals
        │
        └── Reactive Resume (localhost:3000, Docker)
            import resume.json → pick visual template → export PDF
            (used for UX / design roles that need a graphically rich layout)

On git push → GitHub Actions runs the build pipeline
                    │
            ┌───────┴───────────┐
            ▼                   ▼
      CI artifacts          GitHub Pages
      (PDF archive,         (HTML web CV,
       90-day retention)     public URL)
```

The architecture has two rendering paths:

| Path | Tool | Best for | Theme quality | ATS-safe |
|---|---|---|---|---|
| **Typst pipeline** | RenderCV | Technical / academic roles | Polished typographic | ✅ Excellent |
| **Visual builder** | Reactive Resume | UX / design / creative roles | Graphically rich | ⚠️ Layout-dependent |

---

## Repository Structure

```
cv/
├── .devcontainer/
│   ├── Dockerfile              Python 3.12 + pandoc + Node.js
│   ├── docker-compose.yml      Four services: app, reactive_resume, postgres, browserless
│   └── devcontainer.json       VS Code config: port forwards, extensions, postCreateCommand
│
├── .github/
│   └── workflows/
│       └── build.yml           CI: build all variants → upload PDFs → deploy to Pages
│
├── content/
│   └── resume.json             ★ EDIT THIS — all career data, JSON Resume schema
│
├── variants/
│   ├── academic-cv.yaml        Long academic CV: education-first, includes publications
│   ├── industry-resume.yaml    Short tech resume: experience-first, 1–2 pages
│   └── targeted-example.yaml  Template for per-application variants
│
├── scripts/
│   └── build.py                Converts resume.json + variant.yaml → rendercv → output
│
├── output/                     ← git-ignored; rebuilt by make / CI
│
├── Makefile                    make academic | industry | targeted | all | clean
├── requirements.txt            rendercv[full]>=2.8, ruamel.yaml>=0.18
├── .python-version             3.12 (pyenv)
└── .gitignore
```

---

## Toolchain

| Tool | Role | How installed |
|---|---|---|
| **Python 3.12** | Runtime for `build.py` | Devcontainer base image |
| **RenderCV** | CV engine: YAML → Typst → PDF + HTML + MD | `pip install -r requirements.txt` (in devcontainer via `postCreateCommand`) |
| **Typst** | PDF typesetting engine | Bundled inside `rendercv[full]` — no separate install |
| **pandoc** | Markdown → DOCX conversion | `apt-get install pandoc` in Dockerfile |
| **Node.js** | Optional: JSON Resume CLI tooling (`npx resume-cli`) | nvm in Dockerfile |
| **Reactive Resume v5.0.18** | Visual CV builder web UI | Docker image (`amruthpillai/reactive-resume:v5.0.18`) |
| **browserless/chromium** | Headless Chromium for Reactive Resume's PDF export | Docker image (sibling service) |
| **PostgreSQL 16** | Reactive Resume's database | Docker image (sibling service) |

**The only thing you install on your host machine is Docker** (Docker Desktop, OrbStack, or Rancher Desktop). Everything else runs inside the devcontainer.

> **Why no TeX Live?** RenderCV bundles its own Typst binary. Typst is a modern typesetting system that replaces LaTeX for CV use — same output quality, ~1 second build time, no 4 GB TeX Live install.

---

## Getting Started

### Prerequisites

- **Docker Desktop**, [OrbStack](https://orbstack.dev) (macOS, recommended), or [Rancher Desktop](https://rancherdesktop.io) (free, cross-platform)
- **VS Code** with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### First-time setup

1. Clone the repository and open it in VS Code:
   ```bash
   git clone https://github.com/quantized8/cv.git
   cd cv
   code .
   ```

2. VS Code will prompt: **"Reopen in Container"** — click it.

   On first launch Docker builds the dev image and pulls the Reactive Resume stack (~400 MB total). This takes 3–5 minutes once; subsequent starts are instant.

3. After the container starts, `postCreateCommand` runs `pip install -r requirements.txt` automatically.

4. VS Code auto-forwards port 3000. The Reactive Resume web UI opens in your browser.

5. Verify everything works:
   ```bash
   make industry
   ```
   You should see `output/industry-resume.pdf` created in ~2 seconds.

### GitHub Codespaces

This repository works in GitHub Codespaces with no changes. Open it from the GitHub UI → **Code → Codespaces → Create codespace on main**. The free tier (60 core-hours/month on a 2-core machine) is sufficient for occasional CV editing.

---

## Filling In Your Data

All your career data lives in one file: **`content/resume.json`**.

It follows the [JSON Resume](https://jsonresume.org/schema) open standard. VS Code validates it live via the `$schema` reference at the top of the file.

The top-level fields are:

| Field | Content |
|---|---|
| `basics` | Name, title, contact info, location, website, social profiles |
| `work` | Employment history — each entry has company, position, dates, highlights |
| `education` | Degrees — institution, field, dates, GPA, advisors, courses |
| `publications` | Papers, journals, conference proceedings — title, authors, venue, DOI, date |
| `skills` | Skill groups — e.g. "Machine Learning": [PyTorch, JAX, ...] |
| `projects` | Side projects, open source — name, description, highlights, URL, dates |
| `awards` | Awards, fellowships, grants — title, date, awarder, description |
| `certificates` | Certifications — name, date, issuer, credential URL |
| `volunteer` | Teaching, service, reviewing — maps to "Teaching & Service" in the academic CV |
| `languages` | Spoken languages and fluency levels |
| `interests` | Research interests or other interests |
| `references` | Referee names and contact availability |

**Guidelines:**
- Write every entry at its maximum detail level. Variants select which sections to show and in what order — you never need to maintain a "short version" of an entry.
- `highlights` arrays accept Markdown. Links (`[text](url)`) and bold (`**text**`) render in both PDF and HTML.
- Dates use `YYYY-MM` or `YYYY-MM-DD`. Omit or leave blank `endDate` for current positions.

---

## Building CVs Locally

All builds run inside the devcontainer terminal.

```bash
# Build the academic long CV
make academic
# → output/academic-cv.pdf
# → output/academic-cv.html
# → output/academic-cv.md
# → output/academic-cv.docx

# Build the industry short resume
make industry

# Build the targeted-example variant
make targeted

# Build all standard variants
make all

# Remove all generated files
make clean
```

You can also invoke the build script directly, which is useful for custom or targeted variants:

```bash
python scripts/build.py <variant-name>
```

`<variant-name>` must match a file in `variants/` without the `.yaml` extension.

---

## Variant System

A **variant** is a YAML file in `variants/` that defines two things:

1. **Which sections to include**, in what order
2. **Visual design** (theme, colours, font size, page size)

```yaml
# variants/industry-resume.yaml

sections:
  - summary
  - experience
  - education
  - skills
  - projects
  - awards
  - certificates

design:
  theme: engineeringresumes
  color: "#00A693"
  font_size: "10pt"
  page_size: us-letter
  text_alignment: justified
```

The `scripts/build.py` script reads this alongside `content/resume.json` and constructs the full RenderCV input. **The content file is never modified** — only the section list and design config change between variants.

### Section keys

| Key in variant | Source in `resume.json` | Default heading |
|---|---|---|
| `summary` | `basics.summary` | Summary |
| `experience` | `work[]` | Experience |
| `education` | `education[]` | Education |
| `publications` | `publications[]` | Publications |
| `skills` | `skills[]` | Skills |
| `projects` | `projects[]` | Projects |
| `awards` | `awards[]` | Awards |
| `certificates` | `certificates[]` | Certificates |
| `volunteering` | `volunteer[]` | Volunteering |
| `languages` | `languages[]` | Languages |
| `interests` | `interests[]` | Interests |
| `references` | `references[]` | References |

### Renaming section headings

Use `section_titles` to display a section under a different heading without touching the content:

```yaml
section_titles:
  volunteering: Teaching & Service
  interests: Research Interests
```

### Switching themes

Change the `design.theme` value. All nine built-in RenderCV themes accept the same data — no remapping needed:

```yaml
design:
  theme: moderncv       # or: classic, sb2nov, engineeringresumes,
                        #     engineeringclassic, harvard, opal, ink, ember
```

---

## Creating a Targeted Application

For a specific job application, create a new variant file:

```bash
cp variants/targeted-example.yaml variants/targeted-acme-corp.yaml
```

Edit `variants/targeted-acme-corp.yaml` to adjust section order, theme, or colours for the role.

If you need to tailor **individual bullet points** (not just section visibility), use a git branch to keep a clean record:

```bash
git checkout -b targeted/acme-corp
# edit content/resume.json — reorder highlights, add role-specific bullets
python scripts/build.py targeted-acme-corp
# → output/targeted-acme-corp.pdf
git stash   # or commit the branch for archival; discard when done
```

This keeps `main` clean while giving you a full history of every tailored application.

---

## Visual CVs (Reactive Resume)

For roles where visual design matters (UX, product design, creative agencies), use Reactive Resume instead of the Typst pipeline.

Reactive Resume runs as a Docker service inside the devcontainer. It is accessible at **`http://localhost:3000`** in your host browser while the devcontainer is running.

**Workflow:**

1. Open `http://localhost:3000` and create an account (local only — data stays in the devcontainer's PostgreSQL volume).
2. Create a new resume → **Import** → select `content/resume.json`.
3. Pick a template from the template gallery (Azurill, Bronzor, Chikorita, Gengar, Glalie, Kakuna, Lapras, Leafish, Onyx, Pikachu, Rhyhorn, Ditto).
4. Customise colours, fonts, spacing, and section order via the editor.
5. **Export → PDF** to download the rendered file.

When your data changes, re-import `content/resume.json` to sync. Your template selection and customisations are preserved between imports.

> **ATS note:** Visually complex layouts (heavy colour blocks, multi-column sections, icon-heavy sidebars) score poorly with automated applicant tracking systems. Use the Typst pipeline variants for applications submitted through ATS-screened portals, and the visual PDF only when a human reviews it first.

---

## CI/CD and GitHub Pages

The GitHub Actions workflow (`.github/workflows/build.yml`) runs on every push to `main` and on every pull request.

**What it does:**

1. Installs Python 3.12 and pandoc on a clean Ubuntu runner (does not use the devcontainer — this is faster and cheaper)
2. Runs `pip install -r requirements.txt` and `make all`
3. Generates `output/index.html` — a simple page linking to all HTML variants
4. Uploads all PDFs as a **build artifact** named `cv-pdfs-<sha>` (retained for 90 days)
5. On pushes to `main` only: deploys the entire `output/` directory to **GitHub Pages**

### Enabling GitHub Pages

1. Go to your repository → **Settings → Pages**
2. Under **Source**, select **GitHub Actions**
3. Push any change to `main` to trigger the first deployment
4. Your web CV will be live at `https://<username>.github.io/cv/`

The index page links to each variant's HTML version. PDFs are available as CI artifacts on the Actions tab, attached to the commit that produced them.

---

## Dependency Management

| Dependency | Lock mechanism |
|---|---|
| Python packages | `requirements.txt` with minimum version pins; `pip install` inside devcontainer |
| Python version | `.python-version` (read by pyenv; also declared in `actions/setup-python`) |
| Reactive Resume | Image pinned to `v5.0.18` in `docker-compose.yml` |
| PostgreSQL | Image pinned to `postgres:16` in `docker-compose.yml` |
| GitHub Actions | Action versions pinned (`actions/checkout@v4`, etc.) |
| pandoc | Installed from Ubuntu apt; version not pinned (minor version drift is harmless for DOCX output) |

To upgrade RenderCV:

```bash
# Update requirements.txt, then inside the devcontainer:
pip install -r requirements.txt
# Test:
make all
```

To upgrade Reactive Resume, update the image tag in `.devcontainer/docker-compose.yml` and rebuild the container.

---

## Portability

| Environment | Status | Notes |
|---|---|---|
| macOS (Apple Silicon / Intel) | ✅ | Native; OrbStack recommended over Docker Desktop |
| Linux | ✅ | Same setup; `apt` instead of `brew` for Docker |
| Windows (WSL2) | ✅ | Equivalent to Linux inside WSL2 |
| Windows (native) | ⚠️ | Python and pandoc work; Docker requires WSL2 backend |
| GitHub Codespaces | ✅ | Free tier sufficient; zero local setup |
| Fully offline | ⚠️ | RenderCV builds offline; Reactive Resume needs images pre-pulled |
| Collaborator with no Python | ✅ | Devcontainer handles everything; or trigger CI to build PDFs |

---

## Reference: Section Keys

Complete mapping between variant section keys and `resume.json` fields:

| Variant key | JSON Resume field | RenderCV entry type |
|---|---|---|
| `summary` | `basics.summary` (string) | Plain text paragraph |
| `experience` | `work[]` | Experience entry (company, position, dates, highlights) |
| `education` | `education[]` | Education entry (institution, degree, area, dates) |
| `publications` | `publications[]` | Publication entry (title, authors, journal/conf, DOI, date) |
| `skills` | `skills[]` | One-line entry per skill group (label + keywords) |
| `projects` | `projects[]` | Normal entry (name, dates, highlights) |
| `awards` | `awards[]` | Normal entry (name, date, awarder as location, description) |
| `certificates` | `certificates[]` | Normal entry (name, date, issuer, credential link) |
| `volunteering` | `volunteer[]` | Experience entry (maps organisation→company, position, dates, highlights) |
| `languages` | `languages[]` | Single one-line entry listing all languages and fluency levels |
| `interests` | `interests[]` | One-line entry per interest group (label + keywords) |
| `references` | `references[]` | Normal entry (name + reference text as highlight) |

---

## Reference: RenderCV Themes

Set `design.theme` in any variant file to one of:

| Theme | Character | Best for |
|---|---|---|
| `classic` | Clean, traditional two-column header | General purpose |
| `sb2nov` | Compact, minimal | Industry / tech |
| `moderncv` | Coloured rule accents, generous spacing | Academic |
| `engineeringresumes` | Dense, information-rich | Engineering / tech |
| `engineeringclassic` | Classic engineering style | Engineering |
| `harvard` | Tight margins, Harvard-style | Academic (faculty applications) |
| `opal` | Modern, clean lines | Industry |
| `ink` | Bold section headers | Creative-adjacent industry |
| `ember` | Warm accent tones | Industry |

All themes accept the same `design` sub-keys: `color`, `font_size`, `page_size` (`a4` or `us-letter`), `text_alignment` (`justified` or `left`).