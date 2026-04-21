from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
from typing import Iterable

from flask import current_app

from app.models import Book

_TAG_RE = re.compile(r'<[^>]+>')
_H2_SECTION_RE = re.compile(r'<h2[^>]*>(.*?)</h2>(.*?)(?=<h2[^>]*>|</main>|</body>)', re.IGNORECASE | re.DOTALL)
_PARAGRAPH_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)
_CONTENTS_H2_RE = re.compile(r'<h2[^>]*>\s*Contents\s*</h2>', re.IGNORECASE)
_TEXT_H2_RE = re.compile(r'<h2[^>]*>\s*Text\s*</h2>', re.IGNORECASE)
_UL_RE = re.compile(r'<ul[^>]*>(.*?)</ul>', re.IGNORECASE | re.DOTALL)
_A_RE = re.compile(r'<a[^>]*href=["\']#([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
_SECTION_RE = re.compile(r'<section[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</section>', re.IGNORECASE | re.DOTALL)
_H3_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)
_H3_WITH_ID_RE = re.compile(
    r'<h3[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</h3>(.*?)(?=<h3[^>]*id=|</section>|</main>|</body>)',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(slots=True)
class InfoSection:
    title: str
    body: str


@dataclass(slots=True)
class BookTextPreview:
    summary: str
    sections: list[InfoSection]


@dataclass(slots=True)
class ReadContentsItem:
    target_id: str
    title: str


@dataclass(slots=True)
class ReadTextSection:
    section_id: str
    title: str
    paragraphs: list[str]


@dataclass(slots=True)
class BookReadContent:
    contents: list[ReadContentsItem]
    text_sections: list[ReadTextSection]


def load_book_text_source(book_id: int) -> str | None:
    source_path = _resolve_source_path(book_id)
    if source_path is None:
        return None
    return source_path.read_text(encoding='utf-8')


def save_book_text_source(book_id: int, content: str) -> Path:
    target_dir = _resolve_book_text_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    source_path = target_dir / f'book-{book_id}.html'
    normalized_content = content.strip()
    source_path.write_text(f'{normalized_content}\n', encoding='utf-8')
    return source_path


def build_book_text_template(book: Book) -> str:
    return """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
</head>
<body>
    <main>
        <section>
            <h2>Description</h2>
            <p>Write a short summary for readers here.</p>
        </section>

        <section>
            <h2>Plot &amp; Themes</h2>
            <p>Describe the central conflicts, ideas, and themes of the book.</p>
        </section>

        <section>
            <h2>Literary Significance</h2>
            <p>Explain why this book matters, how it is usually interpreted, or what makes it memorable.</p>
        </section>

        <section>
            <h2 id="contents">Contents</h2>
            <ul>
                <li><a href="#chapter-1">Chapter 1</a></li>
            </ul>
        </section>

        <section>
            <h2>Text</h2>
            <section id="chapter-1">
                <h3>Chapter 1</h3>
                <p>Paste the opening section of the reading text here.</p>
                <p><a href="#contents">Back to contents</a></p>
            </section>
        </section>
    </main>
</body>
</html>
"""


def load_book_text_preview(book_id: int) -> BookTextPreview | None:
    source_path = _resolve_source_path(book_id)
    if source_path is None:
        return None

    content = source_path.read_text(encoding='utf-8')
    summary = _extract_summary(content)
    sections = _extract_info_sections(content)

    if not summary and not sections:
        return None

    return BookTextPreview(summary=summary, sections=sections)


def load_book_read_content(book_id: int) -> BookReadContent | None:
    source_path = _resolve_source_path(book_id)
    if source_path is None:
        return None

    content = source_path.read_text(encoding='utf-8')
    contents = _extract_contents_items(content)
    text_sections = _extract_text_sections(content)
    if not contents and not text_sections:
        return None
    return BookReadContent(contents=contents, text_sections=text_sections)


def _extract_summary(content: str) -> str:
    h1_match = re.search(r'<h1[^>]*>.*?</h1>', content, flags=re.IGNORECASE | re.DOTALL)
    if h1_match:
        first_h2_match = re.search(r'<h2[^>]*>', content[h1_match.end() :], flags=re.IGNORECASE)
        section_end = h1_match.end() + first_h2_match.start() if first_h2_match else len(content)
        summary_scope = content[h1_match.end() : section_end]

        paragraph_match = _PARAGRAPH_RE.search(summary_scope)
        if paragraph_match:
            summary = _normalize_text(paragraph_match.group(1))
            if summary:
                return summary

    for title, section_body in _iter_h2_sections(content):
        if title.lower() != 'description':
            continue
        paragraph_match = _PARAGRAPH_RE.search(section_body)
        if not paragraph_match:
            continue
        summary = _normalize_text(paragraph_match.group(1))
        if summary:
            return summary

    return ''


def _extract_contents_items(content: str) -> list[ReadContentsItem]:
    match = _CONTENTS_H2_RE.search(content)
    if not match:
        return []
    ul_match = _UL_RE.search(content, pos=match.end())
    if not ul_match:
        return []

    items: list[ReadContentsItem] = []
    for target_id, raw_title in _A_RE.findall(ul_match.group(1)):
        title = _normalize_text(raw_title)
        if not title:
            continue
        items.append(ReadContentsItem(target_id=target_id.strip(), title=title))
    return items


def _extract_text_sections(content: str) -> list[ReadTextSection]:
    match = _TEXT_H2_RE.search(content)
    if not match:
        return []
    text_scope = content[match.end() :]
    wrapped_sections = _extract_wrapped_text_sections(text_scope)
    if wrapped_sections:
        return wrapped_sections
    return _extract_heading_text_sections(text_scope)


def _extract_wrapped_text_sections(text_scope: str) -> list[ReadTextSection]:
    sections: list[ReadTextSection] = []
    for section_id, raw_section_body in _SECTION_RE.findall(text_scope):
        title_match = _H3_RE.search(raw_section_body)
        title = _normalize_text(title_match.group(1)) if title_match else ''
        paragraphs = _extract_text_paragraphs(raw_section_body)
        if not title and not paragraphs:
            continue
        sections.append(
            ReadTextSection(
                section_id=section_id.strip(),
                title=title,
                paragraphs=paragraphs,
            )
        )
    return sections


def _extract_heading_text_sections(text_scope: str) -> list[ReadTextSection]:
    sections: list[ReadTextSection] = []
    for section_id, raw_title, raw_section_body in _H3_WITH_ID_RE.findall(text_scope):
        title = _normalize_text(raw_title)
        paragraphs = _extract_text_paragraphs(raw_section_body)
        if not title and not paragraphs:
            continue
        sections.append(
            ReadTextSection(
                section_id=section_id.strip(),
                title=title,
                paragraphs=paragraphs,
            )
        )
    return sections


def _extract_text_paragraphs(section_body: str) -> list[str]:
    paragraphs: list[str] = []
    for raw_paragraph in _PARAGRAPH_RE.findall(section_body):
        paragraph = _normalize_text(raw_paragraph)
        if not paragraph or paragraph.lower() == 'back to contents':
            continue
        paragraphs.append(paragraph)
    return paragraphs


def _extract_info_sections(content: str) -> list[InfoSection]:
    result: list[InfoSection] = []
    skip_titles = {'description', 'key facts', 'contents', 'text'}

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


def _resolve_source_path(book_id: int) -> Path | None:
    source_path = _resolve_book_text_dir() / f'book-{book_id}.html'
    if not source_path.exists():
        return None
    return source_path


def _resolve_book_text_dir() -> Path:
    configured_dir = current_app.config.get('BOOK_TEXT_DIR')
    if configured_dir:
        return Path(configured_dir)

    static_folder = current_app.static_folder
    if not static_folder:
        raise RuntimeError('Static folder is not configured for book text storage.')

    return Path(static_folder) / 'book_text'
