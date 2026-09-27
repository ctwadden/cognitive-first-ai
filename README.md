# Cognitive-First AI

A practical high-school teacher newsletter by Chad Wadden.

Public site: https://ctwadden.github.io/cognitive-first-ai/
Contact: cwadden@gnspes.ca

## Publish another issue

This is a static site: no API keys, database, student accounts or paid hosting are needed. It is hosted by GitHub Pages from the root of `main` with `.nojekyll`.

1. Research and write the article with clearly linked primary sources and scope limitations.
2. Add the source article to `content/` and the final images to `assets/`.
3. Add the issue metadata and resource handling in `build.py`; run `python3 build.py`.
4. Check the pages and resources on desktop and mobile. Check that only public-ready material is present.
5. Commit and push to `main`. Wait for the Pages deployment and check the live issue and downloads.

`build.py` uses only the Python standard library. Its small Markdown converter supports the formatting used in the first issue; new issue source is HTML. Edit source files then rebuild rather than editing generated pages.

The assignment planner keeps entries only in page memory. Printing includes entered answers. It has no analytics, submission endpoint or persistent storage.

## Editorial scope

Both initial issues were published September 27, 2026. Issue 001 was prepared September 13. AI assisted research, writing and illustration; sources and limitations are stated in each issue. Teaching routines are proposed applications, not tested interventions or school policy. Images of Chad are AI-generated illustrations based on a supplied AI-enhanced reference image, not documentary photographs.

No mailing-list integration is configured. The contact link opens email; it does not subscribe visitors or send a newsletter automatically.
