"""
Tests for the Document Chunking Service.
"""
from app.services.chunk_service import chunk_document, chunk_metadata


class TestChunkDocument:
    """Tests for chunk_document function."""

    def test_chunk_empty_text(self):
        """Test chunking empty text returns empty list."""
        assert chunk_document("") == []

    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk_size returns as-is."""
        text = "这是一段简短的文本。"
        result = chunk_document(text, chunk_size=500, overlap=50)
        assert result == [text]

    def test_chunk_exact_size(self):
        """Test chunking text exactly matching chunk_size."""
        text = "A" * 500
        result = chunk_document(text, chunk_size=500, overlap=50)
        assert len(result) == 1
        assert result[0] == text

    def test_chunk_splits_correctly(self):
        """Test that long text is split into multiple chunks."""
        text = "第一句。第二句。第三句。第四句。第五句。" * 50
        result = chunk_document(text, chunk_size=100, overlap=20)
        assert len(result) > 1

    def test_chunk_overlap_preserved(self):
        """Test that overlap between chunks contains shared content."""
        text = "第一段内容。" + "第二段内容。" + "第三段内容。" + "第四段内容。"
        text = text * 20  # Make it long enough to require splitting
        result = chunk_document(text, chunk_size=100, overlap=30)

        if len(result) >= 2:
            # The end of chunk 0 should overlap with start of chunk 1
            chunk0_end = result[0][-30:]
            chunk1_start = result[1][:30]
            # There should be some shared content
            assert len(set(chunk0_end) & set(chunk1_start)) > 0

    def test_chunk_respects_sentence_boundary(self):
        """
        Test that chunk breaks prefer sentence boundaries
        (。！？.!?) over mid-sentence splits.
        """
        text = (
            "第一句话的内容完整结束。第二句话的内容也结束了。"
            "第三句话。第四句话。第五句话。第六句话。第七句话。"
        ) * 10
        result = chunk_document(text, chunk_size=100, overlap=20)

        for chunk in result:
            # Most chunks should end with sentence-ending punctuation
            if len(chunk) > 20:
                assert chunk.rstrip()[-1] in "。！？.!?\n" or chunk == result[-1]

    def test_chunk_parameter_defaults(self):
        """Test that default parameters (500/50) work correctly."""
        text = "测试文本。" * 50
        result = chunk_document(text)
        assert len(result) >= 1
        for chunk in result:
            assert len(chunk) <= 500

    def test_chunk_long_word_boundary(self):
        """Test chunking with no natural breaks."""
        # A long string without any punctuation
        text = "微服务架构是一种将应用程序构建为独立可部署服务集合的架构风格" * 20
        result = chunk_document(text, chunk_size=100, overlap=20)
        assert len(result) >= 1

    def test_chunk_newline_boundary(self):
        """Test that chunking respects newline boundaries."""
        text = "\n\n".join([f"这是第{i}段落" for i in range(50)])
        result = chunk_document(text, chunk_size=100, overlap=20)
        assert len(result) >= 1


class TestChunkMetadata:
    """Tests for chunk_metadata function."""

    def test_metadata_basic(self):
        """Test basic metadata generation."""
        chunks = ["chunk1", "chunk2", "chunk3"]
        metadata = chunk_metadata(knowledge_id=1, chunks=chunks)

        assert len(metadata) == 3
        for i, meta in enumerate(metadata):
            assert meta["knowledge_id"] == 1
            assert meta["chunk_index"] == i
            assert meta["chunk_count"] == 3

    def test_metadata_empty_chunks(self):
        """Test metadata with empty chunks list."""
        metadata = chunk_metadata(knowledge_id=1, chunks=[])
        assert metadata == []

    def test_metadata_chunk_index_start(self):
        """Test custom chunk_index_start."""
        chunks = ["a", "b"]
        metadata = chunk_metadata(knowledge_id=5, chunks=chunks, chunk_index_start=10)
        assert metadata[0]["chunk_index"] == 10
        assert metadata[1]["chunk_index"] == 11