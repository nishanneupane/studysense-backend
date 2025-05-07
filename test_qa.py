import requests
import json

BASE_URL = "http://localhost:8000"

def test_flashcard_workflow():
    print("Testing flashcard workflow...")
    
    # Generate and save flashcards
    print("\n1. Generating 2 flashcards for Math...")
    payload = {"subject": "Math", "num_flashcards": 2}
    res = requests.post(f"{BASE_URL}/flashcards", json=payload)
    if res.status_code != 200:
        print(f"Failed to generate flashcards: {res.text}")
        return
    flashcards = res.json()
    print("Generated flashcards:", json.dumps(flashcards, indent=2))
    
    # Verify flashcards are saved
    print("\n2. Fetching saved flashcards for Math...")
    res = requests.get(f"{BASE_URL}/flashcards/Math")
    if res.status_code != 200:
        print(f"Failed to fetch flashcards: {res.text}")
        return
    saved_flashcards = res.json()
    print("Saved flashcards:", json.dumps(saved_flashcards, indent=2))
    
    # Delete one flashcard
    if saved_flashcards:
        flashcard_id = saved_flashcards[0]["id"]
        print(f"\n3. Deleting flashcard ID {flashcard_id}...")
        res = requests.delete(f"{BASE_URL}/flashcard/Math/{flashcard_id}")
        if res.status_code != 200:
            print(f"Failed to delete flashcard: {res.text}")
            return
        print("Delete response:", res.json())
    
    # Verify deletion
    print("\n4. Fetching saved flashcards after deletion...")
    res = requests.get(f"{BASE_URL}/flashcards/Math")
    if res.status_code != 200:
        print(f"Failed to fetch flashcards: {res.text}")
        return
    remaining_flashcards = res.json()
    print("Remaining flashcards:", json.dumps(remaining_flashcards, indent=2))
    
    print("\nFlashcard workflow test completed!")

if __name__ == "__main__":
    test_flashcard_workflow()