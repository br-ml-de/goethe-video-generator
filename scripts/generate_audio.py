#!/usr/bin/env python3
"""
Generate audio files using Amazon Polly for Goethe listening exercises.
Creates synchronized audio sequence with proper timing.
"""

import boto3
import json
import sys
from pathlib import Path
import os
from pydub import AudioSegment
import shutil

class AudioGenerator:
    def __init__(self):
        self.polly_client = boto3.client('polly', region_name='us-east-1')
        self.output_format = 'mp3'
        self.sample_rate = '22050'
    
    def generate_speech(self, text, voice_name='Marlene', engine='neural'):
        """Generate speech from text using Amazon Polly"""
        try:
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat=self.output_format,
                VoiceId=voice_name,
                Engine=engine,
                SampleRate=self.sample_rate
            )
            return response['AudioStream'].read()
        except Exception as e:
            print(f"❌ Polly error with {engine} engine: {e}")
            if engine == 'neural':
                print("🔄 Trying standard engine...")
                return self.generate_speech(text, voice_name, 'standard')
            raise
    
    def create_silence(self, duration_seconds):
        """Create silence audio segment"""
        return AudioSegment.silent(duration=duration_seconds * 1000)
    
    def save_audio(self, audio_data, output_path):
        """Save audio data to file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(audio_data)
    
    def generate_all_audio(self, production_json_path):
        """Generate all audio files for a production JSON"""
        
        # Load production JSON
        with open(production_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create output directory
        base_name = Path(production_json_path).stem
        audio_dir = Path('output/audio') / base_name
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_sequence = []
        total_duration = 0.0

        # Copy intro audio FIRST - before anything else
        intro_source = Path('assets/standard-audio/intro.mp3')
        if intro_source.exists():
            intro_path = audio_dir / 'intro.mp3'
            shutil.copy2(intro_source, intro_path)
            print(f"🎬 Intro copied to {intro_path}")
            
            # Load intro to get actual duration
            intro_segment = AudioSegment.from_mp3(intro_path)
            intro_duration = len(intro_segment) / 1000.0
            
            audio_sequence.append({
                'type': 'intro',
                'file': str(intro_path),
                'duration': intro_duration,
                'start_time': total_duration
            })
            total_duration += intro_duration
            print(f"🎬 Added intro ({intro_duration:.1f}s)")
        else:
            print(f"⚠️  Intro file not found: {intro_source}")


        # Instructions 
        print(f"🎵 Generating audio for {data['exam_info']['title']}")
        
        # Generate instructions
        instructions_text = f"{data['instructions']['main']} {data['instructions']['task']} {data['instructions']['repetition']}"
        instructions_audio = self.generate_speech(instructions_text, 'Marlene', 'neural')
        instructions_path = audio_dir / 'instructions.mp3'
        self.save_audio(instructions_audio, instructions_path)
        
        # Load as AudioSegment to get duration
        instructions_segment = AudioSegment.from_mp3(instructions_path)
        instructions_duration = len(instructions_segment) / 1000.0
        
        audio_sequence.append({
            'type': 'instructions',
            'file': str(instructions_path),
            'duration': instructions_duration,
            'start_time': total_duration
        })
        total_duration += instructions_duration
        
        # Generate content audio (texts and questions)
        for i, content_item in enumerate(data['content'], 1):
            # Get speaker info
            speaker_name = content_item['speaker']
            speaker_info = content_item['speakers'][speaker_name]
            voice_name = speaker_info['voice_name']
            engine = speaker_info['engine']
            
            # Generate text audio
            print(f"🎙️  Generating text {i}: {voice_name} ({engine})")
            text_audio = self.generate_speech(content_item['text'], voice_name, engine)
            text_path = audio_dir / f'text_{i}.mp3'
            self.save_audio(text_audio, text_path)
            
            # Load to get duration
            text_segment = AudioSegment.from_mp3(text_path)
            text_duration = len(text_segment) / 1000.0
            
            # Add text played twice with pause
            audio_sequence.append({
                'type': 'text',
                'number': i,
                'file': str(text_path),
                'duration': text_duration,
                'play_count': 2,
                'pause_between': 3.0,
                'total_duration': text_duration * 2 + 3.0,
                'start_time': total_duration
            })
            total_duration += text_duration * 2 + 3.0
            
            # Generate question audio
            question_data = data['questions'][i-1]
            question_text = f"{question_data['question']} a) {question_data['options']['a']} b) {question_data['options']['b']} c) {question_data['options']['c']}"
            
            print(f"❓ Generating question {i}")
            question_audio = self.generate_speech(question_text, 'Marlene', 'neural')
            question_path = audio_dir / f'question_{i}.mp3'
            self.save_audio(question_audio, question_path)
            
            # Load to get duration
            question_segment = AudioSegment.from_mp3(question_path)
            question_duration = len(question_segment) / 1000.0
            
            # Add thinking time (30s for first 4, 10s for last)
            thinking_time = 30.0 if i < 5 else 10.0
            
            audio_sequence.append({
                'type': 'question',
                'number': i,
                'file': str(question_path),
                'duration': question_duration,
                'thinking_time': thinking_time,
                'total_duration': question_duration + thinking_time,
                'start_time': total_duration
            })
            total_duration += question_duration + thinking_time
        
        # Outro audio (add this entire block)
        outro_source = Path('assets/standard-audio/outro.mp3')
        if outro_source.exists():
            outro_path = audio_dir / 'outro.mp3'
            shutil.copy2(outro_source, outro_path)
            
            # Load outro to get actual duration
            outro_segment = AudioSegment.from_mp3(outro_path)
            outro_duration = len(outro_segment) / 1000.0
            
            audio_sequence.append({
                'type': 'outro',
                'file': str(outro_path),
                'duration': outro_duration,
                'start_time': total_duration
            })
            total_duration += outro_duration
            print(f"🎬 Added outro ({outro_duration:.1f}s)")
        else:
            print(f"⚠️  Outro file not found: {outro_source}")


        # Save audio sequence information
        sequence_info = {
            'total_duration': total_duration,
            'audio_files': len([item for item in audio_sequence]),
            'sequence': audio_sequence,
            'generated_at': str(Path(production_json_path).stat().st_mtime)
        }
        
        sequence_path = audio_dir / 'audio_sequence.json'
        with open(sequence_path, 'w', encoding='utf-8') as f:
            json.dump(sequence_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Audio generation complete!")
        print(f"📁 Output directory: {audio_dir}")
        print(f"⏱️  Total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        print(f"📄 Sequence info: {sequence_path}")
        
        return audio_dir, sequence_info

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_audio.py <production_json_file>")
        sys.exit(1)
    
    production_json_path = sys.argv[1]
    
    if not Path(production_json_path).exists():
        print(f"❌ File not found: {production_json_path}")
        sys.exit(1)
    
    generator = AudioGenerator()
    generator.generate_all_audio(production_json_path)

if __name__ == "__main__":
    main()