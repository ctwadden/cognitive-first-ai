#!/usr/bin/env python3
"""Import an approved Issue package into the static newsletter source."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata


class Refusal(Exception):
    """An expected package validation failure."""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', help='approved Issue package folder')
    parser.add_argument('--number', help='issue number from 1 to 999')
    parser.add_argument('--date', dest='date_line', help='published display line')
    parser.add_argument(
        '--site',
        default=str(Path(__file__).resolve().parent),
        help='site root (defaults to the folder containing this script)',
    )
    return parser.parse_args()


def read_json(path, label):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise Refusal(f'{label} is missing: {path}') from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Refusal(f'{label} could not be read as JSON: {error}') from error


def issue_number(value):
    if isinstance(value, bool):
        raise Refusal('issue number must be an integer from 1 to 999')
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise Refusal('issue number must be an integer from 1 to 999') from error
    if str(value).strip() != str(number) and not str(value).strip().isdigit():
        raise Refusal('issue number must be an integer from 1 to 999')
    if not 1 <= number <= 999:
        raise Refusal('issue number must be from 1 to 999')
    return f'{number:03d}'


def slugify(topic):
    normalized = unicodedata.normalize('NFKD', topic)
    ascii_topic = normalized.encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_topic).strip('-')[:50].rstrip('-')
    if not slug:
        raise Refusal('the package topic must contain a letter or number usable in a slug')
    return slug


def published_date(value):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise Refusal('newsletter.date must be an ISO date such as 2026-10-11') from error
    return f'Published {parsed.strftime("%B")} {parsed.day}, {parsed.year}'


def preheader(newsletter):
    match = re.search(r'^Preheader:\s*(.+?)\s*$', newsletter, flags=re.MULTILINE)
    if not match:
        raise Refusal('draft/newsletter.md must contain a non-empty Preheader: line')
    return match.group(1)


def validate_newsletter(newsletter):
    section = re.search(r'^## The classroom problem\s*$', newsletter, flags=re.MULTILINE)
    if not section:
        raise Refusal('draft/newsletter.md must contain a "## The classroom problem" section')


def validate_status(package):
    status_path = package / 'status.json'
    if not status_path.exists():
        return
    status = read_json(status_path, 'status.json')
    findings = status.get('findings', []) if isinstance(status, dict) else []
    if not isinstance(findings, list):
        raise Refusal('status.json findings must be a list')
    for finding in findings:
        if isinstance(finding, dict) and str(finding.get('severity', '')).lower() == 'block':
            message = finding.get('message') or finding.get('code') or 'unspecified blocking finding'
            raise Refusal(f'package has a blocking status finding: {message}')


def image_extension(path):
    try:
        header = path.read_bytes()[:12]
    except OSError as error:
        raise Refusal(f'image listed in images.json is missing or unreadable: {path.name}') from error
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if header.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'webp'
    raise Refusal(f'image listed in images.json is not a PNG, JPEG or WebP: {path.name}')


def listed_image_path(images_folder, filename):
    if not isinstance(filename, str) or not filename:
        raise Refusal('every images.json entry must have a file name')
    relative = Path(filename)
    if relative.is_absolute() or '..' in relative.parts:
        raise Refusal(f'unsafe image path in images.json: {filename}')
    path = (images_folder / relative).resolve()
    try:
        path.relative_to(images_folder.resolve())
    except ValueError as error:
        raise Refusal(f'unsafe image path in images.json: {filename}') from error
    if not path.is_file():
        raise Refusal(f'image listed in images.json is missing: {filename}')
    return path


def validate_images(draft, number):
    images_folder = draft / 'images'
    manifest = read_json(images_folder / 'images.json', 'draft/images/images.json')
    if not isinstance(manifest, list):
        raise Refusal('draft/images/images.json must contain an array')
    roles = {}
    names = {'hero': 'cover', 'cartoon': 'illustration', 'infographic': 'infographic'}
    for image in manifest:
        if not isinstance(image, dict):
            raise Refusal('every images.json item must be an object')
        source = listed_image_path(images_folder, image.get('file'))
        extension = image_extension(source)
        role = image.get('role')
        alt = image.get('alt')
        if not isinstance(alt, str) or not alt.strip():
            raise Refusal(f'image {source.name} must have non-empty alt text')
        if role not in names:
            continue
        if role in roles:
            raise Refusal(f'images.json contains more than one {role} image')
        target_name = f'issue-{number}-{names[role]}.{extension}'
        roles[role] = {
            'source': source,
            'target_name': target_name,
            'alt': alt,
            'provenance': image.get('provenance'),
        }
    if 'hero' not in roles:
        raise Refusal('images.json must list one image with role "hero"')
    return roles


def optional_source(draft, name):
    path = draft / name
    return path if path.is_file() else None


def read_site_issues(site):
    path = site / 'content/issues.json'
    data = read_json(path, 'site content/issues.json')
    if not isinstance(data, list):
        raise Refusal('site content/issues.json must contain an array')
    return data


def safe_existing_slug(entry, number):
    slug = entry.get('slug')
    pattern = rf'{re.escape(number)}-[a-z0-9]+(?:-[a-z0-9]+)*'
    if not isinstance(slug, str) or not re.fullmatch(pattern, slug):
        raise Refusal(f'existing issue {number} has an unsafe slug and cannot be replaced')
    return slug


def remove_existing_package(site, entry, number):
    old_slug = safe_existing_slug(entry, number)
    old_content = site / 'content/issues' / old_slug
    if old_content.exists():
        if not old_content.is_dir() or old_content.is_symlink():
            raise Refusal(f'existing content path is not a safe directory: {old_content}')
        shutil.rmtree(old_content)
    for role in ('cover', 'illustration', 'infographic'):
        for asset in (site / 'assets').glob(f'issue-{number}-{role}.*'):
            if asset.is_file() and not asset.is_symlink():
                asset.unlink()


def make_entry(number, slug, title, dek, date_line, images, activity, notes):
    hero = images['hero']
    illustration = images.get('cartoon')
    infographic = images.get('infographic')
    caption = hero.get('provenance')
    if not isinstance(caption, str) or not caption.strip():
        caption = 'AI-generated illustration.'

    def image_entry(image):
        if image is None:
            return None
        return {'file': image['target_name'], 'alt': image['alt']}

    has_resources = activity is not None or notes is not None
    resourcecopy = 'Ready-to-use classroom materials for this issue.' if has_resources else ''
    return {
        'kind': 'package',
        'n': number,
        'slug': slug,
        'title': title,
        'dek': dek,
        'date': date_line,
        'img': hero['target_name'],
        'alt': hero['alt'],
        'caption': caption,
        'illustration': image_entry(illustration),
        'infographic': image_entry(infographic),
        'resources': {
            'activity': activity is not None,
            'notes': notes is not None,
        },
        'resourcecopy': resourcecopy,
    }


def write_issues(site, issues):
    path = site / 'content/issues.json'
    text = json.dumps(issues, ensure_ascii=False, indent=2) + '\n'
    path.write_text(text, encoding='utf-8')


def import_issue(args):
    package = Path(args.package).expanduser().resolve()
    site = Path(args.site).expanduser().resolve()
    if not package.is_dir():
        raise Refusal(f'package folder is missing: {package}')
    if not site.is_dir():
        raise Refusal(f'site root is missing: {site}')
    order = read_json(package / 'order.json', 'order.json')
    if not isinstance(order, dict):
        raise Refusal('order.json must contain an object')
    draft = package / 'draft'
    newsletter_path = draft / 'newsletter.md'
    if not newsletter_path.is_file():
        raise Refusal(f'draft/newsletter.md is missing: {newsletter_path}')
    try:
        newsletter = newsletter_path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise Refusal(f'draft/newsletter.md could not be read: {error}') from error
    validate_newsletter(newsletter)
    validate_status(package)
    title = order.get('topic')
    if not isinstance(title, str) or not title.strip():
        raise Refusal('order.json topic must be a non-empty title')
    newsletter_order = order.get('newsletter')
    if not isinstance(newsletter_order, dict):
        raise Refusal('order.json newsletter must be an object')
    number_value = args.number if args.number is not None else newsletter_order.get('issue')
    number = issue_number(number_value)
    date_line = args.date_line or published_date(newsletter_order.get('date'))
    dek = preheader(newsletter)
    slug = f'{number}-{slugify(title)}'
    images = validate_images(draft, number)
    activity = optional_source(draft, 'teacher-activity.md')
    notes = optional_source(draft, 'teacher-notes.md')
    issues = read_site_issues(site)
    same_number = [entry for entry in issues if entry.get('n') == number]
    if any(entry.get('kind') == 'legacy' for entry in same_number):
        raise Refusal(f'issue {number} is legacy and cannot be replaced')
    for entry in same_number:
        remove_existing_package(site, entry, number)
    content_folder = site / 'content/issues' / slug
    content_folder.mkdir(parents=True, exist_ok=False)
    shutil.copy2(newsletter_path, content_folder / 'newsletter.md')
    if activity is not None:
        shutil.copy2(activity, content_folder / 'teacher-activity.md')
    if notes is not None:
        shutil.copy2(notes, content_folder / 'teacher-notes.md')
    asset_paths = []
    for role in ('hero', 'cartoon', 'infographic'):
        image = images.get(role)
        if image is None:
            continue
        target = site / 'assets' / image['target_name']
        shutil.copy2(image['source'], target)
        asset_paths.append(f"assets/{image['target_name']}")
    entry = make_entry(number, slug, title, dek, date_line, images, activity, notes)
    retained = [existing for existing in issues if existing.get('n') != number]
    retained.append(entry)
    retained.sort(key=lambda item: int(item['n']))
    write_issues(site, retained)
    resource_paths = []
    if activity is not None:
        resource_paths.append(f'resources/issue-{number}-activity.html')
    if notes is not None:
        resource_paths.append(f'resources/issue-{number}-notes.html')
    result = {
        'number': number,
        'slug': slug,
        'page': f'issues/{slug}/',
        'resources': resource_paths,
        'assets': asset_paths,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))


def main():
    args = parse_args()
    try:
        import_issue(args)
    except Refusal as error:
        print(f'Cannot add issue: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
