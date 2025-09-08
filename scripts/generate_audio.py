#!/usr/bin/env python3
"""
Enhanced Smart Audio Generator with Configuration System and Buffer Timing
Uses Teil-specific configurations from YAML files instead of hardcoded values
"""

import boto3
import json
import sys
import yaml
from pathlib import Path
import shutil
from pydub import AudioSegment

class ConfigurableAudioGenerator:
    def __init__(self):
        self.polly_client = boto3.client('polly', region_name='us-east-1')
        self.output_format = 'mp3'
        self.sample_rate = '22050'
        self.audio_sequence = []
        self.total_duration = 0.0
        
        # Track voice usage to distribute across speakers
        self.voice_assignments = {}
        self.gender_voice_pools = {
            'female': ['Vicki', 'Marlene'],  # Generative first, then standard
            'male': ['Daniel', 'Hans']       # Generative first, then standard
        }
        self.gender_engine_preferences = {
            'female': ['generative', 'standard'],
            'male': ['generative', 'standard']
        }
        
        # Configuration will be loaded per Teil
        self.config = None
        self.timing_config = None
        self.audio_config = None
    
    def load_teil_config(self, teil: int):
        """Load configuration for specific Teil"""
        config_path = Path(f'config/teil/teil{teil}.yaml')
        
        if not config_path.exists():
            print(f"Warning: No config found for Teil {teil}, using defaults")
            self.config = self._get_default_config()
        else:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                print(f"Loaded configuration for Teil {teil}")
            except Exception as e:
                print(f"Error loading config for Teil {teil}: {e}")
                self.config = self._get_default_config()
        
        # Extract specific config sections
        self.timing_config = self.config.get('timing', {})
        self.audio_config = self.config.get('audio', {})
        
        print(f"Timing config: thinking_time={self.get_thinking_time()}s, pause_between={self.get_pause_between()}s")
        print(f"Buffer config: instructions_buffer={self.get_instructions_buffer()}s, task_start_buffer={self.get_task_start_buffer()}s")
    
    def _get_default_config(self):
        """Fallback configuration if YAML files not available"""
        return {
            'timing': {
                'thinking_time': 5.0,
                'pause_between_plays': 3.0,
                'transition_duration': 2.5,
                'answer_reveal_pause': 2.0,
                'task_setup_pause': 0.5,
                'instructions_buffer': 2.0,      # New: 2s after instructions
                'task_start_buffer': 2.0         # New: 2s before each task
            },
            'audio': {
                'text_play_count': 2,
                'question_play_count': 1,
                'engine_hierarchy': ['generative', 'neural', 'standard'],
                'sample_rate': '22050',
                'format': 'mp3'
            }
        }
    
    def get_thinking_time(self):
        """Get thinking time from config"""
        return self.timing_config.get('thinking_time', 5.0)
    
    def get_pause_between(self):
        """Get pause between plays from config"""
        return self.timing_config.get('pause_between_plays', 3.0)
    
    def get_transition_duration(self):
        """Get minimum transition duration from config"""
        return self.timing_config.get('transition_duration', 2.5)
    
    def get_answer_reveal_pause(self):
        """Get pause after answer reveal from config"""
        return self.timing_config.get('answer_reveal_pause', 2.0)
    
    def get_instructions_buffer(self):
        """Get buffer time after instructions"""
        return self.timing_config.get('instructions_buffer', 2.0)
    
    def get_task_start_buffer(self):
        """Get buffer time before each task starts"""
        return self.timing_config.get('task_start_buffer', 2.0)
    
    def get_text_play_count(self):
        """Get how many times to play text content"""
        return self.audio_config.get('text_play_count', 2)
    
    def get_question_play_count(self):
        """Get how many times to play questions"""
        return self.audio_config.get('question_play_count', 1)
    
    def generate_speech(self, text, voice_name='Vicki', engine='generative'):
        """Generate speech with voice hierarchy: generative -> standard"""
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
            print(f"Polly error with {voice_name} ({engine}): {e}")
            
            # Fallback hierarchy
            if engine == 'generative':
                # Try same voice with standard engine
                print(f"Trying {voice_name} with standard engine...")
                try:
                    return self.generate_speech(text, voice_name, 'standard')
                except:
                    # If that fails, try fallback voice
                    fallback_voice = self.get_fallback_voice(voice_name)
                    print(f"Trying fallback voice {fallback_voice} with standard engine...")
                    return self.generate_speech(text, fallback_voice, 'standard')
            elif engine == 'standard':
                # Already using standard, try fallback voice
                fallback_voice = self.get_fallback_voice(voice_name)
                if fallback_voice != voice_name:
                    print(f"Trying fallback voice {fallback_voice} with standard engine...")
                    return self.generate_speech(text, fallback_voice, 'standard')
            
            # Final fallback - use Marlene with standard
            if voice_name != 'Marlene' or engine != 'standard':
                print(f"Final fallback: Marlene with standard engine...")
                return self.generate_speech(text, 'Marlene', 'standard')
            
            raise
    
    def get_fallback_voice(self, voice_name):
        """Get fallback voice for each primary voice"""
        fallback_map = {
            'Vicki': 'Marlene',      # Female generative -> Female standard
            'Daniel': 'Hans',        # Male generative -> Male standard
            'Marlene': 'Marlene',    # Already standard female
            'Hans': 'Hans'           # Already standard male
        }
        return fallback_map.get(voice_name, 'Marlene')
    
    def detect_speaker_gender(self, speaker_info, speaker_name, context=''):
        """Enhanced gender detection from multiple sources"""
        # 1. Explicit gender in speaker info
        if 'gender' in speaker_info:
            return speaker_info['gender'].lower()
        
        # 2. Voice name mapping
        voice_name = speaker_info.get('voice_name', '').lower()
        if voice_name in ['marlene', 'vicki']:
            return 'female'
        elif voice_name in ['hans', 'daniel']:
            return 'male'
        
        # 3. Speaker name analysis (enhanced)
        speaker_lower = speaker_name.lower()
        role = speaker_info.get('role', '').lower()
        context_lower = context.lower()
        
        # Strong female indicators
        female_indicators = [
            'bäckerei', 'bibliothek', 'friseurin', 'kundin', 'moderatorin',
            'verkäuferin', 'mitarbeiterin', 'lehrerin', 'ärztin'
        ]
        
        # Strong male indicators  
        male_indicators = [
            'trainer', 'optiker', 'verkäufer', 'kunde', 'moderator',
            'mitarbeiter', 'lehrer', 'arzt', 'mechaniker'
        ]
        
        # Check all sources
        all_text = f"{speaker_lower} {role} {context_lower}"
        
        for indicator in female_indicators:
            if indicator in all_text:
                return 'female'
        
        for indicator in male_indicators:
            if indicator in all_text:
                return 'male'
        
        # 4. Fallback: analyze role patterns
        if any(word in role for word in ['in', 'frau']):
            return 'female'
        elif any(word in role for word in ['herr', 'mann']):
            return 'male'
        
        # Default fallback
        return 'female'
    
    def assign_voice_for_speaker(self, speaker_name, detected_gender, content_item):
        """Assign voice ensuring diversity for multiple speakers of same gender"""
        
        # Check if we already assigned a voice to this speaker
        if speaker_name in self.voice_assignments:
            return self.voice_assignments[speaker_name]
        
        # Get available voices for this gender
        available_voices = self.gender_voice_pools[detected_gender].copy()
        engine_preferences = self.gender_engine_preferences[detected_gender].copy()
        
        # Find which voices are already in use for this gender
        used_voices_this_gender = []
        for assigned_speaker, (voice, engine, gender) in self.voice_assignments.items():
            if gender == detected_gender:
                used_voices_this_gender.append(voice)
        
        # Try to assign an unused voice first
        for voice in available_voices:
            if voice not in used_voices_this_gender:
                # Prefer generative engine for first choice
                preferred_engine = engine_preferences[0] if voice == available_voices[0] else engine_preferences[1]
                assignment = (voice, preferred_engine, detected_gender)
                self.voice_assignments[speaker_name] = assignment
                print(f"   NEW: {speaker_name} ({detected_gender}) → {voice} ({preferred_engine})")
                return assignment
        
        # If all voices are used, cycle through them
        voice_index = len([v for v in self.voice_assignments.values() if v[2] == detected_gender]) % len(available_voices)
        selected_voice = available_voices[voice_index]
        selected_engine = engine_preferences[0] if selected_voice == available_voices[0] else engine_preferences[1]
        
        assignment = (selected_voice, selected_engine, detected_gender)
        self.voice_assignments[speaker_name] = assignment
        print(f"   REUSE: {speaker_name} ({detected_gender}) → {selected_voice} ({selected_engine})")
        return assignment
    
    def get_smart_voice_for_speaker(self, speaker_info, content_item):
        """Get voice with multi-speaker awareness"""
        speaker_name = content_item.get('speaker', 'unknown')
        context = content_item.get('context', '')
        
        # Detect gender
        detected_gender = self.detect_speaker_gender(speaker_info, speaker_name, context)
        
        # Assign voice considering existing assignments
        voice_name, engine, gender = self.assign_voice_for_speaker(speaker_name, detected_gender, content_item)
        
        return voice_name, engine, gender
    
    def get_preferred_voice(self, gender='female', role='service_provider'):
        """Get preferred voice based on gender"""
        if gender.lower() == 'female':
            return 'Vicki', 'generative'
        else:
            return 'Daniel', 'generative'
    
    def save_audio(self, audio_data, output_path):
        """Save audio data to file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(audio_data)
    
    def get_audio_duration(self, audio_path):
        """Get duration of audio file in seconds"""
        try:
            audio_segment = AudioSegment.from_mp3(audio_path)
            return len(audio_segment) / 1000.0
        except Exception as e:
            print(f"Could not get duration for {audio_path}: {e}")
            return 3.0
    
    def add_to_sequence(self, step_data):
        """Add step to audio sequence and update total duration"""
        step_data['start_time'] = self.total_duration
        self.audio_sequence.append(step_data)
        
        step_duration = step_data.get('total_duration', step_data.get('duration', 0))
        self.total_duration += step_duration
        
        return self.total_duration
    
    def handle_intro_audio(self, section, audio_dir):
        """Handle intro audio"""
        intro_source = Path('assets/standard-audio/intro.mp3')
        intro_path = audio_dir / 'intro.mp3'
        
        if intro_source.exists():
            shutil.copy2(intro_source, intro_path)
            print(f"Intro copied from assets")
        else:
            intro_text = "Willkommen zum Goethe A2 Hörverstehen Teil 1"
            voice_name, engine = self.get_preferred_voice('female', 'instructor')
            audio_data = self.generate_speech(intro_text, voice_name, engine)
            self.save_audio(audio_data, intro_path)
            print(f"Intro generated with {voice_name} ({engine})")
        
        intro_duration = self.get_audio_duration(intro_path)
        
        step_data = {
            'type': 'intro',
            'file': str(intro_path),
            'duration': intro_duration
        }
        
        self.add_to_sequence(step_data)
        print(f"   Intro: {intro_duration:.1f}s")
    
    def handle_instructions_audio(self, section, data, audio_dir):
        """Handle instructions audio with configurable buffer"""
        instructions_text = f"{data['instructions']['main']} {data['instructions']['task']} {data['instructions']['repetition']}"
        
        voice_name, engine = self.get_preferred_voice('female', 'instructor')
        audio_data = self.generate_speech(instructions_text, voice_name, engine)
        
        instructions_path = audio_dir / 'instructions.mp3'
        self.save_audio(audio_data, instructions_path)
        
        instructions_duration = self.get_audio_duration(instructions_path)
        buffer_time = self.get_instructions_buffer()  # Add configurable buffer
        total_duration = instructions_duration + buffer_time
        
        step_data = {
            'type': 'instructions',
            'file': str(instructions_path),
            'duration': instructions_duration,
            'total_duration': total_duration,  # Include buffer time
            'buffer_after': buffer_time,       # Track buffer separately
            'voice': voice_name,
            'engine': engine
        }
        
        self.add_to_sequence(step_data)
        print(f"   Instructions: {instructions_duration:.1f}s + {buffer_time:.1f}s buffer = {total_duration:.1f}s ({voice_name}, {engine})")
    
    def handle_transition_audio(self, section, audio_dir):
        """Handle transition audio with configurable minimum duration"""
        transition_text = section.get('transition_text', 'Übergang')
        
        voice_name, engine = self.get_preferred_voice('female', 'instructor')
        audio_data = self.generate_speech(transition_text, voice_name, engine)
        
        transition_path = audio_dir / f"transition_{section['id']}.mp3"
        self.save_audio(audio_data, transition_path)
        
        transition_duration = self.get_audio_duration(transition_path)
        
        # Use configurable minimum transition duration
        min_transition_duration = self.get_transition_duration()
        total_duration = max(transition_duration, min_transition_duration)
        
        step_data = {
            'type': 'transition',
            'file': str(transition_path),
            'duration': transition_duration,
            'total_duration': total_duration,
            'transition_text': transition_text,
            'voice': voice_name,
            'engine': engine
        }
        
        self.add_to_sequence(step_data)
        print(f"   Transition '{transition_text}': {transition_duration:.1f}s (total: {total_duration:.1f}s, {voice_name})")
    
    def handle_combined_task_audio(self, section, data, audio_dir):
        """Handle combined task with configurable timing and task start buffer"""
        task_number = section['task_number']
        content_ref = section['content_ref']
        
        content_item = data['content'][content_ref - 1]
        
        # Smart voice selection with multi-speaker support
        if 'speakers' in content_item and content_item['speaker'] in content_item['speakers']:
            speaker_info = content_item['speakers'][content_item['speaker']]
            voice_name, engine, detected_gender = self.get_smart_voice_for_speaker(speaker_info, content_item)
        else:
            voice_name, engine = self.get_preferred_voice('female', 'service_provider')
            detected_gender = 'female'
            print(f"   No speaker info, using default: {voice_name} ({engine})")
        
        # Generate audio
        text_content = content_item['text']
        audio_data = self.generate_speech(text_content, voice_name, engine)
        
        task_path = audio_dir / f"task_{task_number}.mp3"
        self.save_audio(audio_data, task_path)
        
        # Calculate timing using configuration
        task_start_buffer = self.get_task_start_buffer()  # Add buffer before task
        text_duration = self.get_audio_duration(task_path)
        pause_duration = self.get_pause_between()
        thinking_time = self.get_thinking_time()
        play_count = self.get_text_play_count()
        
        # Include task start buffer in total duration
        total_task_duration = task_start_buffer + text_duration * play_count + pause_duration + thinking_time
        
        step_data = {
            'type': 'combined_task',
            'task_number': task_number,
            'file': str(task_path),
            'task_start_buffer': task_start_buffer,  # Track buffer before task
            'text_duration': text_duration,
            'play_count': play_count,
            'pause_between': pause_duration,
            'thinking_time': thinking_time,
            'total_duration': total_task_duration,
            'speaker': content_item.get('speaker', 'unknown'),
            'voice': voice_name,
            'engine': engine,
            'detected_gender': detected_gender
        }
        
        self.add_to_sequence(step_data)
        print(f"   Task {task_number}: {task_start_buffer:.1f}s buffer + {text_duration:.1f}s × {play_count} + {pause_duration:.1f}s + {thinking_time:.1f}s = {total_task_duration:.1f}s")
    
    def handle_answer_reveal_audio(self, section, data, audio_dir):
        """Handle answer reveal audio with configurable pause"""
        task_number = section['task_number']
        correct_answer = section['correct_answer']
        answer_text = section['answer_text']
        
        reveal_text = f"Die richtige Antwort ist {correct_answer}: {answer_text}"
        
        voice_name, engine = self.get_preferred_voice('female', 'instructor')
        audio_data = self.generate_speech(reveal_text, voice_name, engine)
        
        answer_path = audio_dir / f"answer_{task_number}.mp3"
        self.save_audio(audio_data, answer_path)
        
        answer_duration = self.get_audio_duration(answer_path)
        pause_after = self.get_answer_reveal_pause()  # Configurable
        total_duration = answer_duration + pause_after
        
        step_data = {
            'type': 'answer_reveal',
            'task_number': task_number,
            'file': str(answer_path),
            'duration': answer_duration,
            'pause_after': pause_after,
            'total_duration': total_duration,
            'correct_answer': correct_answer,
            'answer_text': answer_text,
            'voice': voice_name,
            'engine': engine
        }
        
        self.add_to_sequence(step_data)
        print(f"   Answer {task_number}: '{correct_answer}: {answer_text}' ({answer_duration:.1f}s + {pause_after:.1f}s, {voice_name})")
    
    def handle_outro_audio(self, section, audio_dir):
        """Handle outro audio"""
        outro_source = Path('assets/standard-audio/outro.mp3')
        outro_path = audio_dir / 'outro.mp3'
        
        if outro_source.exists():
            shutil.copy2(outro_source, outro_path)
            print(f"Outro copied from assets")
        else:
            outro_text = "Vielen Dank! Vergessen Sie nicht zu liken und zu abonnieren!"
            voice_name, engine = self.get_preferred_voice('female', 'instructor')
            audio_data = self.generate_speech(outro_text, voice_name, engine)
            self.save_audio(audio_data, outro_path)
            print(f"Outro generated with {voice_name} ({engine})")
        
        outro_duration = self.get_audio_duration(outro_path)
        
        step_data = {
            'type': 'outro',
            'file': str(outro_path),
            'duration': outro_duration
        }
        
        self.add_to_sequence(step_data)
        print(f"   Outro: {outro_duration:.1f}s")
    
    def generate_all_audio(self, production_json_path):
        """Generate all audio with configurable timing and buffers"""
        
        with open(production_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load Teil-specific configuration
        teil = data['exam_info']['teil']
        self.load_teil_config(teil)
        
        base_name = Path(production_json_path).stem
        audio_dir = Path('output/audio') / base_name
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset sequence and voice tracking
        self.audio_sequence = []
        self.total_duration = 0.0
        self.voice_assignments = {}
        
        title = data['exam_info']['title']
        format_type = data['exam_info'].get('format', 'unknown')
        
        print(f"Configurable Audio Generator with Buffer Timing")
        print(f"Title: {title}")
        print(f"Format: {format_type}")
        print(f"Teil: {teil}")
        print(f"Processing {len(data['sections'])} sections...")
        print(f"Multi-speaker voice distribution enabled")
        
        # Process each section
        for i, section in enumerate(data['sections'], 1):
            section_type = section['type']
            section_id = section.get('id', 'unknown')
            
            print(f"\n{i:2}/{len(data['sections'])}: {section_id} ({section_type})")
            
            try:
                if section_type == 'intro':
                    self.handle_intro_audio(section, audio_dir)
                elif section_type == 'instructions':
                    self.handle_instructions_audio(section, data, audio_dir)
                elif section_type == 'transition':
                    self.handle_transition_audio(section, audio_dir)
                elif section_type == 'combined_task':
                    self.handle_combined_task_audio(section, data, audio_dir)
                elif section_type == 'answer_reveal':
                    self.handle_answer_reveal_audio(section, data, audio_dir)
                elif section_type == 'outro':
                    self.handle_outro_audio(section, audio_dir)
                else:
                    print(f"   Unknown section type: {section_type} - skipping")
                    
            except Exception as e:
                print(f"   Error processing {section_id}: {e}")
                raise
        
        # Save sequence info
        sequence_info = {
            'total_duration': self.total_duration,
            'audio_files': len(self.audio_sequence),
            'sequence': self.audio_sequence,
            'format': format_type,
            'teil': teil,
            'voice_assignments': self.voice_assignments,
            'voice_distribution': self._analyze_voice_distribution(),
            'timing_config': self.timing_config,
            'audio_config': self.audio_config
        }
        
        sequence_path = audio_dir / 'audio_sequence.json'
        with open(sequence_path, 'w', encoding='utf-8') as f:
            json.dump(sequence_info, f, ensure_ascii=False, indent=2)
        
        # Print results
        print(f"\nConfigurable Audio Generation Complete!")
        print(f"Output: {audio_dir}")
        print(f"Duration: {self.total_duration:.1f}s ({self.total_duration/60:.1f} min)")
        print(f"Files: {len(self.audio_sequence)}")
        print(f"Thinking time: {self.get_thinking_time()}s (from Teil {teil} config)")
        print(f"Buffer timing: instructions+{self.get_instructions_buffer()}s, tasks+{self.get_task_start_buffer()}s")
        
        self._print_voice_summary()
        
        return audio_dir, sequence_info
    
    def _analyze_voice_distribution(self):
        """Analyze how voices were distributed"""
        distribution = {
            'female_speakers': {},
            'male_speakers': {},
            'total_by_voice': {}
        }
        
        for speaker, (voice, engine, gender) in self.voice_assignments.items():
            voice_key = f"{voice} ({engine})"
            
            if gender == 'female':
                distribution['female_speakers'][speaker] = voice_key
            else:
                distribution['male_speakers'][speaker] = voice_key
            
            distribution['total_by_voice'][voice_key] = distribution['total_by_voice'].get(voice_key, 0) + 1
        
        return distribution
    
    def _print_voice_summary(self):
        """Print summary of voice assignments"""
        print(f"\nVoice Assignment Summary:")
        
        female_count = len([v for v in self.voice_assignments.values() if v[2] == 'female'])
        male_count = len([v for v in self.voice_assignments.values() if v[2] == 'male'])
        
        print(f"   Female speakers: {female_count}")
        print(f"   Male speakers: {male_count}")
        
        for speaker, (voice, engine, gender) in self.voice_assignments.items():
            gender_icon = '👩' if gender == 'female' else '👨'
            print(f"   {gender_icon} {speaker:15} → {voice:8} ({engine})")
        
        distribution = self._analyze_voice_distribution()
        print(f"\nVoice Usage:")
        for voice, count in distribution['total_by_voice'].items():
            print(f"   {voice:20}: {count} speakers")

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_audio.py <production_json_path>")
        sys.exit(1)
    
    production_json_path = Path(sys.argv[1])
    
    if not production_json_path.exists():
        print(f"Production JSON not found: {production_json_path}")
        sys.exit(1)
    
    try:
        generator = ConfigurableAudioGenerator()
        audio_dir, sequence_info = generator.generate_all_audio(production_json_path)
        
        print(f"\nSuccess! Configurable audio generation complete.")
        print(f"Next: Run video generator with: {audio_dir}")
        
    except Exception as e:
        print(f"Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()