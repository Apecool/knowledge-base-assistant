"""
Document Parser — Markdown-aware document parser that preserves
table structure, heading hierarchy, and code blocks during chunking.
"""
import re
from typing import List, Dict


class DocumentParser:
    """
    Parses documents with awareness of:
    - Markdown headings (#, ##, etc.) — used as section boundaries
    - Tables (| ... |) — kept as atomic units
    - Code blocks (``` ... ```) — kept as atomic units
    - Paragraphs (separated by blank lines)
    """

    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    TABLE_PATTERN = re.compile(r'^\|.+\|\s*$', re.MULTILINE)
    TABLE_SEPARATOR = re.compile(r'^\|[-:| ]+\|$')
    CODE_BLOCK_PATTERN = re.compile(r'```[\w]*\n.*?```', re.DOTALL)
    EMPTY_LINE_PATTERN = re.compile(r'\n\s*\n')

    def parse_structure(self, text: str) -> Dict:
        """
        Parse document structure into sections with metadata.

        Returns:
            Dict with keys:
                - sections: List of {heading, level, content, tables}
                - tables: List of extracted table strings
                - code_blocks: List of extracted code strings
        """
        # Extract code blocks first (protect them from other parsing)
        code_blocks = []
        def _protect_code(match):
            code_blocks.append(match.group(0))
            return f"\n<!-- CODEBLOCK_{len(code_blocks)-1} -->\n"

        protected = self.CODE_BLOCK_PATTERN.sub(_protect_code, text)

        # Extract tables
        tables = []
        def _protect_table(match):
            # Collect consecutive table rows
            start = match.start()
            lines = protected[:start].split('\n')
            table_start = max(0, len(lines) - 1)
            table_lines = []
            # Walk backward to find table start
            i = table_start
            while i >= 0 and (lines[i].strip().startswith('|') or
                              self.TABLE_SEPARATOR.match(lines[i].strip())):
                table_lines.insert(0, lines[i])
                i -= 1
            # Walk forward from current match
            rest = protected[start:]
            rest_lines = rest.split('\n')
            j = 0
            while j < len(rest_lines) and (rest_lines[j].strip().startswith('|') or
                                            self.TABLE_SEPARATOR.match(rest_lines[j].strip())):
                if j > 0:
                    table_lines.append(rest_lines[j])
                j += 1

            table_str = '\n'.join(table_lines)
            tables.append(table_str)
            return f"\n<!-- TABLE_{len(tables)-1} -->\n"

        protected = self.TABLE_PATTERN.sub(_protect_table, protected)

        # Split into sections by headings
        sections = []
        lines = protected.split('\n')
        current_heading = "Introduction"
        current_level = 1
        current_content = []

        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                # Save previous section
                if current_content:
                    sections.append({
                        "heading": current_heading,
                        "level": current_level,
                        "content": '\n'.join(current_content).strip(),
                    })
                current_level = len(heading_match.group(1))
                current_heading = heading_match.group(2)
                current_content = []
            else:
                current_content.append(line)

        # Last section
        if current_content:
            sections.append({
                "heading": current_heading,
                "level": current_level,
                "content": '\n'.join(current_content).strip(),
            })

        # Restore protected blocks
        for i, cb in enumerate(code_blocks):
            for section in sections:
                section["content"] = section["content"].replace(
                    f"<!-- CODEBLOCK_{i} -->", cb
                )

        for i, tbl in enumerate(tables):
            for section in sections:
                section["content"] = section["content"].replace(
                    f"<!-- TABLE_{i} -->", tbl
                )

        return {
            "sections": sections,
            "tables": tables,
            "code_blocks": code_blocks,
        }

    def to_chunks(self, text: str, chunk_size: int = 500,
                  chunk_overlap: int = 50) -> List[Dict]:
        """
        Convert document to chunks, preserving structure.

        Returns list of dicts:
            { "text": str, "heading": str, "level": int,
              "contains_table": bool, "contains_code": bool }
        """
        structure = self.parse_structure(text)
        chunks = []

        for section in structure["sections"]:
            section_text = section["content"]
            if not section_text:
                continue

            # Check for tables/code that should stay intact
            has_table = "|" in section_text and ("--|" in section_text or "---" in section_text)
            has_code = "```" in section_text

            if len(section_text) <= chunk_size:
                chunks.append({
                    "text": section_text,
                    "heading": section["heading"],
                    "level": section["level"],
                    "contains_table": has_table,
                    "contains_code": has_code,
                })
            else:
                # Split this section further
                sub_chunks = self._split_paragraphs(
                    section_text, chunk_size, chunk_overlap
                )
                for sc in sub_chunks:
                    chunks.append({
                        "text": sc,
                        "heading": section["heading"],
                        "level": section["level"],
                        "contains_table": has_table,
                        "contains_code": has_code,
                    })

        return chunks

    def _split_paragraphs(self, text: str, chunk_size: int,
                          chunk_overlap: int) -> List[str]:
        """Split text by paragraph boundaries, then by size."""
        # Try splitting by double newlines first
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 1 <= chunk_size:
                current = (current + "\n\n" + para).strip()
            else:
                if current:
                    chunks.append(current)
                # If the paragraph itself is too long, split it
                if len(para) > chunk_size:
                    sub_chunks = self._split_by_size(para, chunk_size, chunk_overlap)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = para

        if current:
            chunks.append(current)

        return chunks

    def _split_by_size(self, text: str, chunk_size: int,
                       chunk_overlap: int) -> List[str]:
        """Split text by character size with overlap."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        last_start = -1
        while start < len(text):
            if start == last_start:
                start += 1
            last_start = start
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            next_start = end - chunk_overlap
            start = next_start if next_start > start else start + 1
        return chunks


# Convenience function
def chunk_with_structure(text: str, chunk_size: int = 500,
                         chunk_overlap: int = 50) -> List[Dict]:
    """One-call function to get structured chunks."""
    parser = DocumentParser()
    return parser.to_chunks(text, chunk_size, chunk_overlap)