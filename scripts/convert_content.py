#!/usr/bin/env python3
"""
Convert user-friendly JSON to production-ready JSON format.
Enhanced with automatic gender detection for speakers.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Security: Only allow input from specific directories
ALLOWED_INPUT_DIRS = [
    'content/teil1/user-submissions/',
    'content/teil1/test-content/',
    'test-content/',
    './'  # Current directory for testing
]

def enhance_speakers_with_gender_detection(content_data):
    """
    Add gender detection to speaker info if not already present.
    This enhances the user JSON with gender information for better voice selection.
    """
    
    def detect_gender_from_name_and_role(speaker_name, role=''):
        """Detect gender from speaker name and role"""
        speaker_lower = speaker_name.lower()
        role_lower = role.lower()
        
        # Strong female indicators
        female_indicators = [
            'bäckerei', 'bibliothek', 'friseurin', 'kundin', 'moderatorin',
            'verkäuferin', 'mitarbeiterin', 'lehrerin', 'ärztin', 'sekretärin'
        ]
        
        # Strong male indicators  
        male_indicators = [
            'trainer', 'optiker', 'verkäufer', 'kunde', 'moderator',
            'mitarbeiter', 'lehrer', 'arzt', 'mechaniker', 'techniker'
        ]
        
        # Check speaker name
        for indicator in female_indicators:
            if indicator in speaker_lower:
                return 'female'
        
        for indicator in male_indicators:
            if indicator in speaker_lower:
                return 'male'
        
        # Check role
        for indicator in female_indicators:
            if indicator in role_lower:
                return 'female'
        
        for indicator in male_indicators:
            if indicator in role_lower:
                return 'male'
        
        # Role ending patterns
        if role_lower.endswith('in') or 'frau' in role_lower:
            return 'female'
        elif 'herr' in role_lower or 'mann' in role_lower:
            return 'male'
        
        # Default fallback
        return 'female'
    
    print("🎭 Enhancing speakers with gender detection...")
    
    # Process each content item
    for i, content_item in enumerate(content_data.get('content', []), 1):
        if 'speakers' in content_item:
            for speaker_name, speaker_info in content_item['speakers'].items():
                # Add gender if not already present
                if 'gender' not in speaker_info:
                    role = speaker_info.get('role', '')
                    detected_gender = detect_gender_from_name_and_role(speaker_name, role)
                    speaker_info['gender'] = detected_gender
                    print(f"   Text {i}: {speaker_name} → {detected_gender}")
                else:
                    print(f"   Text {i}: {speaker_name} → {speaker_info['gender']} (already set)")
    
    return content_data

def convert_teil1_user_to_production(user_data):
    """Convert Teil 1 user JSON to production format with gender enhancement"""
    
    print("📄 Converting Teil 1 format...")
    
    # First, enhance with gender detection
    user_data = enhance_speakers_with_gender_detection(user_data)
    
    # Extract basic info
    exam_info = user_data.get('exam_info', {})
    instructions = user_data.get('instructions', {})
    content = user_data.get('content', [])
    questions = user_data.get('questions', [])
    solutions = user_data.get('solutions', [])
    
    # Create production format with sections array
    production_data = {
        "exam_info": {
            "level": exam_info.get('level', 'A2'),
            "skill": exam_info.get('skill', 'Hörverstehen'),
            "teil": exam_info.get('teil', 1),
            "format": "teil1_combined_display_with_transitions",
            "ubung": exam_info.get('ubung', 1),
            "title": exam_info.get('title', 'Goethe A2 Hörverstehen - Teil 1'),
            "template_name": "teil1_flexible"
        },
        "instructions": instructions,
        "sections": [],
        "content": content,
        "questions": questions,
        "solutions": solutions
    }
    
    # Build sections array
    sections = []
    
    # Add intro
    sections.append({
        "id": "intro",
        "type": "intro"
    })
    
    # Add instructions
    sections.append({
        "id": "instructions", 
        "type": "instructions"
    })
    
    # Add task sections (5 tasks)
    for i in range(1, 6):
        # Add transition
        sections.append({
            "id": f"transition_{i}",
            "type": "transition",
            "transition_text": f"Aufgabe {i}"
        })
        
        # Add combined task
        sections.append({
            "id": f"task_{i}",
            "type": "combined_task", 
            "task_number": i,
            "content_ref": i,
            "question_ref": i
        })
        
        # Add answer reveal
        correct_answer = questions[i-1]['correct_answer'] if i <= len(questions) else 'a'
        answer_text = questions[i-1]['options'][correct_answer] if i <= len(questions) else 'Unknown'
        
        sections.append({
            "id": f"answer_{i}",
            "type": "answer_reveal",
            "task_number": i,
            "correct_answer": correct_answer,
            "answer_text": answer_text
        })
    
    # Add final transition
    sections.append({
        "id": "transition_end",
        "type": "transition",
        "transition_text": "Ende der Übung"
    })
    
    # Add outro
    sections.append({
        "id": "outro",
        "type": "outro"
    })
    
    production_data["sections"] = sections
    
    print(f"✅ Created {len(sections)} sections for Teil 1")
    print(f"🎭 Gender-enhanced {len(content)} content items")
    
    return production_data

def convert_user_to_production(user_json_path):
    """Main conversion function with gender enhancement"""
    
    user_json_path = Path(user_json_path)
    
    # Security check
    allowed = any(str(user_json_path).startswith(allowed_dir) for allowed_dir in ALLOWED_INPUT_DIRS)
    if not allowed:
        print(f"❌ Input file must be in allowed directories: {ALLOWED_INPUT_DIRS}")
        return False
    
    if not user_json_path.exists():
        print(f"❌ User JSON file not found: {user_json_path}")
        return False
    
    print(f"🔄 Converting: {user_json_path}")
    
    try:
        # Load user JSON
        with open(user_json_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # Determine format and convert accordingly
        teil = user_data.get('exam_info', {}).get('teil', 1)
        
        if teil == 1:
            production_data = convert_teil1_user_to_production(user_data)
        else:
            print(f"❌ Teil {teil} conversion not yet implemented")
            return False
        
        # Generate output filename
        base_name = user_json_path.stem
        if base_name.endswith('_user'):
            base_name = base_name[:-5]  # Remove _user suffix
        
        # Create output directory
        output_dir = Path('content/teil1/production-ready')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{base_name}_production.json"
        
        # Save production JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(production_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Production JSON created: {output_path}")
        print(f"📊 Sections: {len(production_data.get('sections', []))}")
        print(f"📝 Content items: {len(production_data.get('content', []))}")
        print(f"❓ Questions: {len(production_data.get('questions', []))}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python convert_content.py <user_json_file>")
        print("🔍 Supported formats:")
        print("   - Teil 1: Combined display with transitions")
        print("   - Teil 2: Long conversation + visual questions (coming soon)")
        print("   - Teil 3: Short dialogues + visual questions (coming soon)")
        print("   - Teil 4: Long interview + text questions (coming soon)")
        print("📁 Allowed directories:")
        for directory in ALLOWED_INPUT_DIRS:
            print(f"   - {directory}")
        sys.exit(1)
    
    user_json_path = sys.argv[1]
    
    # Security check
    dangerous_patterns = ['../', '..\\', '/etc/', '/proc/', 'C:\\', 'system32']
    if any(pattern in user_json_path for pattern in dangerous_patterns):
        print(f"❌ Potentially unsafe path detected: {user_json_path}")
        sys.exit(1)
    
    success = convert_user_to_production(user_json_path)
    
    if success:
        print(f"\n🎉 Conversion complete!")
        print(f"💡 Next step: python scripts/generate_audio.py content/teil1/production-ready/{Path(user_json_path).stem}_production.json")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()