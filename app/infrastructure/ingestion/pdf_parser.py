import fitz
from app.domain.models.source_document import SourceDocument

class ParserError(Exception):
    pass

class PdfParser:
    def parse(self, file_bytes: bytes, filename: str = "document.pdf") -> SourceDocument:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
                
            if not text.strip():
                raise ParserError("No extractable text found in PDF.")
                
            return SourceDocument(
                document_id="doc_" + filename,
                filename=filename,
                content_type="pdf",
                raw_text=text,
                storage_path=""
            )
        except ParserError:
            raise
        except Exception as e:
            raise ParserError(f"Failed to parse PDF: {str(e)}")
