#!/usr/bin/env python3
"""
Unit tests for convert_content.py
Tests the conversion from user JSON to production JSON format.
"""

import unittest
import json
import tempfile
import os
import sys
from pathlib import Path

# Add scripts directory to path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
from convert_content_old import convert_user_to_production, estimate_audio_duration, estimate_question_duration

class TestContentConverter(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.sample_user_data = {
            "exercise_number": 5,
            "creator_name": "Test Creator",
            "created_date": "2025-09-07",
            "notes": "Test exercise for unit testing",
            
            "texts": [
                {
                    "number": 1,
                    "context": "Test Bäckerei",
                    "setup": "Sie hören eine Test-Nachricht.",
                    "text": "Hallo! Das ist ein Test. Die Torte kostet zwanzig Euro.",
                    "speaker_name": "TestSpeaker1",
                    "voice_preference": "Marlene",
                    "gender": "female",
                    "role": "service_provider"
                },
                {
                    "number": 2,
                    "context": "Test Bibliothek", 
                    "setup": "Sie hören eine Test-Durchsage.",
                    "text": "Die Bibliothek schließt heute früher wegen Tests.",
                    "speaker_name": "TestSpeaker2",
                    "voice_preference": "Hans",
                    "gender": "male",
                    "role": "service_provider"
                },
                {
                    "number": 3,
                    "context": "Test Sport",
                    "setup": "Test-Nachricht vom Sportverein.",
                    "text": "Das Training fällt aus. Nächste Woche ist wieder normal.",
                    "speaker_name": "TestSpeaker3",
                    "voice_preference": "Vicki",
                    "gender": "female", 
                    "role": "service_provider"
                },
                {
                    "number": 4,
                    "context": "Test Optiker",
                    "setup": "Test-Sprachnachricht vom Optiker.",
                    "text": "Ihre Brille ist fertig. Sie können sie morgen abholen.",
                    "speaker_name": "TestSpeaker4",
                    "voice_preference": "Daniel",
                    "gender": "male",
                    "role": "service_provider"
                },
                {
                    "number": 5,
                    "context": "Test Wetter",
                    "setup": "Test-Wetterbericht im Radio.",
                    "text": "Heute wird es sonnig und warm mit fünfundzwanzig Grad.",
                    "speaker_name": "TestSpeaker5",
                    "voice_preference": "Marlene",
                    "gender": "female",
                    "role": "broadcaster"
                }
            ],
            
            "questions": [
                {
                    "number": 1,
                    "question": "Was kostet die Torte?",
                    "options": {
                        "a": "10 Euro",
                        "b": "20 Euro", 
                        "c": "30 Euro"
                    },
                    "correct_answer": "b"
                },
                {
                    "number": 2,
                    "question": "Warum schließt die Bibliothek früher?",
                    "options": {
                        "a": "Wegen Tests",
                        "b": "Wegen Renovierung",
                        "c": "Wegen Feiertag"
                    },
                    "correct_answer": "a"
                },
                {
                    "number": 3,
                    "question": "Was passiert mit dem Training?",
                    "options": {
                        "a": "Es ist normal",
                        "b": "Es fällt aus",
                        "c": "Es ist später"
                    },
                    "correct_answer": "b"
                },
                {
                    "number": 4,
                    "question": "Wann kann die Brille abgeholt werden?",
                    "options": {
                        "a": "Heute",
                        "b": "Morgen",
                        "c": "Übermorgen"
                    },
                    "correct_answer": "b"
                },
                {
                    "number": 5,
                    "question": "Wie wird das Wetter heute?",
                    "options": {
                        "a": "Regnerisch",
                        "b": "Bewölkt",
                        "c": "Sonnig und warm"
                    },
                    "correct_answer": "c"
                }
            ]
        }
    
    def test_estimate_audio_duration(self):
        """Test audio duration estimation"""
        # Short text (5 words) should be minimum 5 seconds
        short_text = "Das ist ein Test hier"
        duration = estimate_audio_duration(short_text)
        self.assertEqual(duration, 5.0)  # Should hit minimum
        
        # Longer text should be calculated properly
        long_text = "Das ist ein sehr langer Text mit vielen Wörtern um die Berechnung zu testen"
        duration = estimate_audio_duration(long_text)
        expected = len(long_text.split()) / 2.5  # 14 words / 2.5 = 5.6 seconds
        self.assertAlmostEqual(duration, expected, places=1)
    
    def test_estimate_question_duration(self):
        """Test question duration estimation"""
        question = "Was ist das?"
        duration = estimate_question_duration(question)
        expected = len(question.split()) / 1.67 + 8  # 3 words / 1.67 + 8 = ~9.8
        self.assertGreaterEqual(duration, 10.0)  # Should hit minimum 10 seconds
    
    def test_convert_user_to_production_structure(self):
        """Test that conversion creates correct production structure"""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='_user.json', delete=False) as temp_user:
            json.dump(self.sample_user_data, temp_user, ensure_ascii=False, indent=2)
            temp_user_path = temp_user.name
        
        try:
            # Convert
            production_path = convert_user_to_production(temp_user_path)
            
            # Load result
            with open(production_path, 'r', encoding='utf-8') as f:
                production_data = json.load(f)
            
            # Test top-level structure
            required_keys = ['exam_info', 'instructions', 'sections', 'content', 'questions', 'solutions']
            for key in required_keys:
                self.assertIn(key, production_data, f"Missing key: {key}")
            
            # Test exam_info
            exam_info = production_data['exam_info']
            self.assertEqual(exam_info['level'], 'A2')
            self.assertEqual(exam_info['skill'], 'Hörverstehen')
            self.assertEqual(exam_info['teil'], 1)
            self.assertEqual(exam_info['ubung'], 5)  # From our test data
            self.assertIn('Übung 5', exam_info['title'])
            
            # Test content count
            self.assertEqual(len(production_data['content']), 5)
            self.assertEqual(len(production_data['questions']), 5)
            self.assertEqual(len(production_data['solutions']), 5)
            
            # Test sections count (1 instruction + 5 texts + 5 questions = 11)
            self.assertEqual(len(production_data['sections']), 11)
            
        finally:
            # Cleanup
            os.unlink(temp_user_path)
            if os.path.exists(production_path):
                os.unlink(production_path)
    
    def test_content_conversion(self):
        """Test that content is converted correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_user.json', delete=False) as temp_user:
            json.dump(self.sample_user_data, temp_user, ensure_ascii=False, indent=2)
            temp_user_path = temp_user.name
        
        try:
            production_path = convert_user_to_production(temp_user_path)
            
            with open(production_path, 'r', encoding='utf-8') as f:
                production_data = json.load(f)
            
            # Test first content item
            content_1 = production_data['content'][0]
            self.assertEqual(content_1['number'], 1)
            self.assertEqual(content_1['context'], 'Test Bäckerei')
            self.assertEqual(content_1['text'], 'Hallo! Das ist ein Test. Die Torte kostet zwanzig Euro.')
            self.assertEqual(content_1['speaker'], 'TestSpeaker1')
            
            # Test speaker configuration
            speaker_info = content_1['speakers']['TestSpeaker1']
            self.assertEqual(speaker_info['voice_name'], 'Marlene')
            self.assertEqual(speaker_info['engine'], 'neural')
            self.assertEqual(speaker_info['language'], 'de-DE')
            self.assertEqual(speaker_info['gender'], 'female')
            
        finally:
            os.unlink(temp_user_path)
            if os.path.exists(production_path):
                os.unlink(production_path)
    
    def test_questions_conversion(self):
        """Test that questions are converted correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_user.json', delete=False) as temp_user:
            json.dump(self.sample_user_data, temp_user, ensure_ascii=False, indent=2)
            temp_user_path = temp_user.name
        
        try:
            production_path = convert_user_to_production(temp_user_path)
            
            with open(production_path, 'r', encoding='utf-8') as f:
                production_data = json.load(f)
            
            # Test first question
            question_1 = production_data['questions'][0]
            self.assertEqual(question_1['number'], 1)
            self.assertEqual(question_1['question'], 'Was kostet die Torte?')
            self.assertEqual(question_1['answer_type'], 'text')
            self.assertEqual(question_1['correct_answer'], 'b')
            self.assertEqual(question_1['options']['b'], '20 Euro')
            
            # Test corresponding solution
            solution_1 = production_data['solutions'][0]
            self.assertEqual(solution_1['number'], 1)
            self.assertEqual(solution_1['answer'], 'b')
            self.assertEqual(solution_1['description'], '20 Euro')
            
        finally:
            os.unlink(temp_user_path)
            if os.path.exists(production_path):
                os.unlink(production_path)
    
    def test_sections_timing(self):
        """Test that sections have proper timing configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_user.json', delete=False) as temp_user:
            json.dump(self.sample_user_data, temp_user, ensure_ascii=False, indent=2)
            temp_user_path = temp_user.name
        
        try:
            production_path = convert_user_to_production(temp_user_path)
            
            with open(production_path, 'r', encoding='utf-8') as f:
                production_data = json.load(f)
            
            sections = production_data['sections']
            
            # Test instruction section
            instruction_section = sections[0]
            self.assertEqual(instruction_section['id'], 'instructions')
            self.assertEqual(instruction_section['audio']['play_count'], 1)
            self.assertEqual(instruction_section['audio']['estimated_duration'], 15.0)
            
            # Test text sections (should be played twice)
            text_sections = [s for s in sections if s['id'].startswith('text_')]
            self.assertEqual(len(text_sections), 5)
            
            for text_section in text_sections:
                self.assertEqual(text_section['audio']['play_count'], 2)
                self.assertEqual(text_section['audio']['pause_between'], 3.0)
                self.assertGreater(text_section['audio']['estimated_duration'], 0)
            
            # Test question sections
            question_sections = [s for s in sections if s['id'].startswith('question_')]
            self.assertEqual(len(question_sections), 5)
            
            # First 4 questions should have 30s pause, last one 10s
            for i, q_section in enumerate(question_sections):
                expected_pause = 30.0 if i < 4 else 10.0
                self.assertEqual(q_section['audio']['pause_after'], expected_pause)
            
        finally:
            os.unlink(temp_user_path)
            if os.path.exists(production_path):
                os.unlink(production_path)

class TestConverterEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_missing_file(self):
        """Test behavior with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            convert_user_to_production('nonexistent_file.json')
    
    def test_empty_text_duration(self):
        """Test duration estimation with empty text"""
        duration = estimate_audio_duration("")
        self.assertEqual(duration, 5.0)  # Should return minimum
    
    def test_very_long_text_duration(self):
        """Test duration estimation with very long text"""
        long_text = " ".join(["word"] * 100)  # 100 words
        duration = estimate_audio_duration(long_text)
        expected = 100 / 2.5  # 40 seconds
        self.assertEqual(duration, expected)

def run_tests():
    """Run all tests and provide clear output"""
    print("🧪 Running Content Converter Tests...")
    print("=" * 50)
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestContentConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestConverterEdgeCases))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        print(f"📊 Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"📊 Ran {result.testsRun} tests")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"💥 Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()