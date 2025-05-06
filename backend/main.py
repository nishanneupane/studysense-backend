from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from data.note_storage import NotesStorage
from backend.qa_engine import QAEngine
from backend.question_generator import QuestionGenerator
from backend.answer_evaluator import AnswerEvaluator
from backend.flashcard_generator import FlashcardGenerator
import os

app = FastAPI(title="StudySense API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
storage = NotesStorage()
qa_engine = QAEngine()
question_generator = QuestionGenerator()
answer_evaluator = AnswerEvaluator()
flashcard_generator = FlashcardGenerator()

# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    subject: str

class PracticeQuestionRequest(BaseModel):
    subject: str
    num_questions: int

class AnswerEvaluationRequest(BaseModel):
    question: str
    user_answer: str
    subject: str

class FlashcardRequest(BaseModel):
    subject: str
    num_flashcards: int

class NoteResponse(BaseModel):
    subject: str
    file_name: str
    created_at: str

# Routes
@app.get("/subjects", response_model=List[str])
async def get_subjects():
    return storage.list_subjects()

@app.get("/notes/{subject}", response_model=List[NoteResponse])
async def get_notes(subject: str):
    notes = storage.load_notes_by_subject(subject)
    collection = storage._get_collection(subject)
    results = collection.get(include=["metadatas"])
    file_names = [meta.get("file_name", "Unknown") for meta in results["metadatas"]]
    return [
        {"subject": note.subject, "file_name": file_names[i], "created_at": note.created_at.isoformat()}
        for i, note in enumerate(notes)
    ]

@app.post("/upload")
async def upload_note(subject: str, files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not file.filename.endswith((".txt", ".docx", ".pdf")):
            raise HTTPException(status_code=400, detail=f"Unsupported file format for {file.filename}. Use txt, docx, or pdf.")
        
        file_path = f"temp_{file.filename}"
        try:
            with open(file_path, "wb") as f:
                f.write(await file.read())
            note = storage.save_note_from_file(file_path, subject, file.filename)
            results.append({
                "subject": note.subject,
                "file_name": file.filename,
                "created_at": note.created_at.isoformat()
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    return results

@app.post("/ask", response_model=dict)
async def ask_question(request: QuestionRequest):
    answer = qa_engine.answer_question(request.question, request.subject)
    return {"question": request.question, "answer": answer}

@app.post("/practice", response_model=List[dict])
async def generate_practice_questions(request: PracticeQuestionRequest):
    questions = question_generator.generate_questions(request.subject, request.num_questions)
    return questions

@app.post("/evaluate", response_model=dict)
async def evaluate_answer(request: AnswerEvaluationRequest):
    result = answer_evaluator.evaluate_answer(request.question, request.user_answer, request.subject)
    return result

@app.post("/flashcards", response_model=List[dict])
async def generate_flashcards(request: FlashcardRequest):
    flashcards = flashcard_generator.generate_flashcards(request.subject, request.num_flashcards)
    return flashcards