"""
Interactive Backend Tester
Simple command-line tool to test your backend manually
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from backend import process_query, detect_changes, load_geotiff

load_dotenv()

def show_menu():
    print("\n" + "=" * 60)
    print("SatQuery AI - Interactive Backend Tester")
    print("=" * 60)
    print("\n[AVAILABLE TESTS]")
    print("1. Ask AI about urban_port.jpg")
    print("2. Ask AI about flood_after.jpg")
    print("3. Compare flood before/after (change detection)")
    print("4. Compare deforestation before/after (change detection)")
    print("5. Ask custom question about any image")
    print("6. Exit")
    print("\n" + "=" * 60)

def test_single_image(image_name, default_question):
    """Test AI Q&A on a single image"""
    sample_dir = Path("sample_data")
    img_path = sample_dir / image_name

    if not img_path.exists():
        print(f"[ERROR] Image not found: {img_path}")
        return

    print(f"\n[Loading] {image_name}...")
    img = Image.open(img_path)

    print(f"\nDefault question: {default_question}")
    try:
        choice = input("Press ENTER to use default, or type your own question: ").strip()
        question = choice if choice else default_question
    except (EOFError, KeyboardInterrupt):
        question = default_question

    print(f"\n[Analyzing with AI...]")
    result = process_query(img, question, model_type="auto")

    print(f"\n{'=' * 60}")
    print(f"Model: {result['model_used']}")
    print(f"Question: {question}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"{'=' * 60}")

def test_change_detection(before_name, after_name):
    """Test change detection between two images"""
    sample_dir = Path("sample_data")

    print(f"\n[Loading] {before_name} and {after_name}...")
    img_before = Image.open(sample_dir / before_name)
    img_after = Image.open(sample_dir / after_name)

    print(f"[Analyzing changes...]")
    result = detect_changes(img_before, img_after)

    print(f"\n{'=' * 60}")
    print(f"CHANGE DETECTION RESULTS")
    print(f"{'=' * 60}")
    print(f"Summary: {result['summary']}")
    print(f"Changed Pixels: {result['changed_pixels']:,} / {result['total_pixels']:,}")
    print(f"Change Percentage: {result['change_percentage']}%")
    print(f"{'=' * 60}")

    # Save heatmap
    heatmap_path = Path("change_heatmap.png")
    result['diff_heatmap'].save(heatmap_path)
    print(f"\n[Saved] Change heatmap saved to: {heatmap_path}")

def test_custom():
    """Test with custom image and question"""
    sample_dir = Path("sample_data")

    print("\nAvailable images:")
    images = list(sample_dir.glob("*.jpg"))
    for i, img_path in enumerate(images, 1):
        print(f"  {i}. {img_path.name}")

    choice = input("\nSelect image number: ").strip()
    try:
        img_path = images[int(choice) - 1]
    except:
        print("[ERROR] Invalid choice")
        return

    question = input("Enter your question: ").strip()
    if not question:
        print("[ERROR] Question cannot be empty")
        return

    img = Image.open(img_path)
    print(f"\n[Analyzing...]")
    result = process_query(img, question, model_type="auto")

    print(f"\n{'=' * 60}")
    print(f"Image: {img_path.name}")
    print(f"Question: {question}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"{'=' * 60}")

def main():
    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("[WARNING] GOOGLE_API_KEY not found in .env file!")
        print("AI will use placeholder mode only.\n")

    while True:
        try:
            show_menu()
            choice = input("Select test (1-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Exiting]")
            break

        if choice == "1":
            test_single_image("urban_port.jpg", "What infrastructure and features do you see in this port area?")

        elif choice == "2":
            test_single_image("flood_after.jpg", "What impact did flooding have on the buildings and river?")

        elif choice == "3":
            test_change_detection("flood_before.jpg", "flood_after.jpg")

        elif choice == "4":
            test_change_detection("deforest_before.jpg", "deforest_after.jpg")

        elif choice == "5":
            test_custom()

        elif choice == "6":
            print("\n[Goodbye!] Backend testing complete.\n")
            break

        else:
            print("[ERROR] Invalid choice. Try again.")

if __name__ == "__main__":
    main()
