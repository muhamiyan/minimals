"""Shared HTML sanitizer for stored rich-text bodies."""
from __future__ import annotations

import html
import re

import nh3

BODY_TAGS = {
    "a", "blockquote", "br", "b", "code", "del", "em", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input",
    "label", "li", "mark", "ol", "p", "pre", "s", "source", "span", "strike",
    "strong", "sub", "sup", "table", "tbody", "td", "th", "thead", "tr", "u",
    "ul", "video",
}

BODY_ATTRIBUTES = {
    "*": {"class", "style", "title"},
    "a": {"href", "target"},
    "img": {"src", "alt", "width", "height"},
    "input": {"type", "checked", "disabled"},
    "li": {"value"},
    "ol": {"start"},
    "source": {"src", "type"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
    "video": {"src", "controls", "width", "height", "poster", "loop", "muted"},
    "iframe": {
        "src", "width", "height", "allow", "allowfullscreen",
        "loading", "frameborder", "title",
    },
}

BODY_URL_SCHEMES = {"http", "https", "mailto", "tel"}
BODY_CONTENT_TAGS = {"script", "style", "template", "noscript", "textarea"}


def clean_body(value: str) -> str:
    """Strip unsafe HTML from a rich-text body (stored-XSS defense)."""
    return nh3.clean(
        value,
        tags=BODY_TAGS,
        attributes=BODY_ATTRIBUTES,
        url_schemes=BODY_URL_SCHEMES,
        clean_content_tags=BODY_CONTENT_TAGS,
    )


EXCERPT_LENGTH = 160


def make_excerpt(body: str) -> str:
    text = re.sub(r"<[^>]+>", " ", body)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= EXCERPT_LENGTH:
        return text
    return text[:EXCERPT_LENGTH].rstrip() + "…"


__all__ = ["clean_body", "make_excerpt"]
