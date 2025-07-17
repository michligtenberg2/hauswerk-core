import re


def slugify(text: str) -> str:
    """Generate a lowercase slug with hyphens from the given text."""
    base = "".join(c for c in text.lower() if c.isalnum() or c in " -_")
    base = re.sub(r"[^a-z0-9_-]", "", base.strip())
    slug = "-".join(base.split())
    return slug[:20] or "plugin"
