from data.note_storage import NotesStorage
from services.ollama_api import query_ollama
import json

class QuestionGenerator:
    def __init__(self):
        self.storage = NotesStorage()

    def generate_questions(self, subject: str, num_questions: int = 2) -> list[dict]:
        """
        Generate open-ended, long-answer practice questions from notes in the specified subject.
        Returns list of dicts with question and type ('long-answer').
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

Generate {num_questions} open-ended, long-answer practice questions that require detailed explanations or essay-style responses. For each, provide:
1. The question text.
2. The type ('long-answer').

Format the output as a JSON list of objects. Example:
[
    {{"question": "Explain the significance of the Pythagorean theorem in geometry.", "type": "long-answer"}}
]"""
        
        # Query Ollama
        response = query_ollama(prompt, temperature=0.7, max_tokens=1000)
        
        # Parse JSON response
        try:
            questions = json.loads(response)
            return questions
        except json.JSONDecodeError:
            return [{"error": "Failed to generate valid questions"}]