#!/usr/bin/env python3
"""
Main pipeline: User JSON → Production JSON → Audio → Video
Complete automation for Goethe video generation.
"""

import sys
import subprocess
import asyncio
from pathlib import Path
import tempfile
import argparse
from datetime import datetime

class GoetheVideoPipeline:
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent
    
    def run_script(self, script_name, args):
        """Run a script with arguments and handle errors"""
        script_path = self.scripts_dir / script_name
        cmd = [sys.executable, str(script_path)] + args
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running {script_name}:")
            print(f"Exit code: {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    async def process_single_file(self, user_json_path, template_path=None):
        """Process a single user JSON file through the complete pipeline"""
        
        user_json_path = Path(user_json_path)
        
        if not user_json_path.exists():
            print(f"❌ Input file not found: {user_json_path}")
            return False
        
        print(f"📝 Processing: {user_json_path}")
        print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Step 1: Convert user JSON to production JSON
        print("\n" + "="*50)
        print("STEP 1: Converting user JSON to production format")
        print("="*50)
        
        if not self.run_script('convert_content.py', [str(user_json_path)]):
            return False
        
        # Determine production JSON path
        production_json_path = str(user_json_path).replace('_user.json', '_production.json')
        production_json_path = production_json_path.replace('user-submissions', 'production-ready')
        
        if not Path(production_json_path).exists():
            print(f"❌ Production JSON not created: {production_json_path}")
            return False
        
        # Step 2: Generate audio files
        print("\n" + "="*50)
        print("STEP 2: Generating audio files with Amazon Polly")
        print("="*50)
        
        if not self.run_script('generate_audio.py', [production_json_path]):
            return False
        
        # Step 3: Generate video
        print("\n" + "="*50)
        print("STEP 3: Recording video with Playwright")
        print("="*50)
        
        video_args = [production_json_path]
        if template_path:
            video_args.append(str(template_path))
        
        # Use asyncio to run the video generator
        from generate_video import VideoGenerator
        generator = VideoGenerator()
        
        base_name = Path(production_json_path).stem
        audio_dir = Path('output/audio') / base_name
        
        try:
            video_path = await generator.record_video(production_json_path, audio_dir, template_path)
            if video_path:
                print(f"✅ Pipeline complete! Video: {video_path}")
                return True
            else:
                print("❌ Video generation failed")
                return False
        except Exception as e:
            print(f"❌ Video generation error: {e}")
            return False
    
    def process_batch(self, input_dir, template_path=None):
        """Process all user JSON files in a directory"""
        
        input_dir = Path(input_dir)
        user_files = list(input_dir.glob("*_user.json"))
        
        if not user_files:
            print(f"❌ No user JSON files found in: {input_dir}")
            return False
        
        print(f"📁 Found {len(user_files)} files to process")
        
        successful = 0
        failed = 0
        
        for user_file in sorted(user_files):
            print(f"\n{'🎯' * 20}")
            print(f"Processing {user_file.name} ({user_files.index(user_file) + 1}/{len(user_files)})")
            print(f"{'🎯' * 20}")
            
            if asyncio.run(self.process_single_file(user_file, template_path)):
                successful += 1
                print(f"✅ SUCCESS: {user_file.name}")
            else:
                failed += 1
                print(f"❌ FAILED: {user_file.name}")
        
        print(f"\n{'🏁' * 20}")
        print(f"BATCH COMPLETE: {successful} successful, {failed} failed")
        print(f"{'🏁' * 20}")
        
        return failed == 0
    
    def setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            'content/teil1/user-submissions',
            'content/teil1/production-ready',
            'output/audio',
            'output/videos',
            'templates'
        ]
        
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        print("📁 Directory structure created")

async def main():
    parser = argparse.ArgumentParser(description='Goethe Video Generation Pipeline')
    parser.add_argument('input', help='Input user JSON file or directory')
    parser.add_argument('--template', help='HTML template path (optional)')
    parser.add_argument('--batch', action='store_true', help='Process all files in directory')
    parser.add_argument('--setup', action='store_true', help='Setup directory structure only')
    
    args = parser.parse_args()
    
    pipeline = GoetheVideoPipeline()
    
    if args.setup:
        pipeline.setup_directories()
        return
    
    if args.batch:
        success = pipeline.process_batch(args.input, args.template)
    else:
        success = await pipeline.process_single_file(args.input, args.template)
    
    if success:
        print("\n🎉 All processing completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())