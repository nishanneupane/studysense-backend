from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from data.note_storage import NotesStorage
from data.flashcard_storage import FlashcardStorage
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
flashcard_storage = FlashcardStorage()
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

class SaveFlashcardRequest(BaseModel):
    subject: str
    question: str
    answer: str

class NoteResponse(BaseModel):
    subject: str
    file_name: str
    created_at: str

class FlashcardResponse(BaseModel):
    id: str
    subject: str
    question: str
    answer: str
    created_at: str

class SubjectRequest(BaseModel):
    subject: str

# Routes
@app.get("/subjects", response_model=List[str])
async def get_subjects():
    return storage.list_subjects()

@app.post("/subjects", response_model=dict)
async def create_subject(request: SubjectRequest):
    try:
        storage.create_subject(request.subject)
        return {"message": f"Subject '{request.subject}' created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subject: {str(e)}")

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

@app.post("/flashcards", response_model=List[FlashcardResponse])
async def generate_flashcards(request: FlashcardRequest):
    try:
        flashcards = flashcard_generator.generate_flashcards(request.subject, request.num_flashcards)
        saved_flashcards = flashcard_storage.save_flashcards(request.subject, flashcards)
        return saved_flashcards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate/save flashcards: {str(e)}")

@app.post("/flashcards/save", response_model=FlashcardResponse)
async def save_flashcard(request: SaveFlashcardRequest):
    try:
        flashcard = [{"question": request.question, "answer": request.answer}]
        saved_flashcards = flashcard_storage.save_flashcards(request.subject, flashcard)
        if not saved_flashcards:
            raise HTTPException(status_code=500, detail="Failed to save flashcard")
        return saved_flashcards[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save flashcard: {str(e)}")

@app.get("/flashcards/{subject}", response_model=List[FlashcardResponse])
async def get_flashcards(subject: str):
    try:
        flashcards = flashcard_storage.get_flashcards(subject)
        return flashcards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flashcards: {str(e)}")

@app.delete("/flashcard/{subject}/{flashcard_id}", response_model=dict)
async def delete_flashcard(subject: str, flashcard_id: str):
    try:
        success = flashcard_storage.delete_flashcard(subject, flashcard_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Flashcard {flashcard_id} not found for subject {subject}")
        return {"message": "Flashcard deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete flashcard: {str(e)}")

@app.delete("/subject/{subject}", response_model=dict)
async def delete_subject(subject: str):
    try:
        notes_success = storage.delete_subject(subject)
        flashcards_success = flashcard_storage.delete_subject(subject)
        if not (notes_success and flashcards_success):
            raise HTTPException(status_code=500, detail=f"Failed to fully delete subject {subject}")
        return {"message": f"Subject {subject} and all associated notes and flashcards deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete subject: {str(e)}")