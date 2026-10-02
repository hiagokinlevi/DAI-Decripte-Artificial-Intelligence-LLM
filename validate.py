# Copyright (c) 2026 Hiago Kin Levi. All rights reserved. SPDX-License-Identifier: LicenseRef-Proprietary
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
REPO = json.loads((ROOT / 'papers.json').read_text())['repositoryName']
PREFIX = f'https://hiagokinlevi.github.io/{REPO}/'


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.meta, self.scripts = [], set(), {}, []
        self.in_schema = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.add(values['id'])
        for name in ['href', 'src']:
            if name in values:
                self.links.append(values[name])
        if tag == 'meta':
            self.meta[values.get('name', values.get('property'))] = values.get('content')
        if tag == 'script' and values.get('type') == 'application/ld+json':
            self.in_schema = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_schema = False

    def handle_data(self, data):
        if self.in_schema:
            self.scripts.append(json.loads(data))


def main():
    errors = []
    files = list(ROOT.rglob('*.html'))
    documents = {}
    for path in files:
        text = path.read_text()
        if re.fullmatch(r'google[0-9a-f]+\.html', path.name):
            if text.strip() != f'google-site-verification: {path.name}':
                errors.append(f'Invalid ownership verification: {path.name}')
            continue
        parsed = Document()
        parsed.feed(text)
        documents[path.resolve()] = parsed
        if not parsed.meta.get('description') or not parsed.scripts:
            errors.append(f'Missing discovery metadata: {path.name}')
        if re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN .*PRIVATE KEY', text):
            errors.append(f'Credential-like content: {path.name}')
    for path, doc in documents.items():
        for value in doc.links:
            url = urlparse(value)
            if value.startswith(PREFIX):
                target = ROOT / unquote(url.path.split(f'/{REPO}/', 1)[1])
            elif url.netloc == 'hiagokinlevi.github.io' and url.path.split('/')[1] in ['DAI-Decripte-Artificial-Intelligence-LLM', 'ADAI-Autonomous-Defensive-Artificial-Intelligence']:
                companion = url.path.split('/')[1]
                relative = '/'.join(url.path.split('/')[2:])
                sibling_names = {'DAI-Decripte-Artificial-Intelligence-LLM': 'dai-paper-public', 'ADAI-Autonomous-Defensive-Artificial-Intelligence': 'adai-paper-public'}
                sibling = ROOT.parent / sibling_names[companion]
                if not sibling.exists():
                    continue
                target = sibling / unquote(relative)
            elif not url.scheme and not url.netloc:
                target = path.parent / unquote(url.path) if url.path else path
            else:
                continue
            if target.is_dir():
                target = target / 'index.html'
            if not target.exists():
                errors.append(f'Missing target: {value}')
            if url.fragment and target.resolve() in documents and url.fragment not in documents[target.resolve()].ids:
                errors.append(f'Missing fragment: {value}')
    for item in json.loads((ROOT/'manifest.json').read_text()):
        data = (ROOT/item['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256'] or len(data) != item['bytes']:
            errors.append(f'Manuscript mismatch: {item["file"]}')
    for path in ['sitemap.xml', 'feed.xml']:
        ElementTree.parse(ROOT/path)
    for slug in ['dai', 'adai']:
        page = ROOT/f'{slug}.html'
        if page.exists():
            meta = documents[page.resolve()].meta
            if not all(meta.get(k) for k in ['citation_title','citation_author','citation_pdf_url','citation_doi']):
                errors.append(f'Missing academic metadata: {slug}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(documents)} pages, ownership verification, local links, fragments, academic metadata, XML and manuscript checksums')


if __name__ == '__main__':
    main()
