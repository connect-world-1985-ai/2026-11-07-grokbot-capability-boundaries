"""Render and validate the local HTML; no external service or browser session."""
import json
import re
from collections import Counter
from pathlib import Path

import html5lib
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent


def validate():
    text = (ROOT / 'index.html').read_text()
    assert not re.search(r'https?://', text), 'Remote reference in HTML'
    parser = html5lib.HTMLParser(strict=False)
    parser.parse(text)
    assert not parser.errors, parser.errors
    expected = json.loads((ROOT / 'data.json').read_text())
    result = {'html5_parse_errors': len(parser.errors), 'viewports': []}
    uri = (ROOT / 'index.html').as_uri()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for width, screenshot in [(2100, 'preview.png'), (1440, None), (1200, None), (390, 'preview-mobile.png')]:
            page = browser.new_page(viewport={'width': width, 'height': 1000}, device_scale_factor=1)
            requests = []
            page.on('request', lambda request: requests.append(request.url))
            page.goto(uri, wait_until='networkidle')
            assert requests == [uri], requests
            assert page.locator('script').count() == 0
            cells = page.locator('tr').evaluate_all('(rows) => rows.map(row => row.children.length)')
            assert set(cells) == {5}, cells
            dom_counts = {}
            for section in expected['sections']:
                rows = page.locator('#' + section['id'] + ' tbody tr')
                c = Counter(rows.evaluate_all('(rows) => rows.map(row => row.dataset.status)'))
                ex = Counter(row['status'] for row in section['rows'])
                assert c == ex, (section['id'], c, ex)
                dom_counts[section['id']] = dict(c)
                tile = page.locator('[data-card="' + section['id'] + '"]')
                if tile.count():
                    for field, status in [('s', 'Supported'), ('u', 'Unsupported'), ('uv', 'Unverified')]:
                        assert int(tile.get_attribute('data-' + field)) == c[status]
                assert rows.locator('.verify').count() == c['Unverified']
            pending = sum(c.get('Unverified', 0) for c in dom_counts.values())
            assert int(page.locator('[data-pending]').get_attribute('data-pending')) == pending
            overflow = page.evaluate('''() => ({
              page: document.documentElement.scrollWidth > innerWidth,
              tiles: [...document.querySelectorAll('.tile')].filter(e => e.scrollWidth > e.clientWidth + 1).length,
              dates: [...document.querySelectorAll('.date')].filter(e => e.scrollWidth > e.clientWidth + 1).length,
              cells: [...document.querySelectorAll('th,td')].filter(e => e.scrollWidth > e.clientWidth + 1).length
            })''')
            assert not any(overflow.values()), (width, overflow)
            if screenshot:
                page.screenshot(path=str(ROOT / screenshot), full_page=True)
            result['viewports'].append(dict(width=width, requests=requests, overflow=overflow, counts=dom_counts,
                                            pending=pending, rows=sum(sum(c.values()) for c in dom_counts.values()),
                                            screenshot=screenshot, height=page.locator('body').bounding_box()['height']))
            page.close()
        browser.close()
    (ROOT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    validate()
