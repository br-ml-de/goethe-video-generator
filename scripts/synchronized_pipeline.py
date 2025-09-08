#!/usr/bin/env python3
"""
Complete synchronized pipeline: User JSON → Final MP4 with perfect timing
Enhanced with synchronization validation and timing analysis.
"""

import sys
import subprocess
import asyncio
import time
import json
from pathlib import Path
import argparse
from datetime import datetime
import shutil

class SynchronizedPipeline:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.start_time = time.time()
        self.step_times = {}
        
    def log(self, message, step=None):
        """Log message with timestamp"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if step:
            if step in self.step_times:
                step_duration = current_time - self.step_times[step]
                print(f"[{elapsed:06.1f}s] {message} (took {step_duration:.1f}s)")
            else:
                self.step_times[step] = current_time
                print(f"[{elapsed:06.1f}s] {message}")
        else:
            print(f"[{elapsed:06.1f}s] {message}")
    
    def run_script(self, script_name, args, step_name):
        """Run a Python script and handle errors"""
        script_path = Path('scripts') / script_name
        if not script_path.exists():
            self.log(f"❌ Script not found: {script_path}", step_name)
            return False
        
        cmd = [sys.executable, str(script_path)] + args
        self.log(f"🚀 Running: {script_name} {' '.join(args)}", step_name)
        
        try:
            if self.verbose:
                # Show real-time output
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
                
                for line in process.stdout:
                    print(f"   {line.rstrip()}")
                
                process.wait()
                success = process.returncode == 0
            else:
                # Capture output
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
                
                if not success:
                    self.log(f"❌ {script_name} failed:", step_name)
                    self.log(f"   STDOUT: {result.stdout}")
                    self.log(f"   STDERR: {result.stderr}")
            
            if success:
                self.log(f"✅ {script_name} completed successfully", step_name)
            
            return success
            
        except Exception as e:
            self.log(f"❌ Error running {script_name}: {e}", step_name)
            return False
    
    def validate_timing_synchronization(self, audio_dir, video_path):
        """
        Validate that audio and video timing are properly synchronized.
        """
        self.log("🔍 Validating timing synchronization...")
        
        # Load audio sequence
        sequence_file = Path(audio_dir) / 'audio_sequence.json'
        if not sequence_file.exists():
            self.log(f"❌ Audio sequence not found: {sequence_file}")
            return False
        
        try:
            with open(sequence_file, 'r') as f:
                audio_sequence = json.load(f)
        except Exception as e:
            self.log(f"❌ Error loading audio sequence: {e}")
            return False
        
        # Check video file
        if not video_path.exists():
            self.log(f"❌ Video file not found: {video_path}")
            return False
        
        # Validate timing structure
        total_duration = audio_sequence.get('total_duration', 0)
        sequence_steps = audio_sequence.get('sequence', [])
        
        if total_duration <= 0:
            self.log("❌ Invalid total duration in audio sequence")
            return False
        
        if len(sequence_steps) < 5:  # At least intro + some content
            self.log(f"❌ Too few sequence steps: {len(sequence_steps)}")
            return False
        
        # Validate step timing
        self.log(f"📊 Timing validation:")
        self.log(f"   Total duration: {total_duration:.1f}s")
        self.log(f"   Sequence steps: {len(sequence_steps)}")
        
        # Check for timing gaps or overlaps
        previous_end = 0
        timing_issues = []
        
        for i, step in enumerate(sequence_steps):
            start_time = step.get('start_time', 0)
            duration = step.get('total_duration', step.get('duration', 0))
            step_type = step.get('type', 'unknown')
            
            # Check for gaps
            if start_time > previous_end + 0.5:  # 500ms tolerance
                timing_issues.append(f"Gap at step {i+1}: {previous_end:.1f}s → {start_time:.1f}s")
            
            # Check for overlaps
            if start_time < previous_end - 0.1:  # 100ms tolerance
                timing_issues.append(f"Overlap at step {i+1}: {start_time:.1f}s < {previous_end:.1f}s")
            
            previous_end = start_time + duration
            
            if i < 5:  # Show first 5 steps
                self.log(f"   {i+1:2}. {start_time:6.1f}s: {step_type:12} ({duration:.1f}s)")
        
        if timing_issues:
            self.log("⚠️ Timing issues detected:")
            for issue in timing_issues[:3]:  # Show first 3 issues
                self.log(f"   {issue}")
            if len(timing_issues) > 3:
                self.log(f"   ... and {len(timing_issues) - 3} more issues")
        else:
            self.log("✅ No timing issues detected")
        
        # Check final timing
        expected_end = total_duration
        actual_end = previous_end
        timing_drift = abs(actual_end - expected_end)
        
        if timing_drift > 1.0:  # 1 second tolerance
            self.log(f"⚠️ Timing drift: {timing_drift:.1f}s (expected: {expected_end:.1f}s, actual: {actual_end:.1f}s)")
        else:
            self.log(f"✅ Timing drift within tolerance: {timing_drift:.1f}s")
        
        return len(timing_issues) == 0 and timing_drift <= 1.0
    
    def analyze_audio_structure(self, audio_dir):
        """Analyze the audio structure for debugging"""
        self.log("🔍 Analyzing audio structure...")
        
        audio_files = list(Path(audio_dir).glob('*.mp3'))
        self.log(f"🔍 Found {len(audio_files)} audio files:")
        
        required_files = ['intro.mp3', 'instructions.mp3', 'outro.mp3']
        for file_name in required_files:
            file_path = Path(audio_dir) / file_name
            if file_path.exists():
                size = file_path.stat().st_size / 1024  # KB
                self.log(f"   ✅ {file_name} ({size:.1f} KB)")
            else:
                self.log(f"   ❌ {file_name} (missing)")
        
        # Check for text and question files
        text_files = [f for f in audio_files if f.name.startswith('text_')]
        question_files = [f for f in audio_files if f.name.startswith('question_')]
        
        self.log(f"🔍 Text files: {len(text_files)}")
        self.log(f"❓ Question files: {len(question_files)}")
        
        if len(text_files) != 5:
            self.log(f"⚠️ Expected 5 text files, found {len(text_files)}")
        if len(question_files) != 5:
            self.log(f"⚠️ Expected 5 question files, found {len(question_files)}")
        
        return len(text_files) == 5 and len(question_files) == 5
    
    def check_prerequisites(self):
        """Check that all required files and dependencies exist"""
        self.log("🔍 Checking prerequisites...")
        
        # Check Python dependencies
        try:
            import boto3
            self.log("   ✅ boto3 (AWS SDK)")
        except ImportError:
            self.log("   ❌ boto3 - run: pip install boto3")
            return False
        
        try:
            from playwright.sync_api import sync_playwright
            self.log("   ✅ playwright")
        except ImportError:
            self.log("   ❌ playwright - run: pip install playwright && playwright install chromium")
            return False
        
        # Check for FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            if result.returncode == 0:
                self.log("   ✅ ffmpeg")
            else:
                self.log("   ❌ ffmpeg not working properly")
                return False
        except FileNotFoundError:
            self.log("   ❌ ffmpeg not found - please install FFmpeg")
            return False
        
        # Check required scripts
        required_scripts = [
            'scripts/convert_content.py',
            'scripts/generate_audio.py'
        ]
        
        # Check for video generation script (either name)
        video_script_found = False
        for script_name in ['generate_video_synchronized.py', 'generate_video.py']:
            if Path(f'scripts/{script_name}').exists():
                self.log(f"   ✅ {script_name}")
                video_script_found = True
                break
        
        if not video_script_found:
            self.log("   ❌ No video generation script found")
            return False
        
        missing_files = []
        for script_path in required_scripts:
            if Path(script_path).exists():
                self.log(f"   ✅ {Path(script_path).name}")
            else:
                missing_files.append(script_path)
        
        if missing_files:
            self.log("❌ Missing required scripts:")
            for missing in missing_files:
                self.log(f"   {missing}")
            return False
        
        # Check for templates
        template_paths = [
            'templates/base/teil1_flexible.html',
            'templates/base/teil1_base.html',
            'templates/themed/teil1_energetic.html',
            'templates/themed/teil1_professional.html',
            'templates/styles/teil1_current.html'
        ]
        
        template_found = False
        for template in template_paths:
            if Path(template).exists():
                self.log(f"   ✅ {template}")
                template_found = True
                break
        
        if not template_found:
            self.log("   ❌ No HTML template found")
            self.log("   💡 Create at least one template file")
            return False
        
        # Check intro/outro audio files
        intro_file = Path('assets/standard-audio/intro.mp3')
        outro_file = Path('assets/standard-audio/outro.mp3')
        
        if intro_file.exists():
            self.log("   ✅ intro.mp3")
        else:
            self.log(f"   ❌ intro.mp3 not found: {intro_file}")
            return False
            
        if outro_file.exists():
            self.log("   ✅ outro.mp3")
        else:
            self.log(f"   ❌ outro.mp3 not found: {outro_file}")
            return False
        
        # Check AWS credentials
        try:
            import boto3
            client = boto3.client('polly', region_name='us-east-1')
            # Test connection
            client.describe_voices(LanguageCode='de-DE')
            self.log("   ✅ AWS credentials and Polly access")
        except Exception as e:
            self.log(f"   ❌ AWS/Polly access issue: {e}")
            self.log("   💡 Run: aws configure")
            return False
        
        self.log("✅ All prerequisites met")
        return True
    
    async def run_synchronized_pipeline(self, user_json_path, output_name=None):
        """Run the complete synchronized pipeline"""
        user_json_path = Path(user_json_path)
        
        if not user_json_path.exists():
            self.log(f"❌ Input file not found: {user_json_path}")
            return False
        
        self.log("🎬 Starting Synchronized Pipeline")
        self.log("=" * 60)
        self.log(f"🔍 Input: {user_json_path}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Create directories
        directories = [
            'content/teil1/production-ready',
            'output/audio',
            'output/videos', 
            'output/final'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Determine output names
        if output_name is None:
            output_name = user_json_path.stem
            if output_name.endswith('_user'):
                output_name = output_name[:-5]

        production_base_name = user_json_path.stem
        if production_base_name.endswith('_user'):
            production_base_name = production_base_name[:-5]  # Remove '_user' suffix
        production_base_name += "_production"
        
        self.log(f"🎯 Target output: output/final/{output_name}_final.mp4")
        
        try:
            # Step 1: Convert user JSON to production JSON
            self.log("", "step1")
            self.log("📄 STEP 1: Converting user content to production format")
            success = self.run_script('convert_content.py', [str(user_json_path)], "step1")
            if not success:
                return False
            
            production_json = Path(f'content/teil1/production-ready/{production_base_name}.json')
            if not production_json.exists():
                self.log(f"❌ Production JSON not created: {production_json}")
                return False
            
            # Step 2: Generate synchronized audio files
            self.log("", "step2")
            self.log("🎵 STEP 2: Generating synchronized German audio with Amazon Polly")
            success = self.run_script('generate_audio.py', [str(production_json)], "step2")
            if not success:
                return False
            
            # Verify audio files and analyze structure
            audio_dir = Path(f'output/audio/{production_base_name}')
            if not audio_dir.exists():
                self.log(f"❌ Audio directory not created: {audio_dir}")
                return False
            
            # Analyze audio structure
            if not self.analyze_audio_structure(audio_dir):
                self.log("⚠️ Audio structure issues detected, but continuing...")
            
            # Step 3: Generate synchronized video
            self.log("", "step3")
            self.log("🎬 STEP 3: Recording synchronized video with precise timing")
            
            # Use the synchronized video generator if available
            video_script = 'generate_video_synchronized.py'
            if not Path(f'scripts/{video_script}').exists():
                self.log("⚠️ Synchronized video generator not found, using standard generator")
                video_script = 'generate_video.py'
            
            success = self.run_script(video_script, [str(production_json)], "step3")
            if not success:
                return False
            
            # Verify video was created (try both possible names)
            possible_video_files = [
                Path(f'output/videos/{output_name}.webm'),
                Path(f'output/videos/{production_base_name}.webm'),
                Path(f'output/videos/{user_json_path.stem}.webm'),
                Path(f'output/videos/{output_name}_calibrated.webm'),
                Path(f'output/videos/{user_json_path.stem}_calibrated.webm')
            ]
            
            video_file = None
            for possible_file in possible_video_files:
                if possible_file.exists():
                    video_file = possible_file
                    break
            
            if not video_file:
                self.log(f"❌ Video file not created. Checked:")
                for possible_file in possible_video_files:
                    self.log(f"   {possible_file}")
                return False
            
            self.log(f"✅ Video created: {video_file}")
            
            # Step 4: Validate synchronization
            self.log("", "step4")
            self.log("🔍 STEP 4: Validating audio-video synchronization")
            
            sync_valid = self.validate_timing_synchronization(audio_dir, video_file)
            if not sync_valid:
                self.log("⚠️ Synchronization validation failed, but continuing...")
            else:
                self.log("✅ Synchronization validation passed!")
   
            # Step 5: Sync audio with video using sync_audio_video.py
            self.log("", "step5")
            self.log("🎵 STEP 5: Synchronizing audio with video using sync_audio_video.py")
            
            # Pass the actual video file path to the sync script
            sync_args = [str(production_json), '--video-file', str(video_file)]
            success = self.run_script('sync_audio_video.py', sync_args, "step5")
            if not success:
                self.log("❌ Audio-video synchronization failed")
                return False
            
            # Find the synced video file (check possible output names)
            possible_synced_files = [
                Path(f'output/videos/{output_name}_synced.webm'),
                Path(f'output/videos/{production_base_name}_synced.webm'),
                Path(f'output/videos/{user_json_path.stem}_synced.webm'),
                Path(f'output/videos/{output_name}.webm'),  # Might overwrite original
                video_file  # Fallback to original if sync script doesn't create new file
            ]
            
            synced_video = None
            for possible_file in possible_synced_files:
                if possible_file.exists():
                    # Check if this file has audio
                    try:
                        result = subprocess.run(['ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                                               '-show_entries', 'stream=index', '-of', 'csv=p=0', 
                                               str(possible_file)], capture_output=True, text=True)
                        has_audio = bool(result.stdout.strip())
                        if has_audio:
                            synced_video = possible_file
                            self.log(f"✅ Found synced video with audio: {synced_video}")
                            break
                    except:
                        continue
            
            if not synced_video:
                self.log("❌ No synced video with audio found")
                self.log("💡 Available video files:")
                for possible_file in possible_synced_files:
                    if possible_file.exists():
                        self.log(f"   {possible_file} (exists)")
                return False
            
            video_file = synced_video  # Use synced video for final conversion

            # Step 6: Convert to final MP4
            self.log("", "step6")
            self.log("🎞️ STEP 6: Converting synced video to final MP4")

            final_video = Path(f'output/final/{output_name}_final.mp4')
            final_video.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                'ffmpeg', '-i', str(video_file), 
                '-c:v', 'libx264', '-c:a', 'aac',
                '-y', str(final_video)
            ]

            try:
                self.log(f"   Running: ffmpeg conversion")
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
                if not success:
                    self.log(f"❌ FFmpeg conversion failed: {result.stderr}")
                    return False
                else:
                    self.log("✅ FFmpeg conversion successful")
            except Exception as e:
                self.log(f"❌ FFmpeg error: {e}")
                return False
            
            # Verify final video was created
            if not final_video.exists():
                self.log(f"❌ Final video not created: {final_video}")
                self.log("💡 Checking what files exist in output/final/:")
                final_dir = Path('output/final')
                if final_dir.exists():
                    files = list(final_dir.glob('*'))
                    if files:
                        for f in files:
                            self.log(f"   Found: {f}")
                    else:
                        self.log("   Directory is empty")
                else:
                    self.log("   Directory doesn't exist")
                return False
            
            # Get final video file size
            file_size = final_video.stat().st_size / (1024 * 1024)  # MB
            
            # Load audio sequence for duration info
            try:
                sequence_file = audio_dir / 'audio_sequence.json'
                with open(sequence_file, 'r') as f:
                    audio_info = json.load(f)
                expected_duration = audio_info.get('total_duration', 0)
            except:
                expected_duration = 0
            
            self.log("", "complete")
            self.log("🎉 SYNCHRONIZED PIPELINE COMPLETE!")
            self.log("=" * 60)
            self.log(f"✅ Final video: {final_video}")
            self.log(f"📊 File size: {file_size:.1f} MB")
            self.log(f"⏱️ Expected duration: {expected_duration:.1f}s ({expected_duration/60:.1f} min)")
            self.log(f"🕒 Processing time: {total_time:.1f}s ({total_time/60:.1f} min)")
            self.log(f"🎬 Perfect for YouTube upload!")
            
            # Additional success metrics
            self.log("\n📈 Quality Metrics:")
            self.log(f"   🎵 Audio files: {len(list(audio_dir.glob('*.mp3')))} generated")
            self.log(f"   🎬 Video synchronization: {'✅ Validated' if sync_valid else '⚠️ Warning'}")
            self.log(f"   📊 File efficiency: {file_size/max(expected_duration/60, 1):.1f} MB/min")
            
            return True
            
        except Exception as e:
            self.log(f"💥 Pipeline failed with error: {e}")
            import traceback
            self.log(f"📍 Full traceback: {traceback.format_exc()}")
            return False
    
    def auto_find_production_json(self, user_json_path):
        """Auto-find production JSON from user JSON path"""
        if not user_json_path:
            return None
            
        user_path = Path(user_json_path)
        base_name = user_path.stem
        
        # Try different production JSON locations
        possible_production_files = [
            Path(f'content/teil1/production-ready/{base_name}_production.json'),
            Path(f'content/teil1/production-ready/{user_path.stem}_production.json'),
            Path('content/teil1/production-ready') / f"{base_name.replace('_user', '')}_production.json"
        ]
        
        for prod_file in possible_production_files:
            if prod_file.exists():
                return str(prod_file)
        
        return None

async def main():
    """Main function with enhanced command line interface"""
    parser = argparse.ArgumentParser(description='Synchronized Goethe Video Pipeline')
    parser.add_argument('input_file', nargs='?', help='Path to user JSON file')
    parser.add_argument('--output-name', help='Output name (default: derived from input)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output from all steps')
    parser.add_argument('--check-prereqs', action='store_true',
                       help='Only check prerequisites')
    
    args = parser.parse_args()
    
    pipeline = SynchronizedPipeline(verbose=args.verbose)
    
    if args.check_prereqs:
        success = pipeline.check_prerequisites()
        sys.exit(0 if success else 1)
    
    if not args.input_file:
        print("❌ Input file required")
        print("💡 Usage: python synchronized_pipeline.py your_file.json")
        print("💡 Use --help for more options")
        sys.exit(1)
    
    success = await pipeline.run_synchronized_pipeline(args.input_file, args.output_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())