#!/usr/bin/env python3
"""
Generate video using Playwright browser recording with synchronized audio.
Records HTML template with audio timing for educational content.
"""

import asyncio
import json
import sys
import os
import tempfile
import shutil
from pathlib import Path
from playwright.async_api import async_playwright
import argparse

class VideoGenerator:
    def __init__(self):
        self.video_config = {
            'width': 1280,
            'height': 720,
            'frame_rate': 30
        }
        self.temp_files = []  # Track temp files for cleanup
    
    def process_template(self, template_path, json_data):
        """
        Process HTML template with JSON data using string replacement.
        
        Args:
            template_path: Path to HTML template file
            json_data: Production JSON data
            
        Returns:
            Processed HTML string
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
            
            print(f"📄 Processing template: {template_path}")
            
            # Basic template replacements
            replacements = {
                '{{exam_info.title}}': json_data['exam_info']['title'],
                '{{instructions.main}}': json_data['instructions']['main'],
                '{{instructions.task}}': json_data['instructions']['task'],
                '{{instructions.repetition}}': json_data['instructions']['repetition']
            }
            
            # Replace content (texts)
            for i, content in enumerate(json_data['content'], 1):
                replacements[f'{{{{content.{i}.setup}}}}'] = content.get('setup', '')
                replacements[f'{{{{content.{i}.text}}}}'] = content['text']
                replacements[f'{{{{content.{i}.context}}}}'] = content.get('context', '')
            
            # Replace questions
            for i, question in enumerate(json_data['questions'], 1):
                replacements[f'{{{{question.{i}.question}}}}'] = question['question']
                replacements[f'{{{{question.{i}.options.a}}}}'] = question['options']['a']
                replacements[f'{{{{question.{i}.options.b}}}}'] = question['options']['b']
                replacements[f'{{{{question.{i}.options.c}}}}'] = question['options']['c']
            
            # Apply all replacements
            processed_html = template_html
            for placeholder, value in replacements.items():
                processed_html = processed_html.replace(placeholder, str(value))
            
            # Check for any remaining unreplaced placeholders
            remaining_placeholders = []
            lines = processed_html.split('\n')
            for i, line in enumerate(lines, 1):
                if '{{' in line and '}}' in line:
                    remaining_placeholders.append(f"Line {i}: {line.strip()}")
            
            if remaining_placeholders:
                print("⚠️  Warning: Some placeholders not replaced:")
                for placeholder in remaining_placeholders[:5]:  # Show first 5
                    print(f"   {placeholder}")
                if len(remaining_placeholders) > 5:
                    print(f"   ... and {len(remaining_placeholders) - 5} more")
            else:
                print("✅ All template placeholders processed successfully")
            
            return processed_html
            
        except FileNotFoundError:
            print(f"❌ Template file not found: {template_path}")
            raise
        except Exception as e:
            print(f"❌ Error processing template: {e}")
            raise
    
    def create_temp_html(self, processed_html):
        """Create temporary HTML file and track it for cleanup"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.html', 
            delete=False, 
            encoding='utf-8'
        )
        temp_file.write(processed_html)
        temp_file.close()
        
        temp_path = Path(temp_file.name)
        self.temp_files.append(temp_path)
        return temp_path
    
    def cleanup_temp_files(self):
        """Clean up all temporary files"""
        for temp_file in self.temp_files:
            try:
                temp_file.unlink()
            except FileNotFoundError:
                pass
        self.temp_files.clear()
    
    async def execute_video_sequence(self, page, audio_sequence):
        """
        Execute the synchronized audio/visual sequence.
        
        Args:
            page: Playwright page object
            audio_sequence: Audio sequence data with timing
        """
        print(f"🎬 Executing video sequence ({len(audio_sequence['sequence'])} steps)")
        
        total_duration = 0
        
        for i, step in enumerate(audio_sequence['sequence'], 1):
            step_type = step['type']
            step_duration = step.get('total_duration', step.get('duration', 0))
            
            print(f"   Step {i}/{len(audio_sequence['sequence'])}: {step_type} ({step_duration:.1f}s)")
            
            if step_type == 'instructions':
                await page.evaluate("showInstructions()")
                await asyncio.sleep(step_duration)
                
            elif step_type == 'text':
                text_num = step['number']
                await page.evaluate(f"showText({text_num})")
                
                # Wait for full text duration (includes 2 plays + pause)
                await asyncio.sleep(step_duration)
                
            elif step_type == 'question':
                question_num = step['number']
                await page.evaluate(f"showQuestion({question_num})")
                
                # Wait for question reading + thinking time
                await asyncio.sleep(step_duration)
            
            total_duration += step_duration
        
        # Show completion
        print("   Final step: Completion screen")
        await page.evaluate("showCompletion()")
        await asyncio.sleep(3.0)  # Brief completion screen
        
        total_duration += 3.0
        print(f"✅ Sequence complete! Total duration: {total_duration:.1f}s")
    
    async def record_video(self, production_json_path, audio_dir, template_path=None, output_path=None):
        """
        Record video with synchronized audio timing.
        
        Args:
            production_json_path: Path to production JSON file
            audio_dir: Directory containing audio files and sequence
            template_path: Optional custom template path
            output_path: Optional custom output path
            
        Returns:
            Path to generated video file
        """
        print(f"🎬 Starting video recording...")
        print(f"📄 Production JSON: {production_json_path}")
        print(f"🎵 Audio directory: {audio_dir}")
        
        # Load production JSON
        try:
            with open(production_json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print("✅ Production JSON loaded")
        except Exception as e:
            print(f"❌ Error loading production JSON: {e}")
            return None
        
        # Load audio sequence
        audio_sequence_path = Path(audio_dir) / 'audio_sequence.json'
        try:
            with open(audio_sequence_path, 'r', encoding='utf-8') as f:
                audio_sequence = json.load(f)
            print(f"✅ Audio sequence loaded ({len(audio_sequence['sequence'])} steps)")
        except Exception as e:
            print(f"❌ Error loading audio sequence: {e}")
            return None
        
        # Determine template path
        if template_path is None:
            # Look for test template first, then enhanced, then current
            possible_templates = [
                'templates/styles/teil1_test.html',
                'templates/styles/teil1_enhanced.html', 
                'templates/styles/teil1_current.html'
            ]
            
            template_path = None
            for possible in possible_templates:
                if Path(possible).exists():
                    template_path = Path(possible)
                    break
            
            if template_path is None:
                print(f"❌ No template found in: {possible_templates}")
                return None
        else:
            template_path = Path(template_path)
        
        print(f"🎨 Using template: {template_path}")
        
        if not template_path.exists():
            print(f"❌ Template not found: {template_path}")
            return None
        
        # Process template
        try:
            processed_html = self.process_template(template_path, json_data)
            temp_html_path = self.create_temp_html(processed_html)
            print(f"📝 Temporary HTML created: {temp_html_path}")
        except Exception as e:
            print(f"❌ Template processing failed: {e}")
            return None
        
        # Determine output path
        if output_path is None:
            output_dir = Path('output/videos')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            base_name = Path(production_json_path).stem.replace('_production', '')
            output_path = output_dir / f"{base_name}.webm"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🎯 Output video: {output_path}")
        
        try:
            async with async_playwright() as p:
                print("🚀 Launching browser...")
                
                # Launch browser with specific settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Create context with video recording
                context = await browser.new_context(
                    viewport={
                        'width': self.video_config['width'], 
                        'height': self.video_config['height']
                    },
                    device_scale_factor=1,
                    record_video_dir=str(output_path.parent),
                    record_video_size={
                        'width': self.video_config['width'],
                        'height': self.video_config['height']
                    }
                )
                
                page = await context.new_page()
                
                # Load the processed HTML
                file_url = f'file://{temp_html_path.absolute()}'
                print(f"📂 Loading HTML: {file_url}")
                
                await page.goto(file_url, wait_until='domcontentloaded')
                
                # Wait for page to be fully ready
                await page.wait_for_function("document.readyState === 'complete'")
                await asyncio.sleep(2)  # Additional buffer for CSS/JS initialization
                
                print("✅ Page loaded and ready")
                
                # Execute the video sequence
                await self.execute_video_sequence(page, audio_sequence)
                
                # Close context to finalize video recording
                print("💾 Finalizing video...")
                await context.close()
                await browser.close()
                
                # Find and rename the recorded video
                recorded_files = list(output_path.parent.glob("*.webm"))
                if recorded_files:
                    # Get the most recently created video file
                    latest_video = max(recorded_files, key=lambda x: x.stat().st_mtime)
                    
                    if latest_video != output_path:
                        print(f"📁 Moving video: {latest_video} → {output_path}")
                        shutil.move(str(latest_video), str(output_path))
                    
                    print(f"✅ Video recording complete: {output_path}")
                    print(f"📊 File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
                    return output_path
                else:
                    print("❌ No video file found after recording")
                    return None
        
        except Exception as e:
            print(f"❌ Video recording failed: {e}")
            return None
        
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()

async def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Generate video from production JSON')
    parser.add_argument('production_json', help='Path to production JSON file')
    parser.add_argument('--template', help='Path to HTML template (optional)')
    parser.add_argument('--output', help='Output video path (optional)')
    parser.add_argument('--audio-dir', help='Audio directory (auto-detected if not provided)')
    
    args = parser.parse_args()
    
    production_json_path = Path(args.production_json)
    
    if not production_json_path.exists():
        print(f"❌ Production JSON not found: {production_json_path}")
        sys.exit(1)
    
    # Determine audio directory
    if args.audio_dir:
        audio_dir = Path(args.audio_dir)
    else:
        # Auto-detect from production JSON filename
        base_name = production_json_path.stem
        audio_dir = Path('output/audio') / base_name
    
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        print("💡 Make sure to run generate_audio.py first!")
        sys.exit(1)
    
    # Check for audio sequence file
    sequence_file = audio_dir / 'audio_sequence.json'
    if not sequence_file.exists():
        print(f"❌ Audio sequence file not found: {sequence_file}")
        print("💡 Make sure audio generation completed successfully!")
        sys.exit(1)
    
    print("🎬 Goethe Video Generator")
    print("=" * 50)
    
    generator = VideoGenerator()
    
    try:
        video_path = await generator.record_video(
            production_json_path=production_json_path,
            audio_dir=audio_dir,
            template_path=args.template,
            output_path=args.output
        )
        
        if video_path:
            print("\n🎉 Video generation successful!")
            print(f"📁 Output: {video_path}")
            print(f"🎬 Ready for YouTube upload!")
        else:
            print("\n❌ Video generation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Video generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())