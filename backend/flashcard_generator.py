from data.note_storage import NotesStorage
from services.ollama_api import query_ollama
import json

class FlashcardGenerator:
    def __init__(self):
        self.storage = NotesStorage()

    def generate_flashcards(self, subject: str, num_flashcards: int = 3) -> list[dict]:
        """
        Generate flashcards from notes in the specified subject.
        Returns list of dicts with question and answer.
        """
        # Retrieve notes
        collection = self.storage._get_collection(subject)
        results = collection.get()
        context = "\n".join(results["documents"]) if results["documents"] else ""
        if not context:
            return []

        # Build prompt for Mistral
        prompt = f"""Using the following notes:
{context}

Generate {num_flashcards} flashcards for quick review. Each flashcard should have:
1. A concise question.
2. A short, accurate answer (1-2 sentences).

Format the output as a JSON list of objects:
[
    {{"question": "<question>", "answer": "<answer>"}}
]"""
        
        # Query Ollama
        response = query_ollama(prompt, temperature=0.7, max_tokens=1000)
        
        # Parse JSON response
        try:
            flashcards = json.loads(response)
            return flashcards
        except json.JSONDecodeError:
            return [{"error": "Failed to generate valid flashcards"}]