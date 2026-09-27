#!/usr/bin/env python3
"""Build the newsletter's static pages with the Python standard library."""
from pathlib import Path
from html import escape
import re
ROOT = Path(__file__).resolve().parent
BASE = 'https://ctwadden.github.io/cognitive-first-ai/'

def inline(s):
    s=escape(s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
    return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)

def markdown(s):
    out=[]
    for block in s.strip().split('\n\n'):
        if block.startswith('#'):
            line,*rest=block.split('\n'); level=len(line)-len(line.lstrip('#'))
            out.append(f'<h{level}>{inline(line[level:].strip())}</h{level}>')
            if rest: out.append('<p>'+inline(' '.join(rest))+'</p>')
        else: out.append('<p>'+inline(block).replace('\n','<br>')+'</p>')
    return '\n'.join(out)

def shell(title, description, body, prefix='', path='', image=None, js=False):
    fulltitle=f'{title} | Cognitive-First AI'
    share=f'<meta property="og:image" content="{BASE}assets/{image}">' if image else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(fulltitle)}</title><meta name="description" content="{escape(description,quote=True)}"><link rel="canonical" href="{BASE}{path}"><meta property="og:title" content="{escape(fulltitle,quote=True)}"><meta property="og:description" content="{escape(description,quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}{path}">{share}<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"></head><body><a class="skip" href="#main">Skip to content</a><header class="masthead"><div class="wrap"><a class="brand" href="{prefix}index.html">Cognitive-First <span>AI</span></a><nav aria-label="Main"><a href="{prefix}index.html#issues">Issues</a><a href="{prefix}index.html#resources">Teacher resources</a><a href="mailto:cwadden@gnspes.ca">Contact Chad</a></nav></div></header><main id="main" class="wrap">{body}</main><footer class="footer"><div class="wrap"><p><strong>Cognitive-First AI</strong><br>Practical ideas for high-school teachers.<br>Written with AI assistance; sources and limitations are listed with each issue.</p><p>Chad Wadden<br><a href="mailto:cwadden@gnspes.ca">cwadden@gnspes.ca</a><br>Illustrations created with AI.</p></div></footer>{f'<script src="{prefix}assets/planner.js"></script>' if js else ''}</body></html>'''

def write(path,text):
    (ROOT/path).write_text(text,encoding='utf-8')

issues=[
 dict(n='001',slug='001-ai-is-not-the-teacher',title='AI Is Not the Teacher: What Generative AI Can and Cannot Do',dek='A practical first step, a ten-minute activity and a check for understanding.',img='issue-001-cover.png',alt='Illustrated newsletter cover featuring Chad Wadden and the message AI is not the teacher.'),
 dict(n='002',slug='002-the-assignment-makeover',title='The Assignment Makeover: Same Learning Goal. Better Evidence.',dek='Three practical before-and-after upgrades for essays, science reports and coding tasks.',img='issue-002-makeover-cover.png',alt='Cut-paper illustration of an assignment transformed from a plain sheet into annotated evidence, titled The Assignment Makeover.')]
for issue in issues:
    n=issue['n']; path=f"issues/{issue['slug']}/"
    if n=='001':
        text=(ROOT/'content/newsletter.md').read_text().split('## The classroom problem',1)[1]
        text='## The classroom problem'+text
        text=text.replace('The attached activity','The companion activity linked below').replace('activity attached to this issue','activity included with this issue')
        body=markdown(text)
        body=body.replace('<h2>Cognitive Safety Box</h2>','<figure><img loading="lazy" src="../../assets/issue-001-cartoon.png" alt="A humorous classroom cartoon about checking an AI answer."><figcaption>AI-generated cartoon; the robot is a visual joke, not a model of how AI works.</figcaption></figure><h2>Cognitive Safety Box</h2>')
        body=body.replace('<h2>From Research to Practice</h2>','<figure><img loading="lazy" src="../../assets/issue-001-infographic.png" alt="Try, Check, Explain: begin with your own thinking, check an answer, then explain independently."><figcaption>The proposed Try → Check → Explain routine. AI-generated illustration.</figcaption></figure><h2>From Research to Practice</h2>')
        resources='<a class="button" href="../../resources/issue-001-activity.html">Open student activity</a><a class="button secondary" href="../../resources/issue-001-notes.html">Teacher notes &amp; answers</a>'
        resourcecopy='A ready-to-use, ten-minute evidence check. Fictional data, a deliberately flawed answer and worked teacher notes. No AI account needed.'
        other=issues[1]; date='Prepared September 13 · Published September 27, 2026'
    else:
        body=(ROOT/'content/issue-002.html').read_text()
        resources='<a class="button" href="../../resources/assignment-redesign-kit.html">Open the redesign kit</a><a class="button secondary" href="../../assets/issue-002-makeover-infographic.png" download>Download infographic</a>'
        resourcecopy='A printable planning sheet, worked redesign and student-facing instructions. Fill it in on screen, then print or save as PDF.'
        other=issues[0]; date='Published September 27, 2026'
    box=f'<aside class="resource-box"><h2>Your companion resource</h2><p>{resourcecopy}</p><div class="resource-links">{resources}</div></aside>'
    caption='AI-generated illustration of Chad Wadden, based on a supplied AI-enhanced reference portrait.' if n=='001' else 'AI-generated editorial collage. The marks and graph are conceptual illustrations, not research data.'
    content=f'''<header class="article-header"><p class="eyebrow">Issue {n} · Classroom practice</p><h1>{issue['title']}</h1><p class="dek">{issue['dek']}</p><p class="meta">By Chad Wadden · {date}</p></header><figure class="hero-figure"><img class="hero" src="../../assets/{issue['img']}" alt="{issue['alt']}"><figcaption>{caption}</figcaption></figure><article class="reading">{box}{body}{box}<div class="next"><span class="eyebrow">Also in the newsletter</span><p><a href="../{other['slug']}/">{other['title']} →</a></p></div></article>'''
    write(path+'index.html',shell(issue['title'],issue['dek'],content,'../../',path,issue['img']))
latest=issues[1]
cards=''.join(f'''<article class="card"><a href="issues/{i['slug']}/"><img loading="lazy" src="assets/{i['img']}" alt="{i['alt']}"></a><div class="copy"><p class="eyebrow">Issue {i['n']}</p><h3><a href="issues/{i['slug']}/">{i['title']}</a></h3><p>{i['dek']}</p><a href="issues/{i['slug']}/">Read issue →</a></div></article>''' for i in reversed(issues))
home=f'''<section class="intro"><p class="eyebrow">A newsletter by Chad Wadden</p><h1>Useful AI ideas.<br>Ready for your classroom.</h1><p>Research, classroom ideas and ready-to-use resources for high-school teachers finding their way with AI.</p></section><section class="feature" aria-labelledby="latest"><a href="issues/{latest['slug']}/"><img src="assets/{latest['img']}" alt="{latest['alt']}"></a><div class="copy"><p class="eyebrow">The latest · Issue 002</p><h2 id="latest">The Assignment Makeover</h2><p>An essay. A science report. A coding task. See what to change—and what you can take out.</p><a href="issues/{latest['slug']}/">Read the new issue →</a></div></section><section id="issues"><h2>The issue archive</h2><div class="archive">{cards}</div></section><section id="resources"><p class="eyebrow">Take it into your classroom</p><h2>Less setup. Something to try.</h2><div class="archive"><article class="card"><div class="copy"><p class="eyebrow">Issue 002 · Teacher planning kit</p><h3>Upgrade one assignment</h3><p>A ten-minute planning sheet, a worked redesign and instructions you can adapt for students.</p><a class="button" href="resources/assignment-redesign-kit.html">Open the redesign kit</a></div></article><article class="card"><div class="copy"><p class="eyebrow">Issue 001 · Classroom activity</p><h3>Try → Check → Explain</h3><p>A ten-minute reasoning exercise with fictional data, a flawed claim and worked answers.</p><div class="resource-links"><a class="button" href="resources/issue-001-activity.html">Student activity</a><a href="resources/issue-001-notes.html">Teacher notes →</a></div></div></article></div></section>'''
write('index.html',shell('Useful AI ideas for your classroom','Research, classroom ideas and ready-to-use resources for high-school teachers, by Chad Wadden.',home,image='issue-002-makeover-cover.png'))
for source,target,title in [('teacher-activity.md','issue-001-activity.html','Try → Check → Explain'),('teacher-notes.md','issue-001-notes.html','Teacher notes and worked answers')]:
    source_text=(ROOT/'content'/source).read_text().replace('The package is a draft until you approve it.','Adapt the activity to your students and your school’s expectations before classroom use.')
    write('content/'+source,source_text)
    body='<div class="resource-page"><p class="eyebrow">Issue 001 · Classroom resource</p><div class="resource-links no-print"><button onclick="window.print()">Print / save as PDF</button><a class="button secondary" href="../issues/001-ai-is-not-the-teacher/">Read the article</a></div>'+markdown(source_text)+'</div>'
    write('resources/'+target,shell(title,'A ten-minute evidence check and classroom resource.',body,'../','resources/'+target))
write('resources/assignment-redesign-kit.html',shell('The assignment redesign kit','A printable teacher planning sheet, worked example and student-facing instructions.','<div class="resource-page">'+(ROOT/'content/assignment-kit.html').read_text()+'</div>','../','resources/assignment-redesign-kit.html',js=True))
write('.nojekyll','')
write('assets/favicon.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#152f3e"/><text x="32" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="43" fill="#f7f4ec">C</text></svg>')
print('Built homepage, 2 issues and 3 resources.')
