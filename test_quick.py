"""
Quick smoke test for the PawPal agent.

Runs the PawPalAgent end-to-end with a sample pet profile and prints
the resulting care plan in a readable, formatted way.

Usage:
    python test_quick.py
"""

import os

# Work around a macOS OpenMP conflict between faiss and other native libs.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from dotenv import load_dotenv

load_dotenv()  # load GROQ_API_KEY from .env

from src.agent import PawPalAgent


def print_section(title, emoji=""):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"{emoji}  {title}".strip())
    print("=" * 60)


def main():
    print_section("PawPal Agent Quick Test", "🐾")

    # 1. Create the agent
    print("\n🔧 Initializing PawPalAgent...")
    agent = PawPalAgent()
    print("✅ Agent ready.")

    # 2. Define the pet profile
    pet_profile = {
        "name": "Buddy",
        "breed": "Golden Retriever",
        "age": 3,
        "weight_kg": 30,
        "health_conditions": [],
    }

    user_request = "Create a daily care plan"

    print_section("Pet Profile", "🐕")
    print(f"  Name:              {pet_profile['name']}")
    print(f"  Breed:             {pet_profile['breed']}")
    print(f"  Age:               {pet_profile['age']} years")
    print(f"  Weight:            {pet_profile['weight_kg']} kg")
    conditions = pet_profile["health_conditions"] or ["None"]
    print(f"  Health Conditions: {', '.join(conditions)}")
    print(f"\n📝 Request: {user_request}")

    # 3. Run the agent
    print_section("Running Agent", "⚙️")
    print("Generating care plan (this may take a moment)...")
    result = agent.run(pet_profile, user_request)

    # 4. Display the results
    print_section("Validated Care Plan", "📋")
    print(result.get("validated_plan", "(no plan generated)"))

    confidence = result.get("confidence_score", 0.0)
    print_section("Confidence Score", "🎯")
    bar_length = 20
    filled = int(round(confidence * bar_length))
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"  {bar}  {confidence:.0%}")

    print_section("Issues", "⚠️")
    issues = result.get("issues", [])
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ No issues found!")

    print_section("Explanation", "💡")
    print(result.get("explanation", "(no explanation generated)"))

    print_section("Test Complete", "🎉")


if __name__ == "__main__":
    main()
