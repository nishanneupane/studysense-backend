from data.note_storage import NotesStorage
from services.ollama_api import query_ollama
import json 
class AnswerEvaluator:
    def __init__(self):
        self.storage = NotesStorage()

    def evaluate_answer(self, question: str, user_answer: str, subject: str) -> dict:
        """
        Evaluate a user's long-answer response against notes.
        Returns dict with score (0-100) and feedback.
        """
        # Retrieve relevant notes
        collection = self.storage._get_collection(subject)
        results = collection.query(
            query_texts=[question],
            n_results=3
        )
        context = "\n".join(results["documents"][0]) if results["documents"] else ""
        if not context:
            return {"score": 0, "feedback": "No relevant notes found for this subject."}

        # Build prompt for Mistral
        prompt = f"""Using the following notes:
{context}

Evaluate the user's answer to the question: {question}
User's answer: {user_answer}

Provide:
1. A score (0-100) based on accuracy, completeness, and relevance.
2. Brief feedback explaining the score.

Format the output as a JSON object:
{{"score": <int>, "feedback": "<string>"}}"""
        
        # Query Ollama
        response = query_ollama(prompt, temperature=0.5, max_tokens=500)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {"score": 0, "feedback": "Error: Failed to evaluate answer."}