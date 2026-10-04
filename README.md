# Cognitive-First AI

A practical high-school teacher newsletter by Chad Wadden.

Public site: https://ctwadden.github.io/cognitive-first-ai/
Contact: cwadden@gnspes.ca

## Publish another issue

This is a static site: no API keys, database, student accounts or paid hosting are needed. It is hosted by GitHub Pages from the root of `main` with `.nojekyll`.

1. Start with an approved Issue package from the production system. From this folder, run `python3 add_issue.py /path/to/package`. Use `--number NNN` or `--date "Published October 11, 2026"` only when you need to override the package values.
2. Run `python3 build.py` to rebuild the static pages.
3. Open `index.html`, the new page under `issues/` and any new pages under `resources/`. Check them locally on desktop and mobile, and confirm that only public-ready material is present.
4. When everything is ready, commit the source and generated files and push to `main`. Wait for the Pages deployment, then check the live issue and resources.

Both scripts use only the Python standard library. `add_issue.py` copies the approved article, optional teacher resources and images into the site, then updates `content/issues.json`. It does not build, commit or publish anything. Edit source files and rebuild rather than editing generated pages.

The assignment planner keeps entries only in page memory. Printing includes entered answers. It has no analytics, submission endpoint or persistent storage.

## Editorial scope

Both initial issues were published September 27, 2026. Issue 001 was prepared September 13. AI assisted research, writing and illustration; sources and limitations are stated in each issue. Teaching routines are proposed applications, not tested interventions or school policy. Images of Chad are AI-generated illustrations based on a supplied AI-enhanced reference image, not documentary photographs.

No mailing-list integration is configured. The contact link opens email; it does not subscribe visitors or send a newsletter automatically.
