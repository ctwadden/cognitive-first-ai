#!/usr/bin/env python3
"""Tests for importing Issue packages and rebuilding the static site."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE_SITE = Path(__file__).resolve().parent
SAMPLE_PACKAGE = Path(
    '/Users/cdawg/Desktop/content-intelligence-studio/'
    'content-studio-main-cis23/fixtures/production/issue-sample'
)


class SiteTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='newsletter-test-')
        self.root = Path(self.temporary.name)
        self.site = self.root / 'site'
        shutil.copytree(
            SOURCE_SITE,
            self.site,
            ignore=shutil.ignore_patterns('.git', '__pycache__'),
        )

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, name, *arguments):
        return subprocess.run(
            [sys.executable, name, *arguments],
            cwd=self.site,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def copy_package(self, name='package'):
        target = self.root / name
        shutil.copytree(SAMPLE_PACKAGE, target)
        return target

    def add_sample(self, package=None, number='003', date_line=None):
        package = package or SAMPLE_PACKAGE
        arguments = [str(package), '--number', number]
        if date_line is not None:
            arguments.extend(['--date', date_line])
        return self.run_script('add_issue.py', *arguments)

    def generated_snapshot(self):
        paths = [
            self.site / 'index.html',
            self.site / '.nojekyll',
            self.site / 'assets/favicon.svg',
        ]
        paths.extend(sorted((self.site / 'issues').rglob('*')))
        paths.extend(sorted((self.site / 'resources').rglob('*')))
        return {
            path.relative_to(self.site).as_posix(): path.read_bytes()
            for path in paths
            if path.is_file()
        }

    def test_legacy_build_is_byte_identical(self):
        before = self.generated_snapshot()
        result = self.run_script('build.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'Built homepage, 2 issues and 3 resources.\n')
        self.assertEqual(self.generated_snapshot(), before)

    def test_add_sample_and_build(self):
        issue_001 = self.site / 'issues/001-ai-is-not-the-teacher/index.html'
        issue_001_before = issue_001.read_bytes()
        added = self.add_sample(date_line='Published October 11, 2026')
        self.assertEqual(added.returncode, 0, added.stderr)
        self.assertEqual(len(added.stdout.strip().splitlines()), 1)
        result = json.loads(added.stdout)
        slug = result['slug']
        self.assertTrue(slug.startswith('003-ai-is-not-the-teacher'))
        self.assertLessEqual(len(slug), 54)
        self.assertFalse(slug.endswith('-'))
        built = self.run_script('build.py')
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertEqual(built.stdout, 'Built homepage, 3 issues and 5 resources.\n')
        page = (self.site / 'issues' / slug / 'index.html').read_text(encoding='utf-8')
        self.assertIn('AI Is Not the Teacher', page)
        self.assertNotIn('Subject:', page)
        self.assertNotIn('Preheader:', page)
        self.assertIn('Published October 11, 2026', page)
        self.assertIn('The companion activity linked below', page)
        self.assertNotIn('The attached activity', page)
        self.assertIn('activity included with this issue', page)
        self.assertIn('doi.org/10.1073/pnas.2422633122', page)
        self.assertIn('002-the-assignment-makeover', page)
        for filename in (
            'issue-003-cover.png',
            'issue-003-illustration.png',
            'issue-003-infographic.png',
        ):
            self.assertIn(filename, page)
            self.assertTrue((self.site / 'assets' / filename).is_file())
        illustration = 'issue-003-illustration.png'
        illustration_heading = 'Cognitive Safety Box</h2>'
        infographic = 'issue-003-infographic.png'
        infographic_heading = 'From Research to Practice</h2>'
        self.assertLess(page.find(illustration), page.find(illustration_heading))
        self.assertLess(page.find(infographic), page.find(infographic_heading))
        self.assertGreater(page.find(infographic), page.find(illustration_heading))
        for suffix in ('activity', 'notes'):
            link = f'resources/issue-003-{suffix}.html'
            self.assertIn(link, page)
            resource = self.site / link
            self.assertTrue(resource.is_file())
            self.assertIn('window.print()', resource.read_text(encoding='utf-8'))
        home = (self.site / 'index.html').read_text(encoding='utf-8')
        positions = [
            home.find(f'issues/{slug}/'),
            home.find('issues/002-the-assignment-makeover/'),
            home.find('issues/001-ai-is-not-the-teacher/'),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(home.count('class="card"'), 3)
        self.assertIn('issue-003-cover.png', home)
        self.assertEqual(issue_001.read_bytes(), issue_001_before)

    def test_same_number_replaces_without_duplicates(self):
        first = self.add_sample()
        self.assertEqual(first.returncode, 0, first.stderr)
        first_slug = json.loads(first.stdout)['slug']
        replacement = self.copy_package('replacement')
        order_path = replacement / 'order.json'
        order = json.loads(order_path.read_text(encoding='utf-8'))
        order['topic'] = 'A Replacement Topic'
        order_path.write_text(json.dumps(order), encoding='utf-8')
        second = self.add_sample(replacement)
        self.assertEqual(second.returncode, 0, second.stderr)
        second_slug = json.loads(second.stdout)['slug']
        self.assertNotEqual(first_slug, second_slug)
        entries = json.loads((self.site / 'content/issues.json').read_text(encoding='utf-8'))
        self.assertEqual([entry['n'] for entry in entries], ['001', '002', '003'])
        self.assertFalse((self.site / 'content/issues' / first_slug).exists())
        self.assertTrue((self.site / 'content/issues' / second_slug).is_dir())
        assets = sorted((self.site / 'assets').glob('issue-003-*'))
        self.assertEqual(len(assets), 3)
        built = self.run_script('build.py')
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertFalse((self.site / 'issues' / first_slug).exists())
        self.assertTrue((self.site / 'issues' / second_slug / 'index.html').is_file())

    def assert_refused(self, package, *arguments):
        result = self.run_script('add_issue.py', str(package), *arguments)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertGreater(len(result.stderr.strip()), 10)
        return result

    def test_refuses_invalid_packages_before_changing_site(self):
        initial = (self.site / 'content/issues.json').read_bytes()

        missing = self.root / 'missing-package'
        self.assert_refused(missing, '--number', '003')

        no_order = self.copy_package('no-order')
        (no_order / 'order.json').unlink()
        self.assert_refused(no_order, '--number', '003')

        no_newsletter = self.copy_package('no-newsletter')
        (no_newsletter / 'draft/newsletter.md').unlink()
        self.assert_refused(no_newsletter, '--number', '003')

        no_section = self.copy_package('no-section')
        (no_section / 'draft/newsletter.md').write_text(
            'Subject: Test\nPreheader: Test\n\n## A different section\nText\n',
            encoding='utf-8',
        )
        self.assert_refused(no_section, '--number', '003')

        blocked = self.copy_package('blocked')
        status = {
            'findings': [
                {'severity': 'block', 'message': 'A source needs review.'},
            ],
        }
        (blocked / 'status.json').write_text(json.dumps(status), encoding='utf-8')
        self.assert_refused(blocked, '--number', '003')

        missing_image = self.copy_package('missing-image')
        (missing_image / 'draft/images/cover.png').unlink()
        self.assert_refused(missing_image, '--number', '003')

        fake_image = self.copy_package('fake-image')
        (fake_image / 'draft/images/cover.png').write_text('not an image', encoding='utf-8')
        self.assert_refused(fake_image, '--number', '003')

        invalid_number = self.copy_package('invalid-number')
        self.assert_refused(invalid_number, '--number', '1000')

        legacy = self.copy_package('legacy')
        self.assert_refused(legacy, '--number', '001')

        self.assertEqual((self.site / 'content/issues.json').read_bytes(), initial)
        self.assertFalse((self.site / 'content/issues').exists())
        self.assertEqual(list((self.site / 'assets').glob('issue-003-*')), [])

    def test_package_text_is_html_escaped(self):
        package = self.copy_package('escaped')
        order_path = package / 'order.json'
        order = json.loads(order_path.read_text(encoding='utf-8'))
        order['topic'] = 'Thinking <script>alert(1)</script> first'
        order_path.write_text(json.dumps(order), encoding='utf-8')
        newsletter_path = package / 'draft/newsletter.md'
        newsletter = newsletter_path.read_text(encoding='utf-8')
        newsletter = newsletter.replace(
            'A polished answer can arrive in seconds.',
            'A polished <img src=x onerror=alert(1)> answer can arrive in seconds.',
        )
        newsletter_path.write_text(newsletter, encoding='utf-8')
        images_path = package / 'draft/images/images.json'
        images = json.loads(images_path.read_text(encoding='utf-8'))
        images[0]['alt'] = '\"><script>alert(2)</script>'
        images_path.write_text(json.dumps(images), encoding='utf-8')
        added = self.add_sample(package, number='003')
        self.assertEqual(added.returncode, 0, added.stderr)
        slug = json.loads(added.stdout)['slug']
        self.assertRegex(slug, r'^003-[a-z0-9-]+$')
        built = self.run_script('build.py')
        self.assertEqual(built.returncode, 0, built.stderr)
        page = (self.site / 'issues' / slug / 'index.html').read_text(encoding='utf-8')
        home = (self.site / 'index.html').read_text(encoding='utf-8')
        for html in (page, home):
            self.assertNotIn('<script>alert(1)</script>', html)
            self.assertNotIn('<script>alert(2)</script>', html)
            self.assertNotIn('<img src=x onerror', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', page)
        self.assertIn('&quot;&gt;&lt;script&gt;alert(2)&lt;/script&gt;', page)


if __name__ == '__main__':
    unittest.main()
