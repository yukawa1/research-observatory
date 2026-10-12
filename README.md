# Research Observatory

A public, source-linked daily research discovery website, initially focused on active galactic nuclei (AGN).

## First release

- Astro static site with searchable, filterable paper archive and pre-rendered paper pages.
- Seeded with five **real** October 2026 arXiv papers, including curated, source-attributed summaries.
- Daily automated arXiv Atom API ingestion via Python standard library, deterministic topical ranking and arXiv-ID deduplication.
- New records are explicitly **metadata only**: abstracts are author-written and never presented as AI-verified findings.
- Links to primary arXiv records and careful separation of preprint/accepted status, limitations and review provenance.
- No analytics, cookies, API secrets or paid services required for the MVP.

## Run locally

Requires Node.js 22+, Python 3.11+.

```sh
npm install
npm run dev
python -m unittest discover -s tests -v
python scripts/update_arxiv.py --dry-run
```

The Python command performs a live arXiv API request; only use it when network access is available. For an offline demonstration, build the existing seed dataset directly with `npm run build`.

## Deployment

1. In **Settings → Pages**, select **GitHub Actions** as the build/deployment source.
2. Push to `main` or run **Actions → Publish Research Observatory → Run workflow**.
3. The website will be available at **https://yukawa1.github.io/research-observatory/** after the deployment succeeds.
4. The workflow runs at 06:20 UTC daily (not a guaranteed wall-clock start). GitHub Actions may delay scheduled runs. The importer queries recent submissions with a multi-day lookback to recover delayed runs.

GitHub Actions has write permissions to commit any newly discovered metadata, then builds and deploys **in the same run**. This avoids reliance on a second workflow being triggered by a `GITHUB_TOKEN` push.

## Structure

- `config/topics.json`: topical relevance profile (extend with more subjects)
- `scripts/update_arxiv.py`: arXiv metadata importer and stable scoring
- `src/data/papers.json`: committed, inspectable research dataset
- `src/pages`: static homepage, about page and individual paper pages
- `tests`: offline importer tests
- `.github/workflows/site.yml`: ingestion, tests, build and GitHub Pages deploy

## Editorial policy

The website is an independent project, **not affiliated with or endorsed by arXiv**. Links lead to primary-source abstracts and PDFs hosted by arXiv. The original papers remain under their own licenses. All paper records preserve source IDs, links, dates and review level. Automated ingest never manufactures results, conclusions, references or an ELI5 explanation. It never overwrites curated summaries.

The connected **Notion AGN Research Observatory** is a private research notebook. It is *not* automatically published or synced to this repository. Any future Notion integration requires explicit selection of public-safe content and separate credentials; never place credentials in this repository.

## Future

- Human-in-the-loop editorial review workflow, AI evidence extraction with citations, multiple categories, email/RSS subscription.
- Continuous integration and richer filters by research topic and publication status.

References: [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html), [Astro GitHub Pages deployment](https://docs.astro.build/en/guides/deploy/github/).
