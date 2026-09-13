"""
Recursive sliding-window text chunker for Sovereign RAG pipeline.
Splits text along semantic boundaries (paragraphs, sentences, words)
with configurable overlap and comprehensive metadata tracking.
"""

from typing import Any, Dict, List, Optional
from core.logging import logger


class TextChunk:
    """Represents a text chunk with associated document metadata."""
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "metadata": self.metadata}


class TextChunker:
    """Splits document text into overlapping chunks while preserving context."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, base_metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        Chunk text into overlapping windows respecting paragraph and sentence boundaries.
        """
        if not text or not text.strip():
            return []

        base_meta = base_metadata.copy() if base_metadata else {}
        clean_text = text.strip()

        # If text is smaller than chunk size, return single chunk
        if len(clean_text) <= self.chunk_size:
            meta = base_meta.copy()
            meta.update({"chunk_index": 0, "total_chunks": 1, "char_length": len(clean_text)})
            return [TextChunk(text=clean_text, metadata=meta)]

        chunks = []
        start = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # If not at the very end of text, try to find a natural break point
            if end < text_len:
                # Look backwards for paragraph break, then period/sentence break, then space
                slice_to_search = clean_text[start:end]
                break_point = -1

                for sep in ["\n\n", "\n", ". ", "; ", ", ", " "]:
                    pos = slice_to_search.rfind(sep)
                    if pos != -1 and pos > len(slice_to_search) * 0.5:
                        break_point = pos + len(sep)
                        break

                if break_point != -1:
                    end = start + break_point

            chunk_str = clean_text[start:end].strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Advance window with overlap
            start = end - self.chunk_overlap
            if start >= text_len - self.chunk_overlap or end >= text_len:
                break

        # Attach metadata to each chunk
        total = len(chunks)
        result = []
        for idx, c in enumerate(chunks):
            meta = base_meta.copy()
            meta.update({
                "chunk_index": idx,
                "total_chunks": total,
                "char_length": len(c)
            })
            result.append(TextChunk(text=c, metadata=meta))

        logger.info(f"Chunked document into {total} chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")
        return result


text_chunker = TextChunker()
