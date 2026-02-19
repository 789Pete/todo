from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dict by key (coerces key to string)."""
    return dictionary.get(str(key))


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
