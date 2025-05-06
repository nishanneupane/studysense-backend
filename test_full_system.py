import requests
import os
import json

# FastAPI endpoint
BASE_URL = "http://localhost:8001"

# Create sample TXT file
def create_sample_file():
    with open("sample_math.txt", "w", encoding="utf-8") as f:
        f.write("The Pythagorean theorem states that a^2 + b^2 = c^2 for a right triangle. It is used to calculate the length of sides in right-angled triangles.")
    return "sample_math.txt"

# Test note upload
file_path = create_sample_file()
with open(file_path, "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload?subject=Math",
        files={"files": (file_path, f, "text/plain")}
    )
print("Upload Response:", response.json())

# Test get subjects
response = requests.get(f"{BASE_URL}/subjects")
print("Subjects:", response.json())

# Test get notes
response = requests.get(f"{BASE_URL}/notes/Math")
print("Notes:", response.json())

# Test question answering
response = requests.post(
    f"{BASE_URL}/ask",
    json={"question": "What is the Pythagorean theorem?", "subject": "Math"}
)
print("QA Response:", response.json())

# Test question generation
response = requests.post(
    f"{BASE_URL}/practice",
    json={"subject": "Math", "num_questions": 2}
)
print("Generated Questions:", response.json())

# Test answer evaluation
question = response.json()[0]["question"]
response = requests.post(
    f"{BASE_URL}/evaluate",
    json={
        "question": question,
        "user_answer": "The Pythagorean theorem, a^2 + b^2 = c^2, calculates side lengths in right triangles.",
        "subject": "Math"
    }
)
print("Answer Evaluation:", response.json())

# Test flashcard generation
response = requests.post(
    f"{BASE_URL}/flashcards",
    json={"subject": "Math", "num_flashcards": 3}
)
print("Generated Flashcards:", response.json())

# Clean up
if os.path.exists(file_path):
    os.remove(file_path)