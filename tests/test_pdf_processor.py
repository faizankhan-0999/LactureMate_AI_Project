from io import BytesIO
import pytest
from pypdf import PdfWriter
from src.pdf_processor import extract_pdf

def make_pdf(pages):
    writer=PdfWriter()
    for text in pages:
        page=writer.add_blank_page(width=300,height=300)
        # Add text using a minimal PDF content stream for extraction.
        from pypdf.generic import DecodedStreamObject, NameObject
        stream=DecodedStreamObject(); stream.set_data(("BT /F1 12 Tf 20 200 Td ("+text.replace('(','').replace(')','')+") Tj ET").encode())
        page[NameObject('/Contents')]=writer._add_object(stream)
    out=BytesIO(); writer.write(out); return out.getvalue()

def test_invalid_pdf():
    with pytest.raises(ValueError): extract_pdf(b"not a pdf")

def test_empty_pdf_bytes():
    with pytest.raises(ValueError): extract_pdf(b"")

def test_page_count_and_reference():
    # Use a generated PDF; extraction failure on a synthetic content stream is still a valid page record.
    data=make_pdf(["A sufficiently long lecture sentence to be extracted.","Another sufficiently long page for testing page numbers."])
    result=extract_pdf(data,"test.pdf", low_text_threshold=1)
    assert result.total_pages == 2
    assert [p.page_number for p in result.pages] == [1,2]
    assert result.coverage["total_pages"] == 2
