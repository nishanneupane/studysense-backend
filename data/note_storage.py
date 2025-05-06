import os
import uuid
from datetime import datetime
from backend.models import NoteSection
import chromadb
from sentence_transformers import SentenceTransformer
from docx import Document
from PyPDF2 import PdfReader

class NotesStorage:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def _get_collection(self, subject: str):
        """
        Get or create a Chroma DB collection for the subject.
        """
        collection_name = subject.lower().replace(" ", "_")
        return self.client.get_or_create_collection(name=collection_name)

    def save_note_from_file(self, file_path: str, subject: str, file_name: str = "Unknown") -> NoteSection:
        """
        Extract text from uploaded file (txt, docx, pdf) and save to subject-specific Chroma DB collection.
        """
        # Extract text based on file extension
        content = ""
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            content = "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            raise ValueError("Unsupported file format. Use txt, docx, or pdf.")

        # Create NoteSection
        note = NoteSection(subject=subject, content=content.strip())

        # Generate embedding and save to subject-specific collection
        collection = self._get_collection(subject)
        note_id = str(uuid.uuid4())
        embedding = self.embedding_model.encode(note.content).tolist()
        collection.add(
            documents=[note.content],
            metadatas=[{
                "subject": note.subject,
                "created_at": note.created_at.isoformat(),
                "file_name": file_name
            }],
            ids=[note_id]
        )
        return note

    def load_notes_by_subject(self, subject: str) -> list[NoteSection]:
        """
        Load notes from the subject-specific Chroma DB collection.
        """
        collection = self._get_collection(subject)
        results = collection.get()
        notes = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            notes.append(NoteSection(
                subject=meta["subject"],
                content=doc,
                created_at=datetime.fromisoformat(meta["created_at"])
            ))
        return notes

    def list_subjects(self) -> list[str]:
        """
        List all subjects (collections) in Chroma DB.
        """
        collections = self.client.list_collections()
        return sorted([coll.name.replace("_", " ").title() for coll in collections])