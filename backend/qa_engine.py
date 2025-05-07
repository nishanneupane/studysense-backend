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
Provide a concise and accurate answer based only on the notes and if the context is not enough add your own knowledge as well.
And while evaluating dont say 'users' answers. speak like you are talking to the user directly.
treat yourself like a professor and they are your student as well as friends.
The answer should be shown with proper spacing and if required proper code snippets. 
"""
        
        # Query Ollama
        response = query_ollama(prompt, temperature=0.5, max_tokens=200)
        return response