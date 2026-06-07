import re

from django import template
from django.utils.html import escape, mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dict by key (coerces key to string)."""
    return dictionary.get(str(key))


@register.filter
def highlight(value, query):
    """Wrap matching substrings in <mark> tags. HTML-escapes output to prevent XSS.

    Matches against the original (unescaped) value so the query can never land
    inside an HTML entity produced by escaping (e.g. searching "amp" in "AT&T").
    """
    query = (query or "").strip()
    if not query:
        return value
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    pieces = []
    last = 0
    for match in pattern.finditer(value):
        pieces.append(escape(value[last : match.start()]))
        pieces.append(f"<mark>{escape(match.group())}</mark>")
        last = match.end()
    pieces.append(escape(value[last:]))
    return mark_safe("".join(pieces))


@register.filter
def badge_text_color(hex_color):
    """Return '#000000' or '#ffffff' for WCAG AA contrast on hex_color background."""
    hex_color = str(hex_color).lstrip("#")
    if len(hex_color) != 6:
        return "#ffffff"
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    def to_linear(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * to_linear(r) + 0.7152 * to_linear(g) + 0.0722 * to_linear(b)
    return "#000000" if lum > 0.179 else "#ffffff"
