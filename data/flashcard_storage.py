import uuid
from datetime import datetime
import chromadb
from typing import List, Dict

class FlashcardStorage:
    def __init__(self, db_path="./chroma_db_flashcards"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)

    def _get_collection(self, subject: str):
        """
        Get or create a Chroma DB collection for flashcards in the subject.
        """
        collection_name = f"flashcards_{subject.lower().replace(' ', '_')}"
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            raise Exception(f"Failed to access collection for {subject}: {str(e)}")

    def save_flashcards(self, subject: str, flashcards: List[Dict[str, str]]) -> List[Dict]:
        """
        Save flashcards to the subject-specific Chroma DB collection.
        """
        collection = self._get_collection(subject)
        saved_flashcards = []
        for flashcard in flashcards:
            flashcard_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            try:
                collection.add(
                    documents=[flashcard["question"]],
                    metadatas=[{
                        "subject": subject,
                        "question": flashcard["question"],
                        "answer": flashcard["answer"],
                        "created_at": created_at
                    }],
                    ids=[flashcard_id]
                )
                saved_flashcards.append({
                    "id": flashcard_id,
                    "subject": subject,
                    "question": flashcard["question"],
                    "answer": flashcard["answer"],
                    "created_at": created_at
                })
            except Exception as e:
                raise Exception(f"Failed to save flashcard for {subject}: {str(e)}")
        return saved_flashcards

    def get_flashcards(self, subject: str) -> List[Dict]:
        """
        Retrieve all flashcards for a subject.
        """
        try:
            collection = self._get_collection(subject)
            results = collection.get(include=["metadatas"])
            return [
                {
                    "id": id,
                    "subject": meta["subject"],
                    "question": meta["question"],
                    "answer": meta["answer"],
                    "created_at": meta["created_at"]
                }
                for id, meta in zip(results["ids"], results["metadatas"])
            ]
        except Exception as e:
            raise Exception(f"Failed to retrieve flashcards for {subject}: {str(e)}")

    def delete_flashcard(self, subject: str, flashcard_id: str) -> bool:
        """
        Delete a flashcard by ID from the subject-specific collection.
        """
        try:
            collection = self._get_collection(subject)
            # Check if ID exists
            results = collection.get(ids=[flashcard_id], include=["metadatas"])
            if not results["ids"]:
                return False
            collection.delete(ids=[flashcard_id])
            # Verify deletion
            results = collection.get(ids=[flashcard_id])
            return len(results["ids"]) == 0
        except Exception as e:
            raise Exception(f"Failed to delete flashcard {flashcard_id} for {subject}: {str(e)}")

    def delete_subject(self, subject: str) -> bool:
        """
        Delete the entire subject collection from Chroma DB.
        """
        try:
            collection_name = f"flashcards_{subject.lower().replace(' ', '_')}"
            self.client.delete_collection(name=collection_name)
            return True
        except Exception:
            # Collection may not exist
            return True