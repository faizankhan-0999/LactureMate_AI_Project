import pytest
from src.source_analyzer import analyze_chunks
from src.lecture_chunker import LectureChunk

class Service:
    def __init__(self, fail=False): self.fail=fail; self.calls=[]
    def generate(self,prompt):
        self.calls.append(prompt)
        if self.fail: raise RuntimeError("mock failure")
        return "summary of supported concepts"

def test_every_chunk_is_analyzed_with_page_refs():
    chunks=[LectureChunk(1,"content A",[1,2]),LectureChunk(2,"content B",[3])]
    service=Service(); out=analyze_chunks(service,chunks)
    assert len(service.calls)==2 and "PAGES 1, 2" in out and "PAGES 3" in out

def test_failed_chunk_is_not_silently_skipped():
    with pytest.raises(RuntimeError,match="incomplete"):
        analyze_chunks(Service(fail=True),[LectureChunk(1,"content",[4])])
