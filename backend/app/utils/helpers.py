"""
Utility Helper Functions
"""
import re
from typing import List


def format_tags(tags: List[str]) -> str:
    """Convert a list of tags to a comma-separated string."""
    return ",".join(tags)


def parse_tags(tag_string: str) -> List[str]:
    """Parse a comma-separated tag string into a list of trimmed tags."""
    if not tag_string:
        return []
    return [tag.strip() for tag in tag_string.split(",") if tag.strip()]


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')