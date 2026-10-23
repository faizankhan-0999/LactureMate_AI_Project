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

def test_failure_surfaces_actionable_service_diagnostic():
    class BadService:
        def generate(self, prompt):
            raise RuntimeError("Gemini rejected request (diagnostic: quota, HTTP 429)")
    with pytest.raises(RuntimeError, match="quota, HTTP 429"):
        analyze_chunks(BadService(), [LectureChunk(1, "short content", [1, 2])])


def test_size_failure_retries_with_smaller_sections():
    class SizeLimitedService:
        def __init__(self): self.calls = 0
        def generate(self, prompt):
            self.calls += 1
            if len(prompt) > 5000:
                raise RuntimeError("HTTP 400 invalid argument: request too large")
            return "supported summary"
    service = SizeLimitedService()
    chunk = LectureChunk(1, ("Concept paragraph. " * 400), list(range(1, 9)))
    output = analyze_chunks(service, [chunk])
    assert "supported summary" in output
    assert service.calls >= 3
