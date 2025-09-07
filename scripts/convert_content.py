#!/usr/bin/env python3
"""
Convert user-friendly JSON to production-ready JSON format.
Transforms simple content into detailed audio/video generation specifications.
SECURE VERSION with path validation.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Define allowed directories for security
# Security whitelist: Only allow files from these trusted directories
# This prevents path traversal attacks by restricting input locations

ALLOWED_INPUT_DIRS = [
    'content/teil1/user-submissions',
    'content/teil1/test-content',
    'tests/test-data'
]

ALLOWED_OUTPUT_DIR = 'content/teil1/production-ready'

def validate_input_path(file_path):
    """
    Validate that the input file path is safe and within allowed directories.
    Protects against path traversal attacks.
    """
    try:
        # Convert to absolute path and resolve any .. or . components
        abs_path = Path(file_path).resolve()
        
        # Get the current working directory
        cwd = Path.cwd().resolve()
        
        # Ensure the file is within our project directory
        if not str(abs_path).startswith(str(cwd)):
            raise ValueError(f"File must be within project directory: {cwd}")
        
        # Get relative path from project root
        try:
            rel_path = abs_path.relative_to(cwd)
        except ValueError:
            raise ValueError("File path is outside project directory")
        
        # Check if the file is in an allowed input directory
        path_str = str(rel_path)
        allowed = any(path_str.startswith(allowed_dir) for allowed_dir in ALLOWED_INPUT_DIRS)
        
        if not allowed:
            raise ValueError(f"File must be in one of these directories: {ALLOWED_INPUT_DIRS}")
        
        # Check file extension
        if not path_str.endswith('.json'):
            raise ValueError("File must have .json extension")
        
        # Check if file exists
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Check if it's actually a file (not directory)
        if not abs_path.is_file():
            raise ValueError(f"Path is not a file: {abs_path}")
        
        return abs_path
        
    except Exception as e:
        print(f"❌ Invalid file path: {e}")
        sys.exit(1)

def create_safe_output_path(input_path):
    """
    Create a safe output path based on the input file name.
    """
    input_file = Path(input_path)
    
    # Extract base filename without extension
    base_name = input_file.stem
    
    # Remove '_user' suffix if present and add '_production'
    if base_name.endswith('_user'):
        base_name = base_name[:-5]  # Remove '_user'
    
    production_name = f"{base_name}_production.json"
    
    # Create output path in allowed directory
    output_path = Path(ALLOWED_OUTPUT_DIR) / production_name
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    return output_path

def convert_user_to_production(user_json_path):
    """Convert user JSON to production format with detailed audio/video specs"""
    
    # Validate and secure the input path
    safe_input_path = validate_input_path(user_json_path)
    
    # Create safe output path
    safe_output_path = create_safe_output_path(safe_input_path)
    
    print(f"📁 Input: {safe_input_path}")
    print(f"📁 Output: {safe_output_path}")
    
    # Load user JSON
    try:
        with open(safe_input_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        sys.exit(1)
    
    # Validate required fields in user data
    required_fields = ['exercise_number', 'texts', 'questions']
    for field in required_fields:
        if field not in user_data:
            print(f"❌ Missing required field in JSON: {field}")
            sys.exit(1)
    
    # Validate we have exactly 5 texts and 5 questions
    if len(user_data['texts']) != 5:
        print(f"❌ Expected 5 texts, found {len(user_data['texts'])}")
        sys.exit(1)
    
    if len(user_data['questions']) != 5:
        print(f"❌ Expected 5 questions, found {len(user_data['questions'])}")
        sys.exit(1)
    
    # Create production JSON structure
    production_data = {
        "exam_info": {
            "level": "A2",
            "skill": "Hörverstehen", 
            "teil": 1,
            "ubung": user_data.get("exercise_number", 1),
            "title": f"Goethe A2 Hörverstehen - Teil 1 - Übung {user_data.get('exercise_number', 1)}",
            "template_name": "teil1_standard"
        },
        "instructions": {
            "main": "Sie hören fünf kurze Texte.",
            "task": "Wählen Sie bei jeder Aufgabe die richtige Lösung a, b oder c.",
            "repetition": "Sie hören jeden Text zweimal."
        },
        "sections": [],
        "content": [],
        "questions": [],
        "solutions": []
    }
    
    # Generate sections (instructions + 5 text/question pairs)
    sections = [
        {
            "id": "instructions",
            "html_element": "instruction-panel",
            "audio": {
                "play_count": 1,
                "estimated_duration": 15.0
            },
            "display": {
                "show_instructions": True,
                "show_content": False,
                "show_question": False
            }
        }
    ]
    
    # Add sections for each of the 5 texts
    for i in range(1, 6):
        # Text section
        sections.append({
            "id": f"text_{i}",
            "html_element": f"content-panel-{i}",
            "content_reference": i,
            "audio": {
                "play_count": 2,
                "pause_between": 3.0,
                "estimated_duration": estimate_audio_duration(user_data['texts'][i-1]['text'])
            },
            "display": {
                "show_instructions": False,
                "show_content": True,
                "show_question": False,
                "show_setup": True
            }
        })
        
        # Question section
        pause_after = 30.0 if i < 5 else 10.0  # Last question gets shorter pause
        sections.append({
            "id": f"question_{i}",
            "html_element": f"question-panel-{i}",
            "question_reference": i,
            "audio": {
                "play_count": 1,
                "pause_after": pause_after,
                "estimated_duration": estimate_question_duration(user_data['questions'][i-1]['question'])
            },
            "display": {
                "show_instructions": False,
                "show_content": False,
                "show_question": True,
                "show_options": True
            }
        })
    
    production_data["sections"] = sections
    
    # Convert content
    for i, text_data in enumerate(user_data['texts'], 1):
        production_data["content"].append({
            "number": i,
            "context": text_data.get('context', ''),
            "setup": text_data.get('setup', ''),
            "type": "monologue",
            "speakers": {
                text_data.get('speaker_name', 'Speaker'): {
                    "voice_name": text_data.get('voice_preference', 'Marlene'),
                    "engine": "neural",
                    "fallback_engines": ["standard"],
                    "language": "de-DE",
                    "gender": text_data.get('gender', 'female'),
                    "speaking_rate": "medium",
                    "role": text_data.get('role', 'service_provider')
                }
            },
            "text": text_data['text'],
            "speaker": text_data.get('speaker_name', 'Speaker')
        })
    
    # Convert questions
    for i, question_data in enumerate(user_data['questions'], 1):
        production_data["questions"].append({
            "number": i,
            "question": question_data['question'],
            "answer_type": "text",
            "options": question_data['options'],
            "correct_answer": question_data['correct_answer']
        })
        
        # Add solution
        production_data["solutions"].append({
            "number": i,
            "answer": question_data['correct_answer'],
            "description": question_data['options'][question_data['correct_answer']]
        })
    
    # Save production JSON securely
    try:
        with open(safe_output_path, 'w', encoding='utf-8') as f:
            json.dump(production_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Converted: {safe_input_path} → {safe_output_path}")
        return str(safe_output_path)
        
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)

def estimate_audio_duration(text):
    """Estimate audio duration based on text length (German speech rate)"""
    if not text or not text.strip():
        return 5.0
    
    words = len(text.split())
    # German speech: ~150 words per minute = 2.5 words per second
    return max(words / 2.5, 5.0)  # Minimum 5 seconds

def estimate_question_duration(question):
    """Estimate question reading duration"""
    if not question or not question.strip():
        return 10.0
    
    words = len(question.split())
    # Slower speech for questions: ~100 words per minute = 1.67 words per second
    return max(words / 1.67 + 8, 10.0)  # Add 8 seconds for options, min 10 seconds

def main():
    """Main function with proper argument validation"""
    if len(sys.argv) != 2:
        print("❌ Usage: python convert_content.py <user_json_file>")
        print("📁 Allowed directories:")
        for directory in ALLOWED_INPUT_DIRS:
            print(f"   - {directory}")
        print("📄 Example: python convert_content.py content/teil1/user-submissions/my_exercise.json")
        sys.exit(1)
    
    user_json_path = sys.argv[1]
    
    # Additional safety check: reject obviously malicious patterns
    dangerous_patterns = ['../', '..\\', '/etc/', '/proc/', 'C:\\', 'system32']
    if any(pattern in user_json_path for pattern in dangerous_patterns):
        print(f"❌ Potentially unsafe path detected: {user_json_path}")
        sys.exit(1)
    
    convert_user_to_production(user_json_path)

if __name__ == "__main__":
    main()