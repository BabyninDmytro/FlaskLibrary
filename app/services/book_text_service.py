from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
from typing import Iterable

from flask import current_app

_TAG_RE = re.compile(r'<[^>]+>')
_H2_SECTION_RE = re.compile(r'<h2[^>]*>(.*?)</h2>(.*?)(?=<h2[^>]*>|</body>)', re.IGNORECASE | re.DOTALL)
_PARAGRAPH_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)
_KEY_FACT_ITEM_RE = re.compile(
    r'<li[^>]*>\s*<strong[^>]*>(.*?):</strong>\s*(.*?)\s*</li>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(slots=True)
class FactItem:
    label: str
    value: str


@dataclass(slots=True)
class InfoSection:
    title: str
    body: str


@dataclass(slots=True)
class BookTextPreview:
    summary: str
    facts: list[FactItem]
    sections: list[InfoSection]


def load_book_text_preview(book_id: int) -> BookTextPreview | None:
    static_folder = current_app.static_folder
    if not static_folder:
        return None

    source_path = Path(static_folder) / 'book_text' / f'book-{book_id}.html'
    if not source_path.exists():
        return None

    content = source_path.read_text(encoding='utf-8')
    summary = _extract_summary(content)
    facts = _extract_key_facts(content)
    sections = _extract_info_sections(content)

    if not summary and not facts and not sections:
        return None

    return BookTextPreview(summary=summary, facts=facts, sections=sections)


def _extract_summary(content: str) -> str:
    h1_match = re.search(r'<h1[^>]*>.*?</h1>', content, flags=re.IGNORECASE | re.DOTALL)
    if not h1_match:
        return ''

    first_h2_match = re.search(r'<h2[^>]*>', content[h1_match.end() :], flags=re.IGNORECASE)
    section_end = h1_match.end() + first_h2_match.start() if first_h2_match else len(content)
    summary_scope = content[h1_match.end() : section_end]

    paragraph_match = _PARAGRAPH_RE.search(summary_scope)
    if not paragraph_match:
        return ''

    return _normalize_text(paragraph_match.group(1))


def _extract_key_facts(content: str) -> list[FactItem]:
    for title, section_body in _iter_h2_sections(content):
        if title.lower() != 'key facts':
            continue

        items = []
        for label_raw, value_raw in _KEY_FACT_ITEM_RE.findall(section_body):
            label = _normalize_text(label_raw)
            value = _normalize_text(value_raw)
            if label and value:
                items.append(FactItem(label=label, value=value))
        return items

    return []


def _extract_info_sections(content: str) -> list[InfoSection]:
    result: list[InfoSection] = []
    skip_titles = {'key facts', 'contents', 'text'}

    for title, section_body in _iter_h2_sections(content):
        title_key = title.lower()
        if title_key in skip_titles:
            continue

        paragraph_match = _PARAGRAPH_RE.search(section_body)
        if not paragraph_match:
            continue

        body = _normalize_text(paragraph_match.group(1))
        if body:
            result.append(InfoSection(title=title, body=body))

    return result


def _iter_h2_sections(content: str) -> Iterable[tuple[str, str]]:
    for title_html, section_body in _H2_SECTION_RE.findall(content):
        title = _normalize_text(title_html)
        if title:
            yield title, section_body


def _normalize_text(value: str) -> str:
    without_tags = _TAG_RE.sub(' ', value)
    unescaped = unescape(without_tags)
    return ' '.join(unescaped.split())
