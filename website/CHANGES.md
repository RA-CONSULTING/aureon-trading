# Aureon Zorza / Project Envision — metadata & identity correction pass

**Date:** 2026-07-13 · **Applied by:** R&A Consulting and Brokerage Services Ltd
**Base:** the home.pl upload package built by Łukasz (`luciferprosun/RA-Consulting`, commit
`f21fbdb`).

This pass **adds correct system metadata and company identity** and **refreshes the flagship
project facts** — mirroring the correctness pass done on the Aureon OS repository. It is
**additive**: the site's design, imagery, portfolio structure, authorship credit, GitHub links,
and every "TO VERIFY / Draft / not investment advice" evidence label are preserved unchanged.

## What changed

### 1. Brand & credential assets (new)
- `assets/images/brand/aureon-zorza-logo.jpg` — used as the site OG/Twitter share image and the
  `Organization` logo.
- `assets/images/brand/ra-consulting-logo.jpg`
- `assets/images/brand/innovate-ni-silver-2025.png` — shown on the About page.

### 2. Machine-readable metadata (added to the 19 indexable pages)
- `<link rel="canonical">` on `https://aureonzorzatechnologies.pl/…`.
- `<meta name="author">` = "R&A Consulting and Brokerage Services Ltd (Aureon Zorza Technologies)".
- **Open Graph** (`og:type/site_name/locale/title/description/url/image`) and **Twitter Card**
  (`summary_large_image`) tags.
- `noindex` archive/redirect pages were intentionally **not** given canonical tags (to avoid a
  noindex+canonical contradiction).

### 3. Structured data (JSON-LD)
- `index.html` + `about/index.html` carry an `Organization` block — `legalName` *R&A Consulting
  and Brokerage Services Ltd*, `identifier` *UK Companies House NI696693*, `founder` *Gary Leckey
  (Director & Owner)*, `employee` *Łukasz (Chief Researcher & site creator)*, the Innovate NI
  Silver `award`, and `sameAs` GitHub links. `index.html` also carries a `WebSite` block.

### 4. Identity content
- **About** (`about/index.html`) gained three sections: **Company** (legal entity, NI696693,
  Belfast NI UK, trading-name note, Aureon Institute research identity), **Team** (*Gary Leckey —
  Director & Owner*; *Łukasz — Chief Researcher & site creator*, with his GitHub + email kept),
  and **Recognition** (the Silver-level Innovate NI certificate, 21 July 2025, with image).
- **Footer** — a legal line added site-wide (19 public pages): *"© 2025 R&A Consulting and
  Brokerage Services Ltd — trading as Aureon Zorza Technologies · Company no. NI696693 (Northern
  Ireland, UK). Aureon Institute is the research identity for the HNC framework."* A small
  `.footer-legal` rule was added to `styles.css`.
- **Contact** — the two public contacts were relabelled to the agreed roles (*Gary Leckey —
  Director & Owner, R&A Consulting*; *Łukasz — Chief Researcher & site creator*). Emails and
  GitHub links unchanged.

### 5. Flagship fact refresh (hedges preserved)
- `data/projects.json` **P-04** and `data/publications.json` "Project Brief 001": the *AUREON
  Trading System* entry now reads **Aureon OS — Harmonic Nexus Core**, with the repository link
  updated to `github.com/RA-CONSULTING/Aureon-OS`. **Status stays "Draft / private review",
  `is_public` stays false, and the "Not investment advice / no performance claims" cautions are
  unchanged.** The `projects/aureon-trading-system/` slug/URL is unchanged.
- `data/projects.json` **P-09 (HNC Framework)**: a light factual note that the framework is
  published under the **Aureon Institute** research identity. Its "TO VERIFY" status and cautions
  are unchanged.

### 6. Sitemap & robots
- `sitemap.xml` now lists all 19 indexable pages with absolute
  `https://aureonzorzatechnologies.pl/…` URLs (was an empty skeleton).
- `robots.txt` gained a `Sitemap:` line.

### 7. Research tab (new)
- New **Research** section (`research/index.html`, formerly a redirect stub) in the site's ledger
  format, plus a **Research** link added to the primary nav on every page.
- Driven by a new `data/research.json` (rendered by `script.js`), grouped by researcher:
  - **Gary Leckey** (Aureon Institute / HNC) — 14 public papers, with profile links to ORCID
    (`0009-0004-2792-4649`), Zenodo, ResearchGate, Academia (`gleckey.academia.edu`), GitHub, and
    the Aureon Institute site, plus the whitepaper library on GitHub. Papers verified via the
    ORCID public API and Zenodo DOIs (HNC, HNC+Auris Conjecture, HNC+Aureon Trading Framework,
    Tandem in Unity, QGITA ×2, EPAS, LuminaCell v2, Math Angel Protocol, Harmonic Reality
    Framework ×2, Dynamic Systems Model, Modeling Light Dynamics, The Barons' Banner).
  - **Łukasz (LuciferSun)** (Project Envision) — 4 archived Zenodo records (AOIA-Core, MHLM/MDLH,
    LSC ×2) + GitHub. LSC records kept labelled "TO VERIFY".
- Every link points to a real, verified public record; no profile URL or paper was invented.
  `research/` is now indexable and included in the sitemap.

## What was **not** changed
Design, CSS layout, colours, and imagery (except the three added brand assets and one small
`.footer-legal` rule); Łukasz's authorship, credits, GitHub links, and contact; the portfolio
ethos and every project's evidence/status labels; the `noindex` posture of archive/redirect
pages. No claim was converted into a performance or investment promise.

## Domain note
Metadata uses `https://aureonzorzatechnologies.pl`. If the live domain differs, update the
`canonical`, `og:url`, JSON-LD `url`, `sitemap.xml`, and the `robots.txt` `Sitemap:` line
accordingly.
