from src.pdf_processor import PageText
from src.lecture_chunker import chunk_pages

def test_chunking_preserves_page_refs():
    pages=[PageText(i, (f"Content from page {i}. "*15), 300, "text") for i in range(1,5)]
    chunks=chunk_pages(pages,max_chars=500,overlap_chars=30)
    assert len(chunks)>1
    refs={p for chunk in chunks for p in chunk.source_pages}
    assert refs == {1,2,3,4}
    assert all(chunk.text for chunk in chunks)

def test_empty_pages_return_no_chunks():
    assert chunk_pages([PageText(1,"",0,"low_text")]) == []
