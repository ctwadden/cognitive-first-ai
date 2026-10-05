#!/usr/bin/env python3
"""Build the newsletter's static pages with the Python standard library."""
from html import escape
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
BASE = 'https://ctwadden.github.io/cognitive-first-ai/'


def inline(s):
    s = escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def markdown(s):
    out = []
    for block in s.strip().split('\n\n'):
        if block.startswith('#'):
            line, *rest = block.split('\n')
            level = len(line) - len(line.lstrip('#'))
            out.append(f'<h{level}>{inline(line[level:].strip())}</h{level}>')
            if rest:
                out.append('<p>' + inline(' '.join(rest)) + '</p>')
        else:
            out.append('<p>' + inline(block).replace('\n', '<br>') + '</p>')
    return '\n'.join(out)


def shell(title, description, body, prefix='', path='', image=None, js=False):
    fulltitle = f'{title} | Cognitive-First AI'
    share = f'<meta property="og:image" content="{BASE}assets/{image}">' if image else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(fulltitle)}</title><meta name="description" content="{escape(description, quote=True)}"><link rel="canonical" href="{BASE}{path}"><meta property="og:title" content="{escape(fulltitle, quote=True)}"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}{path}">{share}<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"></head><body><a class="skip" href="#main">Skip to content</a><header class="masthead"><div class="wrap"><a class="brand" href="{prefix}index.html">Cognitive-First <span>AI</span></a><nav aria-label="Main"><a href="{prefix}index.html#issues">Issues</a><a href="{prefix}index.html#resources">Teacher resources</a><a href="https://chadwadden.ca/">About Chad</a></nav></div></header><main id="main" class="wrap">{body}</main><footer class="footer"><div class="wrap"><p><strong>Cognitive-First AI</strong><br>Practical ideas for high-school teachers.<br>Written with AI assistance; sources and limitations are listed with each issue.</p><p>Chad Wadden<br><a href="https://chadwadden.ca/">chadwadden.ca</a><br>Illustrations created with AI.</p></div></footer>{f'<script src="{prefix}assets/planner.js"></script>' if js else ''}</body></html>'''


def write(path, text):
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding='utf-8')


def load_issues():
    return json.loads((ROOT / 'content/issues.json').read_text(encoding='utf-8'))


def render_links(links):
    rendered = []
    for link in links:
        href = escape(link['href'], quote=True)
        label = escape(link['label'])
        class_name = link.get('class')
        class_attribute = f' class="{escape(class_name, quote=True)}"' if class_name else ''
        download = ' download' if link.get('download') else ''
        rendered.append(f'<a{class_attribute} href="{href}"{download}>{label}</a>')
    return ''.join(rendered)


def render_resource_box(issue, links):
    if not links:
        return ''
    copy = escape(issue['resourcecopy'])
    return f'<aside class="resource-box"><h2>Your companion resource</h2><p>{copy}</p><div class="resource-links">{render_links(links)}</div></aside>'


def render_legacy_001(issue):
    source = (ROOT / 'content/newsletter.md').read_text(encoding='utf-8')
    text = '## The classroom problem' + source.split('## The classroom problem', 1)[1]
    text = text.replace('The attached activity', 'The companion activity linked below')
    text = text.replace('activity attached to this issue', 'activity included with this issue')
    body = markdown(text)
    illustration = '<figure><img loading="lazy" src="../../assets/issue-001-cartoon.png" alt="A humorous classroom cartoon about checking an AI answer."><figcaption>AI-generated cartoon; the robot is a visual joke, not a model of how AI works.</figcaption></figure>'
    infographic = '<figure><img loading="lazy" src="../../assets/issue-001-infographic.png" alt="Try, Check, Explain: begin with your own thinking, check an answer, then explain independently."><figcaption>The proposed Try → Check → Explain routine. AI-generated illustration.</figcaption></figure>'
    body = body.replace('<h2>Cognitive Safety Box</h2>', illustration + '<h2>Cognitive Safety Box</h2>')
    body = body.replace('<h2>From Research to Practice</h2>', infographic + '<h2>From Research to Practice</h2>')
    return body, issue['resources']


def render_legacy_002(issue):
    body = (ROOT / 'content/issue-002.html').read_text(encoding='utf-8')
    return body, issue['resources']


LEGACY_RENDERERS = {
    '001': render_legacy_001,
    '002': render_legacy_002,
}


def package_figure(image, caption):
    if image is None:
        return ''
    filename = escape(image['file'], quote=True)
    alt = escape(image['alt'], quote=True)
    return f'<figure><img loading="lazy" src="../../assets/{filename}" alt="{alt}"><figcaption>{escape(caption)}</figcaption></figure>'


def package_resource_links(issue):
    links = []
    resources = issue['resources']
    if resources.get('activity'):
        links.append({
            'href': f"../../resources/issue-{issue['n']}-activity.html",
            'label': 'Open student activity',
            'class': 'button',
        })
    if resources.get('notes'):
        links.append({
            'href': f"../../resources/issue-{issue['n']}-notes.html",
            'label': 'Teacher notes & answers',
            'class': 'button secondary' if links else 'button',
        })
    return links


def render_package(issue):
    source_path = ROOT / 'content/issues' / issue['slug'] / 'newsletter.md'
    source = source_path.read_text(encoding='utf-8')
    marker = '## The classroom problem'
    text = marker + source.split(marker, 1)[1]
    text = text.replace('The attached activity', 'The companion activity linked below')
    text = text.replace('activity attached to this issue', 'activity included with this issue')
    body = markdown(text)
    illustration = package_figure(issue.get('illustration'), 'AI-generated illustration.')
    infographic = package_figure(issue.get('infographic'), 'The proposed classroom routine; not a tested intervention.')
    if illustration:
        body = body.replace('<h2>Cognitive Safety Box</h2>', illustration + '<h2>Cognitive Safety Box</h2>')
    if infographic:
        body = body.replace('<h2>From Research to Practice</h2>', infographic + '<h2>From Research to Practice</h2>')
    return body, package_resource_links(issue)


def render_issue_page(issue, other):
    if issue['kind'] == 'legacy':
        body, links = LEGACY_RENDERERS[issue['legacy_renderer']](issue)
    else:
        body, links = render_package(issue)
    box = render_resource_box(issue, links)
    number = escape(issue['n'])
    title = escape(issue['title'])
    dek = escape(issue['dek'])
    date = escape(issue['date'])
    image = escape(issue['img'], quote=True)
    alt = escape(issue['alt'], quote=True)
    caption = escape(issue['caption'])
    other_slug = escape(other['slug'], quote=True)
    other_title = escape(other['title'])
    content = f'''<header class="article-header"><p class="eyebrow">Issue {number} · Classroom practice</p><h1>{title}</h1><p class="dek">{dek}</p><p class="meta">By Chad Wadden · {date}</p></header><figure class="hero-figure"><img class="hero" src="../../assets/{image}" alt="{alt}"><figcaption>{caption}</figcaption></figure><article class="reading">{box}{body}{box}<div class="next"><span class="eyebrow">Also in the newsletter</span><p><a href="../{other_slug}/">{other_title} →</a></p></div></article>'''
    path = f"issues/{issue['slug']}/"
    write(path + 'index.html', shell(issue['title'], issue['dek'], content, '../../', path, issue['img']))


def other_issue(issues, position):
    if position == 0:
        return issues[position + 1]
    return issues[position - 1]


def render_archive_cards(issues):
    cards = []
    for issue in reversed(issues):
        slug = escape(issue['slug'], quote=True)
        image = escape(issue['img'], quote=True)
        alt = escape(issue['alt'], quote=True)
        number = escape(issue['n'])
        title = escape(issue['title'])
        dek = escape(issue['dek'])
        cards.append(f'''<article class="card"><a href="issues/{slug}/"><img loading="lazy" src="assets/{image}" alt="{alt}"></a><div class="copy"><p class="eyebrow">Issue {number}</p><h3><a href="issues/{slug}/">{title}</a></h3><p>{dek}</p><a href="issues/{slug}/">Read issue →</a></div></article>''')
    return ''.join(cards)


def render_home_resource_card(resource, distinguish):
    card_class = 'card resource-card' if distinguish else 'card'
    eyebrow = escape(resource['eyebrow'])
    title = escape(resource['title'])
    copy = escape(resource['copy'])
    links = render_links(resource['links'])
    if resource['group_links']:
        links = f'<div class="resource-links">{links}</div>'
    return f'''<article class="{card_class}"><div class="copy"><p class="eyebrow">{eyebrow}</p><h3>{title}</h3><p>{copy}</p>{links}</div></article>'''


def render_home_resources(issues):
    resources = [issue['home_resource'] for issue in reversed(issues) if issue.get('home_resource')]
    distinguish = any(issue['kind'] == 'package' for issue in issues)
    cards = ''.join(render_home_resource_card(resource, distinguish) for resource in resources)
    return f'<section id="resources"><p class="eyebrow">Take it into your classroom</p><h2>Less setup. Something to try.</h2><div class="archive">{cards}</div></section>'


def build_homepage(issues):
    latest = issues[-1]
    slug = escape(latest['slug'], quote=True)
    image = escape(latest['img'], quote=True)
    alt = escape(latest['alt'], quote=True)
    number = escape(latest['n'])
    feature_title = escape(latest.get('feature_title', latest['title']))
    feature_dek = escape(latest.get('feature_dek', latest['dek']))
    cards = render_archive_cards(issues)
    home_resources = render_home_resources(issues)
    home = f'''<section class="intro"><p class="eyebrow">A newsletter by Chad Wadden</p><h1>Useful AI ideas.<br>Ready for your classroom.</h1><p>Research, classroom ideas and ready-to-use resources for high-school teachers finding their way with AI.</p></section><section class="feature" aria-labelledby="latest"><a href="issues/{slug}/"><img src="assets/{image}" alt="{alt}"></a><div class="copy"><p class="eyebrow">The latest · Issue {number}</p><h2 id="latest">{feature_title}</h2><p>{feature_dek}</p><a href="issues/{slug}/">Read the new issue →</a></div></section><section id="issues"><h2>The issue archive</h2><div class="archive">{cards}</div></section>{home_resources}'''
    page = shell(
        'Useful AI ideas for your classroom',
        'Research, classroom ideas and ready-to-use resources for high-school teachers, by Chad Wadden.',
        home,
        image=latest['img'],
    )
    write('index.html', page)


def build_legacy_001_resources(issue):
    pages = [
        ('teacher-activity.md', 'issue-001-activity.html', 'Try → Check → Explain'),
        ('teacher-notes.md', 'issue-001-notes.html', 'Teacher notes and worked answers'),
    ]
    for source, target, title in pages:
        source_path = ROOT / 'content' / source
        source_text = source_path.read_text(encoding='utf-8')
        source_text = source_text.replace(
            'The package is a draft until you approve it.',
            'Adapt the activity to your students and your school’s expectations before classroom use.',
        )
        write('content/' + source, source_text)
        body = '<div class="resource-page"><p class="eyebrow">Issue 001 · Classroom resource</p><div class="resource-links no-print"><button onclick="window.print()">Print / save as PDF</button><a class="button secondary" href="../issues/001-ai-is-not-the-teacher/">Read the article</a></div>' + markdown(source_text) + '</div>'
        page = shell(title, 'A ten-minute evidence check and classroom resource.', body, '../', 'resources/' + target)
        write('resources/' + target, page)
    return len(pages)


def build_legacy_002_resources(issue):
    body = '<div class="resource-page">' + (ROOT / 'content/assignment-kit.html').read_text(encoding='utf-8') + '</div>'
    page = shell(
        'The assignment redesign kit',
        'A printable teacher planning sheet, worked example and student-facing instructions.',
        body,
        '../',
        'resources/assignment-redesign-kit.html',
        js=True,
    )
    write('resources/assignment-redesign-kit.html', page)
    return 1


LEGACY_RESOURCE_BUILDERS = {
    '001': build_legacy_001_resources,
    '002': build_legacy_002_resources,
}


def build_package_resources(issue):
    count = 0
    number = issue['n']
    slug = issue['slug']
    base = ROOT / 'content/issues' / slug
    definitions = [
        ('activity', 'teacher-activity.md', 'activity', 'Student activity'),
        ('notes', 'teacher-notes.md', 'notes', 'Teacher notes'),
    ]
    for resource_key, source_name, suffix, label in definitions:
        target = f'issue-{number}-{suffix}.html'
        target_path = ROOT / 'resources' / target
        if not issue['resources'].get(resource_key):
            if target_path.exists():
                target_path.unlink()
            continue
        source_text = (base / source_name).read_text(encoding='utf-8')
        issue_number = escape(number)
        issue_slug = escape(slug, quote=True)
        body = f'<div class="resource-page"><p class="eyebrow">Issue {issue_number} · Classroom resource</p><div class="resource-links no-print"><button onclick="window.print()">Print / save as PDF</button><a class="button secondary" href="../issues/{issue_slug}/">Read the article</a></div>' + markdown(source_text) + '</div>'
        title = f"{issue['title']} — {label}"
        page = shell(title, issue['resourcecopy'], body, '../', 'resources/' + target)
        write('resources/' + target, page)
        count += 1
    return count


def remove_replaced_package_page(issue):
    issue_root = ROOT / 'issues'
    current = issue_root / issue['slug']
    for candidate in issue_root.glob(f"{issue['n']}-*"):
        if candidate == current or not candidate.is_dir():
            continue
        for child in candidate.iterdir():
            if child.is_file():
                child.unlink()
        candidate.rmdir()


def main():
    issues = load_issues()
    for position, issue in enumerate(issues):
        if issue['kind'] == 'package':
            remove_replaced_package_page(issue)
        render_issue_page(issue, other_issue(issues, position))
    build_homepage(issues)
    resource_count = 0
    for issue in issues:
        if issue['kind'] == 'legacy':
            resource_count += LEGACY_RESOURCE_BUILDERS[issue['legacy_renderer']](issue)
        else:
            resource_count += build_package_resources(issue)
    write('.nojekyll', '')
    favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#152f3e"/><text x="32" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="43" fill="#f7f4ec">C</text></svg>'
    write('assets/favicon.svg', favicon)
    print(f'Built homepage, {len(issues)} issues and {resource_count} resources.')


if __name__ == '__main__':
    main()
