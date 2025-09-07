#!/usr/bin/env python3
"""
Complete end-to-end pipeline: User JSON → Final MP4
Runs all components in sequence with error handling and progress tracking.
"""

import sys
import subprocess
import asyncio
import time
from pathlib import Path
import argparse
from datetime import datetime

class CompletePipeline:
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
    
    def check_prerequisites(self):
        """Check that all required files and dependencies exist"""
        self.log("🔍 Checking prerequisites...")
        
        required_scripts = [
            'scripts/convert_content.py',
            'scripts/generate_audio.py', 
            'scripts/generate_video.py',
            'scripts/sync_audio_video.py'
        ]
        
        missing_files = []
        for script_path in required_scripts:
            if not Path(script_path).exists():
                missing_files.append(script_path)
        
        if missing_files:
            self.log("❌ Missing required scripts:")
            for missing in missing_files:
                self.log(f"   {missing}")
            return False
        
        # Check for template
        template_paths = [
            'templates/styles/teil1_test.html',
            'templates/styles/teil1_enhanced.html',
            'templates/styles/teil1_current.html'
        ]
        
        template_found = any(Path(p).exists() for p in template_paths)
        if not template_found:
            self.log("❌ No HTML template found in:")
            for template in template_paths:
                self.log(f"   {template}")
            return False
        
        # Check Python dependencies
        try:
            import boto3, pydub, playwright
            self.log("✅ Python dependencies available")
        except ImportError as e:
            self.log(f"❌ Missing Python dependency: {e}")
            return False
        
        # Check external tools
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.log("✅ FFmpeg available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ FFmpeg not found - install with: brew install ffmpeg")
            return False
        
        try:
            subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                         capture_output=True, check=True)
            self.log("✅ AWS credentials configured")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ AWS not configured - run: aws configure")
            return False
        
        self.log("✅ All prerequisites met")
        return True
    
    def create_directories(self):
        """Create necessary output directories"""
        directories = [
            'content/teil1/production-ready',
            'output/audio',
            'output/videos', 
            'output/final'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        self.log("✅ Output directories ready")
    
    async def run_complete_pipeline(self, user_json_path, output_name=None):
        """Run the complete pipeline from user JSON to final MP4"""
        user_json_path = Path(user_json_path)
        
        if not user_json_path.exists():
            self.log(f"❌ Input file not found: {user_json_path}")
            return False
        
        self.log("🎬 Starting Complete Pipeline")
        self.log("=" * 60)
        self.log(f"📝 Input: {user_json_path}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Create directories
        self.create_directories()
        
        # Determine output name
        if output_name is None:
            output_name = user_json_path.stem
            # Remove _user suffix if present
            if output_name.endswith('_user'):
                output_name = output_name[:-5]

        # The production file will have the full original name + _production
        production_base_name = user_json_path.stem + "_production"

        
        self.log(f"🎯 Target output: output/final/{output_name}_final.mp4")
        
        try:
            # Step 1: Convert user JSON to production JSON
            self.log("", "step1")
            self.log("📝 STEP 1: Converting user content to production format")
            success = self.run_script('convert_content.py', [str(user_json_path)], "step1")
            if not success:
                return False
            
            # Verify production JSON was created
            production_json = Path(f'content/teil1/production-ready/{production_base_name}.json')
            if not production_json.exists():
                self.log(f"❌ Production JSON not created: {production_json}")
                return False
            
            # Step 2: Generate audio files
            self.log("", "step2")
            self.log("🎵 STEP 2: Generating German audio with Amazon Polly")
            success = self.run_script('generate_audio.py', [str(production_json)], "step2")
            if not success:
                return False
            
            # Verify audio files were created
            audio_dir = Path(f'output/audio/{production_base_name}')
            if not audio_dir.exists():
                self.log(f"❌ Audio directory not created: {audio_dir}")
                return False
            
            audio_files = list(audio_dir.glob('*.mp3'))
            if len(audio_files) < 5:
                self.log(f"❌ Expected at least 5 audio files, found {len(audio_files)}")
                return False
            
            # Step 3: Generate video
            self.log("", "step3")
            self.log("🎬 STEP 3: Recording synchronized video with Playwright")
            success = self.run_script('generate_video.py', [str(production_json)], "step3")
            if not success:
                return False
            
            # Verify video was created
            video_file = Path(f'output/videos/{output_name}.webm')
            if not video_file.exists():
                self.log(f"❌ Video file not created: {video_file}")
                return False
            
            # Step 4: Synchronize audio and video
            self.log("", "step4")
            self.log("🎊 STEP 4: Combining audio and video into final MP4")
            success = self.run_script('sync_audio_video.py', [str(production_json)], "step4")
            if not success:
                return False
            
            # Verify final video was created
            final_video = Path(f'output/final/{output_name}_final.mp4')
            if not final_video.exists():
                self.log(f"❌ Final video not created: {final_video}")
                return False
            
            # Success!
            total_time = time.time() - self.start_time
            file_size = final_video.stat().st_size / (1024 * 1024)  # MB
            
            self.log("", "complete")
            self.log("🎉 PIPELINE COMPLETE!")
            self.log("=" * 60)
            self.log(f"✅ Final video: {final_video}")
            self.log(f"📊 File size: {file_size:.1f} MB")
            self.log(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
            self.log("🎬 Ready for YouTube upload!")
            
            return True
            
        except Exception as e:
            self.log(f"💥 Pipeline failed with error: {e}")
            return False
    
    def test_individual_components(self, user_json_path):
        """Test each component individually for debugging"""
        self.log("🧪 Testing Individual Components")
        self.log("=" * 60)
        
        user_json_path = Path(user_json_path)
        if not user_json_path.exists():
            self.log(f"❌ Test file not found: {user_json_path}")
            return False
        
        # Test converter
        self.log("📝 Testing converter...")
        success = self.run_script('convert_content.py', [str(user_json_path)], "test_convert")
        if not success:
            self.log("❌ Converter test failed")
            return False
        
        # Find production JSON
        production_files = list(Path('content/teil1/production-ready').glob('*_production.json'))
        if not production_files:
            self.log("❌ No production JSON found after conversion")
            return False
        
        production_json = production_files[0]
        self.log(f"✅ Found production JSON: {production_json}")
        
        # Test audio generator
        self.log("🎵 Testing audio generator...")
        success = self.run_script('generate_audio.py', [str(production_json)], "test_audio")
        if not success:
            self.log("❌ Audio generator test failed")
            return False
        
        # Test video generator
        self.log("🎬 Testing video generator...")
        success = self.run_script('generate_video.py', [str(production_json)], "test_video")
        if not success:
            self.log("❌ Video generator test failed")
            return False
        
        # Test synchronizer
        self.log("🎊 Testing synchronizer...")
        success = self.run_script('sync_audio_video.py', [str(production_json)], "test_sync")
        if not success:
            self.log("❌ Synchronizer test failed")
            return False
        
        self.log("✅ All component tests passed!")
        return True

async def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Complete Goethe Video Pipeline')
    parser.add_argument('user_json', help='Path to user JSON file')
    parser.add_argument('--output-name', help='Output name (default: derived from input)')
    parser.add_argument('--test-components', action='store_true', 
                       help='Test each component individually')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output from all steps')
    parser.add_argument('--check-prereqs', action='store_true',
                       help='Only check prerequisites, don\'t run pipeline')
    
    args = parser.parse_args()
    
    pipeline = CompletePipeline(verbose=args.verbose)
    
    if args.check_prereqs:
        success = pipeline.check_prerequisites()
        sys.exit(0 if success else 1)
    
    if args.test_components:
        success = pipeline.test_individual_components(args.user_json)
    else:
        success = await pipeline.run_complete_pipeline(args.user_json, args.output_name)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())