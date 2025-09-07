#!/usr/bin/env python3
"""
Audio testing configuration and utilities.
Provides test data and helper functions for audio testing.
"""

import json
import tempfile
from pathlib import Path

# Test production JSON data for audio testing
TEST_PRODUCTION_JSON = {
    "exam_info": {
        "level": "A2",
        "skill": "Hörverstehen",
        "teil": 1,
        "ubung": 999,  # Use 999 to avoid conflicts with real exercises
        "title": "Goethe A2 Hörverstehen - Teil 1 - Test Exercise",
        "template_name": "teil1_standard"
    },
    "instructions": {
        "main": "Sie hören fünf kurze Texte.",
        "task": "Wählen Sie bei jeder Aufgabe die richtige Lösung a, b oder c.",
        "repetition": "Sie hören jeden Text zweimal."
    },
    "sections": [
        {
            "id": "instructions",
            "html_element": "instruction-panel",
            "audio": {
                "play_count": 1,
                "estimated_duration": 15.0
            }
        },
        # Text and question sections would be here...
    ],
    "content": [
        {
            "number": 1,
            "context": "Test Audio Context 1",
            "setup": "Sie hören eine Test-Nachricht.",
            "type": "monologue",
            "speakers": {
                "TestSpeaker1": {
                    "voice_name": "Marlene",
                    "engine": "neural",
                    "fallback_engines": ["standard"],
                    "language": "de-DE",
                    "gender": "female",
                    "speaking_rate": "medium",
                    "role": "service_provider"
                }
            },
            "text": "Das ist ein kurzer Test für die Audio-Generierung.",
            "speaker": "TestSpeaker1"
        },
        {
            "number": 2,
            "context": "Test Audio Context 2",
            "setup": "Sie hören eine zweite Test-Nachricht.",
            "type": "monologue",
            "speakers": {
                "TestSpeaker2": {
                    "voice_name": "Hans",
                    "engine": "neural",
                    "fallback_engines": ["standard"],
                    "language": "de-DE",
                    "gender": "male",
                    "speaking_rate": "medium",
                    "role": "service_provider"
                }
            },
            "text": "Hier ist der zweite Text mit männlicher Stimme.",
            "speaker": "TestSpeaker2"
        },
        {
            "number": 3,
            "context": "Test Audio Context 3",
            "setup": "Sie hören eine dritte Test-Nachricht.",
            "type": "monologue",
            "speakers": {
                "TestSpeaker3": {
                    "voice_name": "Vicki",
                    "engine": "generative",
                    "fallback_engines": ["neural", "standard"],
                    "language": "de-DE",
                    "gender": "female",
                    "speaking_rate": "medium",
                    "role": "broadcaster"
                }
            },
            "text": "Der dritte Text verwendet eine andere weibliche Stimme.",
            "speaker": "TestSpeaker3"
        }
    ],
    "questions": [
        {
            "number": 1,
            "question": "Was ist das erste Wort im ersten Text?",
            "answer_type": "text",
            "options": {
                "a": "Das",
                "b": "Dies",
                "c": "Es"
            },
            "correct_answer": "a"
        },
        {
            "number": 2,
            "question": "Welche Stimme spricht den zweiten Text?",
            "answer_type": "text",
            "options": {
                "a": "Weibliche Stimme",
                "b": "Männliche Stimme",
                "c": "Kinderstimme"
            },
            "correct_answer": "b"
        },
        {
            "number": 3,
            "question": "Wie heißt die Sprecherin des dritten Textes?",
            "answer_type": "text",
            "options": {
                "a": "Marlene",
                "b": "Vicki",
                "c": "Anna"
            },
            "correct_answer": "b"
        }
    ],
    "solutions": [
        {"number": 1, "answer": "a", "description": "Das"},
        {"number": 2, "answer": "b", "description": "Männliche Stimme"},
        {"number": 3, "answer": "b", "description": "Vicki"}
    ]
}

# Minimal test data for quick tests
MINIMAL_TEST_DATA = {
    "exam_info": {
        "title": "Minimal Test",
        "level": "A2",
        "teil": 1,
        "ubung": 998
    },
    "instructions": {
        "main": "Kurzer Test.",
        "task": "Wählen Sie a, b oder c.",
        "repetition": "Hören Sie einmal."
    },
    "content": [
        {
            "number": 1,
            "text": "Test.",
            "speaker": "TestSpeaker",
            "speakers": {
                "TestSpeaker": {
                    "voice_name": "Marlene",
                    "engine": "neural"
                }
            }
        }
    ],
    "questions": [
        {
            "number": 1,
            "question": "Test?",
            "options": {"a": "Ja", "b": "Nein", "c": "Vielleicht"}
        }
    ]
}

def create_test_production_file(data=None, suffix="_test_audio"):
    """
    Create a temporary production JSON file for testing
    
    Args:
        data: JSON data to write (defaults to TEST_PRODUCTION_JSON)
        suffix: Filename suffix
    
    Returns:
        Path to temporary file
    """
    if data is None:
        data = TEST_PRODUCTION_JSON
    
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'{suffix}.json', 
        delete=False,
        encoding='utf-8'
    )
    
    json.dump(data, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()
    
    return Path(temp_file.name)

def create_minimal_test_file():
    """Create a minimal test file for quick testing"""
    return create_test_production_file(MINIMAL_TEST_DATA, "_minimal_test")

def cleanup_test_file(file_path):
    """Clean up a test file"""
    try:
        Path(file_path).unlink()
    except FileNotFoundError:
        pass

class AudioTestHelper:
    """Helper class for audio testing"""
    
    def __init__(self):
        self.temp_files = []
    
    def create_test_file(self, data=None, suffix="_test"):
        """Create a test file and track it for cleanup"""
        file_path = create_test_production_file(data, suffix)
        self.temp_files.append(file_path)
        return file_path
    
    def cleanup_all(self):
        """Clean up all created test files"""
        for file_path in self.temp_files:
            cleanup_test_file(file_path)
        self.temp_files.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_all()

# Voice testing configurations
VOICE_TESTS = [
    {"voice_name": "Marlene", "engine": "neural", "gender": "female"},
    {"voice_name": "Hans", "engine": "neural", "gender": "male"},
    {"voice_name": "Vicki", "engine": "generative", "gender": "female"},
    {"voice_name": "Daniel", "engine": "generative", "gender": "male"},
]

# Test texts in German for different scenarios
TEST_TEXTS = {
    "short": "Hallo.",
    "medium": "Das ist ein mittellanger Test für die Audio-Generierung mit normaler Länge.",
    "long": "Das ist ein sehr langer Text für die Audio-Generierung, der verwendet wird, um zu testen, wie das System mit längeren Texten umgeht und ob die Zeitschätzungen korrekt funktionieren.",
    "special_chars": "Café, Größe, Weiß, Straße - äöüß test.",
    "numbers": "Zwanzig Euro, fünfzehn Minuten, um sechzehn Uhr dreißig.",
    "empty": "",
    "whitespace": "   \n\t   "
}

# Expected audio durations (rough estimates for validation)
EXPECTED_DURATIONS = {
    "instructions": (10, 20),  # 10-20 seconds
    "short_text": (3, 8),     # 3-8 seconds  
    "medium_text": (8, 15),   # 8-15 seconds
    "long_text": (15, 30),    # 15-30 seconds
    "question": (8, 20),      # 8-20 seconds
}

def validate_audio_duration(audio_type, actual_duration):
    """
    Validate that audio duration is within expected range
    
    Args:
        audio_type: Type of audio (instructions, short_text, etc.)
        actual_duration: Actual duration in seconds
    
    Returns:
        bool: True if duration is reasonable
    """
    if audio_type not in EXPECTED_DURATIONS:
        return True  # No validation available
    
    min_dur, max_dur = EXPECTED_DURATIONS[audio_type]
    return min_dur <= actual_duration <= max_dur

def print_test_summary(test_name, passed, failed, skipped=0):
    """Print a formatted test summary"""
    total = passed + failed + skipped
    
    print(f"\n📊 {test_name} Test Summary:")
    print(f"   ✅ Passed: {passed}/{total}")
    if failed > 0:
        print(f"   ❌ Failed: {failed}/{total}")
    if skipped > 0:
        print(f"   ⏭️  Skipped: {skipped}/{total}")
    
    if failed == 0:
        print(f"   🎉 All {test_name.lower()} tests successful!")
    else:
        print(f"   ⚠️  {failed} {test_name.lower()} tests need attention")

if __name__ == "__main__":
    print("🧪 Audio Test Configuration")
    print("This module provides test data and utilities for audio testing.")
    print(f"📋 Available test configurations: {len(VOICE_TESTS)} voices, {len(TEST_TEXTS)} test texts")
    
    # Demonstrate creating a test file
    with AudioTestHelper() as helper:
        test_file = helper.create_test_file()
        print(f"📁 Example test file created: {test_file}")
        print(f"📄 File size: {test_file.stat().st_size} bytes")
        # File will be automatically cleaned up