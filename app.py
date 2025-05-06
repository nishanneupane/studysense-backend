import streamlit as st
from data.note_storage import NotesStorage
from backend.qa_engine import QAEngine
from backend.question_generator import QuestionGenerator
from backend.answer_evaluator import AnswerEvaluator
from backend.flashcard_generator import FlashcardGenerator
import os

st.set_page_config(page_title="StudySense", layout="wide")

# Initialize components
storage = NotesStorage()
qa_engine = QAEngine()
question_generator = QuestionGenerator()
answer_evaluator = AnswerEvaluator()
flashcard_generator = FlashcardGenerator()

# Sidebar for navigation
st.sidebar.title("StudySense")
page = st.sidebar.radio("Select Feature", ["Upload Notes", "Ask Questions", "Practice Questions", "Flashcards"])

# Upload Notes
if page == "Upload Notes":
    st.header("Upload Notes")
    subject = st.text_input("Subject (e.g., Math, Physics)")
    uploaded_file = st.file_uploader("Upload Note (TXT, DOCX, PDF)", type=["txt", "docx", "pdf"])
    
    if st.button("Upload") and subject and uploaded_file:
        # Save file temporarily
        file_path = f"temp_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Save to Chroma DB
        try:
            storage.save_note_from_file(file_path, subject)
            st.success(f"Note uploaded for {subject}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            os.remove(file_path)
    
    # List subjects
    subjects = storage.list_subjects()
    st.subheader("Available Subjects")
    for subj in subjects:
        with st.expander(subj):
            notes = storage.load_notes_by_subject(subj)
            for note in notes:
                st.write(f"Created: {note.created_at}")
                st.write(note.content)

# Ask Questions
elif page == "Ask Questions":
    st.header("Ask Questions")
    subject = st.selectbox("Select Subject", storage.list_subjects())
    question = st.text_area("Your Question")
    
    if st.button("Submit Question") and subject and question:
        answer = qa_engine.answer_question(question, subject)
        st.write("**Answer:**")
        st.write(answer)

# Practice Questions
elif page == "Practice Questions":
    st.header("Practice Questions")
    subject = st.selectbox("Select Subject", storage.list_subjects())
    num_questions = st.slider("Number of Questions", 1, 5, 2)
    
    if st.button("Generate Questions") and subject:
        questions = question_generator.generate_questions(subject, num_questions)
        st.session_state["questions"] = questions
        st.session_state["current_question"] = 0
        st.session_state["user_answers"] = ["" for _ in questions]
    
    if "questions" in st.session_state and st.session_state["questions"]:
        q_index = st.session_state["current_question"]
        if q_index < len(st.session_state["questions"]):
            question = st.session_state["questions"][q_index]
            st.write(f"**Question {q_index + 1}:** {question['question']}")
            user_answer = st.text_area("Your Answer", key=f"answer_{q_index}")
            st.session_state["user_answers"][q_index] = user_answer
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Submit Answer"):
                    result = answer_evaluator.evaluate_answer(
                        question["question"], user_answer, subject
                    )
                    st.write(f"**Score:** {result['score']}")
                    st.write(f"**Feedback:** {result['feedback']}")
            with col2:
                if st.button("Next Question"):
                    st.session_state["current_question"] += 1
        else:
            st.write("All questions answered! Generate new questions to continue.")

# Flashcards
elif page == "Flashcards":
    st.header("Flashcards")
    subject = st.selectbox("Select Subject", storage.list_subjects())
    num_flashcards = st.slider("Number of Flashcards", 1, 10, 3)
    
    if st.button("Generate Flashcards") and subject:
        flashcards = flashcard_generator.generate_flashcards(subject, num_flashcards)
        st.session_state["flashcards"] = flashcards
        st.session_state["current_flashcard"] = 0
    
    if "flashcards" in st.session_state and st.session_state["flashcards"]:
        fc_index = st.session_state["current_flashcard"]
        if fc_index < len(st.session_state["flashcards"]):
            flashcard = st.session_state["flashcards"][fc_index]
            st.write(f"**Question {fc_index + 1}:** {flashcard['question']}")
            if st.button("Show Answer"):
                st.write(f"**Answer:** {flashcard['answer']}")
            if st.button("Next Flashcard"):
                st.session_state["current_flashcard"] += 1
        else:
            st.write("All flashcards reviewed! Generate new flashcards to continue.")