from backend.flashcard_generator import FlashcardGenerator
from data.note_storage import NotesStorage
import os

# Create sample TXT file
def create_sample_file():
    with open("sample_math.txt", "w", encoding="utf-8") as f:
        f.write("The Pythagorean theorem states that a^2 + b^2 = c^2 for a right triangle. It is used to calculate the length of sides in right-angled triangles.")
    return "sample_math.txt"

# Test flashcard generation
storage = NotesStorage()
flashcard_generator = FlashcardGenerator()

# Save sample note
file_path = create_sample_file()
storage.save_note_from_file(file_path, "Math")

# Generate flashcards
flashcards = flashcard_generator.generate_flashcards("Math", num_flashcards=3)
print("Generated Flashcards:")
for fc in flashcards:
    print(fc)

# Clean up
if os.path.exists(file_path):
    os.remove(file_path)