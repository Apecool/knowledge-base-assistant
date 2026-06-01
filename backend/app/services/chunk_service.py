"""
Document Chunking Service
Splits knowledge documents into smaller chunks for embedding and retrieval.
- chunk_size: target characters per chunk (default 500)
- overlap: character overlap between consecutive chunks (default 50)
"""
from typing import List


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """
    Split a document into chunks with overlap.

    Strategy:
    1. If text is shorter than chunk_size, return as-is.
    2. Otherwise, split into chunks of `chunk_size` chars
       with `overlap` chars of overlap between chunks.
    3. Each chunk boundary tries to break at a sentence end
       (。！？.!?\n) for cleaner splits.

    Args:
        text: The full document text.
        chunk_size: Max characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    # Track previous start to detect infinite loop
    last_start = -1

    while start < len(text):
        if start == last_start:
            # Safety: forced forward progress
            start += 1
            continue
        last_start = start

        # Determine end position for this chunk
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Try to find a natural break point near the end of chunk
            search_start = max(start, end - 100)
            search_region = text[search_start:end]

            break_positions = []
            for punct in ["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";"]:
                pos = search_region.rfind(punct)
                if pos != -1:
                    break_positions.append(pos + len(punct))

            if break_positions:
                best_pos = max(break_positions)
                end = search_start + best_pos
                # Ensure end is always after start
                if end <= start:
                    end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, accounting for overlap
        start = max(start + 1, end - overlap)

    return chunks


def chunk_metadata(
    knowledge_id: int,
    chunks: List[str],
    chunk_index_start: int = 0,
) -> List[dict]:
    """
    Generate metadata for each chunk.

    Args:
        knowledge_id: The parent knowledge item ID.
        chunks: List of chunk texts.
        chunk_index_start: Starting index for chunk numbering.

    Returns:
        List of metadata dicts with chunk_index and knowledge_id.
    """
    return [
        {
            "knowledge_id": knowledge_id,
            "chunk_index": chunk_index_start + i,
            "chunk_count": len(chunks),
        }
        for i in range(len(chunks))
    ]