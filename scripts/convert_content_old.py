#!/usr/bin/env python3
"""
Convert user-friendly JSON to production-ready JSON format.
Transforms simple content into detailed audio/video generation specifications.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def convert_user_to_production(user_json_path):
    """Convert user JSON to production format with detailed audio/video specs"""
    
    # Load user JSON
    with open(user_json_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
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
    
    # Save production JSON
    output_path = user_json_path.replace('_user.json', '_production.json')
    output_path = output_path.replace('user-submissions', 'production-ready')
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(production_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Converted: {user_json_path} → {output_path}")
    return output_path

def estimate_audio_duration(text):
    """Estimate audio duration based on text length (German speech rate)"""
    words = len(text.split())
    # German speech: ~150 words per minute = 2.5 words per second
    return max(words / 2.5, 5.0)  # Minimum 5 seconds

def estimate_question_duration(question):
    """Estimate question reading duration"""
    words = len(question.split())
    # Slower speech for questions: ~100 words per minute = 1.67 words per second
    return max(words / 1.67 + 8, 10.0)  # Add 8 seconds for options, min 10 seconds

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_content.py <user_json_file>")
        sys.exit(1)
    
    user_json_path = sys.argv[1]
    convert_user_to_production(user_json_path)