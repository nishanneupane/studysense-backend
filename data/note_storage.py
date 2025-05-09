import os
import uuid
from datetime import datetime
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from backend.models import Note
from services.text_extract import extract_text_from_file

class NotesStorage:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _normalize_subject(self, subject: str) -> str:
        """
        Normalize subject name to a consistent format for collection names.
        """
        return subject.lower().replace(' ', '_')

    def _get_collection(self, subject: str):
        """
        Get or create a Chroma DB collection for notes in the subject.
        Ensures no duplicate collections are created for equivalent subject names.
        """
        normalized_subject = self._normalize_subject(subject)
        collection_name = f"notes_{normalized_subject}"
        
        # Check if a collection with the same normalized name already exists
        existing_collections = self.client.list_collections()
        for collection in existing_collections:
            if collection.name == collection_name:
                return collection
        
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            raise Exception(f"Failed to access collection for {subject}: {str(e)}")

    def create_subject(self, subject: str) -> None:
        """
        Create a new subject by initializing an empty collection in Chroma DB.
        Raises ValueError if the subject already exists.
        """
        normalized_subject = self._normalize_subject(subject)
        collection_name = f"notes_{normalized_subject}"
        
        # Check for existing collections to prevent duplicates
        existing_collections = self.client.list_collections()
        for collection in existing_collections:
            existing_subject = collection.name.replace("notes_", "")
            if existing_subject == normalized_subject:
                raise ValueError(f"Subject '{subject}' already exists as '{existing_subject.replace('_', ' ').title()}'")
        
        try:
            # Create an empty collection for the subject
            self.client.create_collection(name=collection_name)
        except Exception as e:
            raise Exception(f"Failed to create subject '{subject}': {str(e)}")

    def save_note_from_file(self, file_path: str, subject: str, file_name: str) -> Note:
        """
        Save a note extracted from a file to the Chroma DB.
        Validates that the subject doesn't conflict with existing subjects.
        """
        try:
            # Normalize subject to check for conflicts
            normalized_subject = self._normalize_subject(subject)
            existing_collections = self.client.list_collections()
            for collection in existing_collections:
                existing_subject = collection.name.replace("notes_", "")
                if existing_subject == normalized_subject:
                    # Allow saving if the subject matches exactly after normalization
                    if collection.name == f"notes_{normalized_subject}":
                        break
                    raise Exception(f"Subject '{subject}' conflicts with existing subject '{existing_subject.replace('_', ' ').title()}'")

            text = extract_text_from_file(file_path)
            embedding = self.embedding_model.encode(text).tolist()
            note_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            collection = self._get_collection(subject)
            collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[{"subject": subject, "file_name": file_name, "created_at": created_at.isoformat()}],
                ids=[note_id]
            )
            return Note(id=note_id, subject=subject, content=text, created_at=created_at)
        except Exception as e:
            raise Exception(f"Failed to save note from {file_name}: {str(e)}")

    def load_notes_by_subject(self, subject: str) -> List[Note]:
        """
        Load all notes for a given subject from Chroma DB.
        """
        try:
            collection = self._get_collection(subject)
            results = collection.get(include=["documents", "metadatas"])
            notes = []
            for id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                notes.append(
                    Note(
                        id=id,
                        subject=meta["subject"],
                        content=doc,
                        created_at=datetime.fromisoformat(meta["created_at"])
                    )
                )
            return notes
        except Exception as e:
            raise Exception(f"Failed to load notes for {subject}: {str(e)}")

    def list_subjects(self) -> List[str]:
        """
        List all unique subjects in the Chroma DB.
        """
        try:
            collections = self.client.list_collections()
            subjects = list(set(c.name.replace("notes_", "").replace("_", " ").title() for c in collections))
            return sorted(subjects)
        except Exception as e:
            raise Exception(f"Failed to list subjects: {str(e)}")

    def delete_subject(self, subject: str) -> bool:
        """
        Delete the entire subject collection from Chroma DB.
        """
        try:
            collection_name = f"notes_{self._normalize_subject(subject)}"
            self.client.delete_collection(name=collection_name)
            return True
        except Exception:
            # Collection may not exist
            return True