"""Direct tests for chunk_service - no conftest needed, no app imports."""

def test_chunk_document_empty():
    from app.services.chunk_service import chunk_document
    assert chunk_document("") == []

def test_chunk_document_short():
    from app.services.chunk_service import chunk_document
    text = "这是一段简短的文本。"
    result = chunk_document(text, chunk_size=500, overlap=50)
    assert result == [text]

def test_chunk_document_splits():
    from app.services.chunk_service import chunk_document
    text = "第一句。第二句。第三句。第四句。第五句。" * 50
    result = chunk_document(text, chunk_size=100, overlap=20)
    assert len(result) > 1

def test_chunk_document_defaults():
    from app.services.chunk_service import chunk_document
    text = "测试文本。" * 30
    result = chunk_document(text)
    assert len(result) >= 1

def test_chunk_metadata_basic():
    from app.services.chunk_service import chunk_metadata
    meta = chunk_metadata(1, ["a", "b", "c"])
    assert len(meta) == 3
    assert meta[0]["knowledge_id"] == 1
    assert meta[0]["chunk_index"] == 0

def test_chunk_metadata_empty():
    from app.services.chunk_service import chunk_metadata
    assert chunk_metadata(1, []) == []

def test_chunk_metadata_index_start():
    from app.services.chunk_service import chunk_metadata
    meta = chunk_metadata(5, ["a", "b"], chunk_index_start=10)
    assert meta[0]["chunk_index"] == 10
    assert meta[1]["chunk_index"] == 11