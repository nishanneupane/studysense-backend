from data.note_storage import NotesStorage
from services.ollama_api import query_ollama

class QAEngine:
    def __init__(self):
        self.storage = NotesStorage()

    def answer_question(self, question: str, subject: str) -> str:
        """
        Answer a question using notes from the specified subject.
        """
        # Retrieve relevant notes
        collection = self.storage._get_collection(subject)
        results = collection.query(
            query_texts=[question],
            n_results=3  # Top 3 most relevant notes
        )
        
        # Combine notes into context
        context = "\n".join(results["documents"][0]) if results["documents"] else ""
        if not context:
            return "No relevant notes found for this subject."

        # Build prompt for Mistral
        prompt = f"""Using the following notes:
{context}

Answer the question: {question}
Provide a concise and accurate answer based only on the notes."""
        
        # Query Ollama
        response = query_ollama(prompt, temperature=0.5, max_tokens=200)
        return response