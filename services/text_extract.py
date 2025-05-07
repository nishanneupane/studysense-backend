from PyPDF2 import PdfReader
from docx import Document
import os

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from TXT, DOCX, or PDF files.
    """
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.docx':
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif ext == '.pdf':
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
            return text
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        raise Exception(f"Failed to extract text from {file_path}: {str(e)}")