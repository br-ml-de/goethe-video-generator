#!/usr/bin/env python3
"""
Comprehensive test suite for audio generation.
Tests both functionality and integration with Amazon Polly.
"""

import unittest
import tempfile
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the audio generator
from generate_audio_old import AudioGenerator

class TestAudioGeneratorUnit(unittest.TestCase):
    """Unit tests for AudioGenerator class methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.audio_gen = AudioGenerator()
        
        # Sample production JSON data
        self.sample_production_data = {
            "exam_info": {
                "title": "Goethe A2 Hörverstehen - Teil 1 - Übung 1",
                "level": "A2",
                "teil": 1,
                "ubung": 1
            },
            "instructions": {
                "main": "Sie hören fünf kurze Texte.",
                "task": "Wählen Sie bei jeder Aufgabe die richtige Lösung a, b oder c.",
                "repetition": "Sie hören jeden Text zweimal."
            },
            "content": [
                {
                    "number": 1,
                    "text": "Hallo! Das ist ein Test.",
                    "speaker": "TestSpeaker",
                    "speakers": {
                        "TestSpeaker": {
                            "voice_name": "Marlene",
                            "engine": "neural",
                            "fallback_engines": ["standard"],
                            "language": "de-DE",
                            "gender": "female",
                            "speaking_rate": "medium",
                            "role": "service_provider"
                        }
                    }
                }
            ],
            "questions": [
                {
                    "number": 1,
                    "question": "Was ist das?",
                    "options": {
                        "a": "Ein Test",
                        "b": "Ein Spiel", 
                        "c": "Ein Buch"
                    },
                    "correct_answer": "a"
                }
            ]
        }
    
    def test_audio_generator_initialization(self):
        """Test AudioGenerator initializes correctly"""
        self.assertEqual(self.audio_gen.output_format, 'mp3')
        self.assertEqual(self.audio_gen.sample_rate, '22050')
        self.assertIsNotNone(self.audio_gen.polly_client)
    
    def test_create_silence(self):
        """Test silence generation"""
        silence = self.audio_gen.create_silence(2.0)
        self.assertEqual(len(silence), 2000)  # 2 seconds = 2000ms
    
    @patch('boto3.client')
    def test_generate_speech_success(self, mock_boto_client):
        """Test successful speech generation"""
        # Mock Polly response
        mock_response = {
            'AudioStream': Mock()
        }
        mock_response['AudioStream'].read.return_value = b'fake_audio_data'
        
        mock_polly = Mock()
        mock_polly.synthesize_speech.return_value = mock_response
        mock_boto_client.return_value = mock_polly
        
        # Create new generator with mocked client
        audio_gen = AudioGenerator()
        audio_gen.polly_client = mock_polly
        
        # Test speech generation
        result = audio_gen.generate_speech("Test text", "Marlene", "neural")
        
        self.assertEqual(result, b'fake_audio_data')
        mock_polly.synthesize_speech.assert_called_once_with(
            Text="Test text",
            OutputFormat='mp3',
            VoiceId="Marlene",
            Engine="neural",
            SampleRate='22050'
        )
    
    @patch('boto3.client')
    def test_generate_speech_fallback(self, mock_boto_client):
        """Test fallback to standard engine when neural fails"""
        mock_polly = Mock()
        
        # Create mock for successful response
        mock_success_response = {'AudioStream': Mock()}
        mock_success_response['AudioStream'].read.return_value = b'fallback_audio'
        
        # First call (neural) fails, second call (standard) succeeds
        mock_polly.synthesize_speech.side_effect = [
            ClientError({'Error': {'Code': 'InvalidParameterValue'}}, 'synthesize_speech'),
            mock_success_response
        ]
        
        mock_boto_client.return_value = mock_polly
        
        audio_gen = AudioGenerator()
        audio_gen.polly_client = mock_polly
        
        result = audio_gen.generate_speech("Test", "Marlene", "neural")
        
        # Should have been called twice (neural, then standard)
        self.assertEqual(mock_polly.synthesize_speech.call_count, 2)
        self.assertEqual(result, b'fallback_audio')

    
    def test_save_audio(self):
        """Test audio file saving"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test.mp3'
            test_data = b'test_audio_data'
            
            self.audio_gen.save_audio(test_data, output_path)
            
            self.assertTrue(output_path.exists())
            with open(output_path, 'rb') as f:
                self.assertEqual(f.read(), test_data)

class TestAudioGeneratorIntegration(unittest.TestCase):
    """Integration tests with real AWS Polly (optional)"""
    
    def setUp(self):
        """Set up for integration tests"""
        self.audio_gen = AudioGenerator()
        
        # Check if AWS credentials are available
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            self.aws_available = credentials is not None
        except:
            self.aws_available = False
    
    @unittest.skipUnless(os.getenv('TEST_WITH_AWS') == 'true', "Set TEST_WITH_AWS=true to run AWS tests")
    def test_real_polly_connection(self):
        """Test actual connection to Amazon Polly (requires AWS credentials)"""
        if not self.aws_available:
            self.skipTest("AWS credentials not available")
        
        try:
            # Test with a very short text to minimize costs
            result = self.audio_gen.generate_speech("Test", "Marlene", "neural")
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 0)
        except Exception as e:
            self.fail(f"Polly connection failed: {e}")
    
    @unittest.skipUnless(os.getenv('TEST_WITH_AWS') == 'true', "Set TEST_WITH_AWS=true to run AWS tests")
    def test_german_voices_available(self):
        """Test that German voices are available"""
        if not self.aws_available:
            self.skipTest("AWS credentials not available")
        
        try:
            polly = boto3.client('polly', region_name='us-east-1')
            voices = polly.describe_voices(LanguageCode='de-DE')
            
            voice_names = [voice['Id'] for voice in voices['Voices']]
            
            # Check that our required voices are available
            required_voices = ['Marlene', 'Hans', 'Vicki', 'Daniel']
            for voice in required_voices:
                self.assertIn(voice, voice_names, f"Voice {voice} not available")
                
        except Exception as e:
            self.fail(f"Voice check failed: {e}")

class TestAudioGeneratorEnd2End(unittest.TestCase):
    """End-to-end tests with mocked Polly"""
    
    def setUp(self):
        """Set up for end-to-end tests"""
        self.test_production_data = {
            "exam_info": {
                "title": "Test Exercise",
                "level": "A2",
                "teil": 1,
                "ubung": 1
            },
            "instructions": {
                "main": "Test instructions.",
                "task": "Test task.",
                "repetition": "Test repetition."
            },
            "content": [
                {
                    "number": 1,
                    "text": "Test text one.",
                    "speaker": "Speaker1",
                    "speakers": {
                        "Speaker1": {
                            "voice_name": "Marlene",
                            "engine": "neural"
                        }
                    }
                },
                {
                    "number": 2,
                    "text": "Test text two.",
                    "speaker": "Speaker2", 
                    "speakers": {
                        "Speaker2": {
                            "voice_name": "Hans",
                            "engine": "neural"
                        }
                    }
                }
            ],
            "questions": [
                {
                    "number": 1,
                    "question": "Test question one?",
                    "options": {"a": "Option A", "b": "Option B", "c": "Option C"}
                },
                {
                    "number": 2,
                    "question": "Test question two?",
                    "options": {"a": "Option A", "b": "Option B", "c": "Option C"}
                }
            ]
        }
    
    @patch('generate_audio.AudioSegment')
    @patch('generate_audio.AudioGenerator.generate_speech')
    @patch('generate_audio.AudioGenerator.save_audio')
    def test_generate_all_audio_structure(self, mock_save, mock_generate, mock_audio_segment):
        """Test complete audio generation process structure"""
        
        # Mock AudioSegment for duration calculation
        mock_segment = Mock()
        mock_segment.__len__ = Mock(return_value=5000)  # 5 seconds
        mock_audio_segment.from_mp3.return_value = mock_segment
        
        # Mock speech generation
        mock_generate.return_value = b'fake_audio_data'
        
        # Create temporary production file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(self.test_production_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            audio_gen = AudioGenerator()
            audio_dir, sequence_info = audio_gen.generate_all_audio(temp_file_path)
            
            # Verify structure
            self.assertIsInstance(audio_dir, Path)
            self.assertIsInstance(sequence_info, dict)
            
            # Check sequence info structure
            self.assertIn('total_duration', sequence_info)
            self.assertIn('audio_files', sequence_info)
            self.assertIn('sequence', sequence_info)
            
            # Check that all expected audio types are generated
            sequence = sequence_info['sequence']
            audio_types = [item['type'] for item in sequence]
            
            self.assertIn('instructions', audio_types)
            self.assertIn('text', audio_types)
            self.assertIn('question', audio_types)
            
            # Verify correct number of calls
            # Should be: 1 instructions + 2 texts + 2 questions = 5 total
            self.assertEqual(mock_generate.call_count, 5)
            
        finally:
            os.unlink(temp_file_path)

class TestAudioValidation(unittest.TestCase):
    """Tests for audio quality and validation"""
    
    def test_audio_duration_calculation(self):
        """Test audio duration calculations are reasonable"""
        from generate_audio_old import AudioGenerator
        
        audio_gen = AudioGenerator()
        
        # Test with fake audio data
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            # Create a minimal MP3 file (this is a hack for testing)
            temp_audio.write(b'\xff\xfb\x90\x00' + b'\x00' * 1000)  # Fake MP3 header + data
            temp_path = temp_audio.name
        
        try:
            # This would normally load with pydub, but we'll mock it
            with patch('generate_audio.AudioSegment') as mock_segment:
                mock_audio = Mock()
                mock_audio.__len__ = Mock(return_value=3000)  # 3 seconds
                mock_segment.from_mp3.return_value = mock_audio
                
                # Load the mock audio
                segment = mock_segment.from_mp3(temp_path)
                duration = len(segment) / 1000.0
                
                self.assertEqual(duration, 3.0)
                
        finally:
            os.unlink(temp_path)

def run_audio_tests(test_level='unit'):
    """
    Run audio tests at different levels
    
    Args:
        test_level: 'unit', 'integration', 'all'
    """
    print(f"🎵 Running Audio Generator Tests - Level: {test_level}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Always run unit tests
    suite.addTests(loader.loadTestsFromTestCase(TestAudioGeneratorUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioGeneratorEnd2End))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioValidation))
    
    # Add integration tests if requested
    if test_level in ['integration', 'all']:
        suite.addTests(loader.loadTestsFromTestCase(TestAudioGeneratorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All audio tests passed!")
        print(f"📊 Ran {result.testsRun} tests successfully")
        
        if test_level == 'unit':
            print("\n💡 To test with real AWS:")
            print("   export TEST_WITH_AWS=true")
            print("   python tests/test_audio_generator.py integration")
    else:
        print("❌ Some audio tests failed!")
        print(f"📊 Ran {result.testsRun} tests")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"💥 Errors: {len(result.errors)}")
        
        # Print detailed error information
        if result.failures:
            print("\n📋 Failures:")
            for test, traceback in result.failures:
                print(f"   {test}: {traceback}")
        
        if result.errors:
            print("\n📋 Errors:")
            for test, traceback in result.errors:
                print(f"   {test}: {traceback}")
    
    return result.wasSuccessful()

def main():
    """Main test runner with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run audio generator tests')
    parser.add_argument('level', nargs='?', default='unit', 
                       choices=['unit', 'integration', 'all'],
                       help='Test level to run')
    
    args = parser.parse_args()
    
    success = run_audio_tests(args.level)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()