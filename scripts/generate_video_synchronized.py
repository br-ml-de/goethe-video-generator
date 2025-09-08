#!/usr/bin/env python3
"""
Timing-Calibrated Video Generator with Multi-Layer Drift Correction
Measures browser performance and applies real-time timing corrections.
"""

import asyncio
import json
import sys
import os
import tempfile
import shutil
import time
import yaml
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright
import argparse

class TimingCalibratedVideoGenerator:
    def __init__(self):
        self.video_config = {
            'width': 1280,
            'height': 720,
            'frame_rate': 30
        }
        self.temp_files = []
        self.start_time = None
        self.sync_tolerance = 0.02  # Very tight tolerance for calibrated system
        
        # Timing calibration data
        self.browser_lag_baseline = 0.0
        self.cumulative_drift = 0.0
        self.timing_measurements = []
        self.calibration_samples = 10
        
        # Configuration will be loaded per Teil
        self.config = None
        self.timing_config = None
        self.visual_config = None
    
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
        self.visual_config = self.config.get('visual', {})
        
        print(f"Timing calibration mode enabled")
    
    def _get_default_config(self):
        """Fallback configuration if YAML files not available"""
        return {
            'visual': {
                'base_template': 'teil1_base.html',
                'default_theme': 'energetic',
                'show_progress_bar': True,
                'transition_animations': True
            }
        }
    
    def get_template_path(self, teil: int, theme: str = None):
        """Get template path based on Teil and theme"""
        if theme is None:
            theme = self.visual_config.get('default_theme', 'energetic')
        
        # Check for themed template first
        themed_template = Path(f'templates/themed/teil{teil}_{theme}.html')
        if themed_template.exists():
            return themed_template
        
        # Check for base template
        base_template = Path(f'templates/base/teil{teil}_base.html')
        if base_template.exists():
            return base_template
        
        # Fallback templates
        fallback_templates = [
            Path(f'templates/base/teil{teil}_flexible.html'),
            Path('templates/base/teil1_base.html'),
            Path('templates/base/teil1_flexible.html')
        ]
        
        for template in fallback_templates:
            if template.exists():
                return template
        
        raise FileNotFoundError(f"No suitable template found for Teil {teil}")
    
    def process_template(self, template_path, json_data, theme=None):
        """Process HTML template with JSON data and theme support"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
            
            print(f"Processing template: {template_path}")
            
            # Basic template replacements
            replacements = {
                '{{exam_info.title}}': json_data['exam_info']['title'],
                '{{instructions.main}}': json_data['instructions']['main'],
                '{{instructions.task}}': json_data['instructions']['task'],
                '{{instructions.repetition}}': json_data['instructions']['repetition'],
                '{{channel_name}}': json_data.get('channel_name', 'Zielort Deutschland')
            }
            
            # Theme-specific replacements
            if theme:
                replacements['{{theme_class}}'] = f'theme-{theme}'
                replacements['{{theme_name}}'] = theme
            else:
                replacements['{{theme_class}}'] = 'theme-default'
                replacements['{{theme_name}}'] = 'default'
            
            # Apply all replacements
            processed_html = template_html
            for placeholder, value in replacements.items():
                processed_html = processed_html.replace(placeholder, str(value))
            
            print("Template processed successfully")
            return processed_html
            
        except Exception as e:
            print(f"Error processing template: {e}")
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
    
    def get_current_time(self):
        """Get current time relative to video start"""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    async def calibrate_browser_timing(self, page):
        """
        Measure browser execution lag with calibrated test sequence.
        Returns average lag that should be compensated for.
        """
        print(f"Calibrating browser timing with {self.calibration_samples} samples...")
        
        lag_measurements = []
        test_intervals = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]  # Various timing intervals
        
        calibration_start = time.time()
        
        for i, target_interval in enumerate(test_intervals):
            # Wait for target interval and measure actual time
            interval_start = time.time()
            await asyncio.sleep(target_interval)
            actual_interval = time.time() - interval_start
            
            lag = actual_interval - target_interval
            lag_measurements.append(lag)
            
            print(f"   Sample {i+1}: target={target_interval:.3f}s, actual={actual_interval:.3f}s, lag={lag:+.3f}s")
        
        # Calculate statistics
        avg_lag = sum(lag_measurements) / len(lag_measurements)
        max_lag = max(lag_measurements)
        min_lag = min(lag_measurements)
        
        # Store baseline lag for compensation
        self.browser_lag_baseline = avg_lag
        
        calibration_duration = time.time() - calibration_start
        
        print(f"Browser timing calibration complete:")
        print(f"   Average lag: {avg_lag:+.3f}s")
        print(f"   Range: {min_lag:+.3f}s to {max_lag:+.3f}s")
        print(f"   Calibration time: {calibration_duration:.1f}s")
        
        # Determine if browser timing is stable enough
        lag_variance = max_lag - min_lag
        if lag_variance > 0.1:  # More than 100ms variance
            print(f"   Warning: High timing variance ({lag_variance:.3f}s) detected")
            print(f"   Video timing may be less reliable")
        else:
            print(f"   Timing stability: Good ({lag_variance:.3f}s variance)")
        
        return avg_lag
    
    async def wait_until_calibrated_time(self, target_time):
        """
        Wait until specific time with lag compensation and drift correction.
        """
        # Apply calibration corrections
        compensated_target = target_time - self.browser_lag_baseline - self.cumulative_drift
        
        while True:
            current_time = self.get_current_time()
            if current_time >= compensated_target - self.sync_tolerance:
                break
            
            # More aggressive sleeping for tighter sync
            sleep_time = min(0.01, max(0.002, (compensated_target - current_time) / 4))
            await asyncio.sleep(sleep_time)
    
    def track_timing_drift(self, expected_time, step_index):
        """
        Track cumulative timing drift and adjust future steps.
        """
        actual_time = self.get_current_time()
        step_error = actual_time - expected_time
        
        # Update cumulative drift (weighted average)
        if len(self.timing_measurements) == 0:
            self.cumulative_drift = step_error
        else:
            # Weight recent measurements more heavily
            weight = 0.3
            self.cumulative_drift = (1 - weight) * self.cumulative_drift + weight * step_error
        
        self.timing_measurements.append({
            'step': step_index,
            'expected': expected_time,
            'actual': actual_time,
            'error': step_error,
            'cumulative_drift': self.cumulative_drift
        })
        
        return step_error
    
    async def execute_calibrated_step(self, page, step, step_index):
        """Execute visual step with timing calibration and drift tracking"""
        
        step_type = step['type']
        step_start = step['start_time']
        
        print(f"      Calibrated step: {step_type} at {step_start:.3f}s")
        
        # Wait for calibrated timing
        await self.wait_until_calibrated_time(step_start)
        
        # Track timing accuracy
        timing_error = self.track_timing_drift(step_start, step_index)
        
        actual_time = self.get_current_time()
        print(f"        Target: {step_start:.3f}s, Actual: {actual_time:.3f}s")
        print(f"        Error: {timing_error:+.3f}s, Drift: {self.cumulative_drift:+.3f}s")
        
        try:
            # Execute the visual step
            if step_type == 'intro':
                await page.evaluate("window.showIntro && window.showIntro()")
                
            elif step_type == 'instructions':
                await page.evaluate("window.showInstructions && window.showInstructions()")
                
            elif step_type == 'transition':
                transition_text = step.get('transition_text', 'Übergang')
                escaped_text = transition_text.replace("'", "\\'").replace('"', '\\"')
                await page.evaluate(f"window.showTransition && window.showTransition('{escaped_text}')")
                
            elif step_type == 'combined_task':
                task_number = step['task_number']
                await page.evaluate(f"window.showCombinedTask && window.showCombinedTask({task_number})")
                
            elif step_type == 'answer_reveal':
                task_number = step['task_number']
                correct_answer = step['correct_answer']
                answer_text = step['answer_text'].replace("'", "\\'").replace('"', '\\"')
                await page.evaluate(f"window.showAnswerReveal && window.showAnswerReveal({task_number}, '{correct_answer}', '{answer_text}')")
                
            elif step_type == 'outro':
                await page.evaluate("window.showOutro && window.showOutro()")
                
            else:
                print(f"        Unknown step type: {step_type}")
                
        except Exception as e:
            print(f"        Error executing step {step_type}: {e}")
    
    def get_video_duration(self, video_path):
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return None
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return None
    
    def validate_recording_timing(self, video_path, expected_duration, tolerance=1.0):
        """
        Validate that recorded video duration matches expected duration.
        Returns (is_valid, actual_duration, speed_correction_factor)
        """
        actual_duration = self.get_video_duration(video_path)
        
        if actual_duration is None:
            return False, None, None
        
        duration_error = actual_duration - expected_duration
        
        print(f"Recording validation:")
        print(f"   Expected: {expected_duration:.2f}s")
        print(f"   Actual: {actual_duration:.2f}s")
        print(f"   Error: {duration_error:+.2f}s")
        
        is_valid = abs(duration_error) <= tolerance
        speed_correction = expected_duration / actual_duration if actual_duration > 0 else None
        
        if is_valid:
            print(f"   Status: VALID (within {tolerance}s tolerance)")
        else:
            print(f"   Status: INVALID (exceeds {tolerance}s tolerance)")
            if speed_correction:
                print(f"   Speed correction needed: {speed_correction:.4f}x")
        
        return is_valid, actual_duration, speed_correction
    
    def apply_speed_correction(self, input_video, output_video, speed_factor):
        """Apply speed correction to video using ffmpeg"""
        print(f"Applying speed correction: {speed_factor:.4f}x")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_video),
            '-filter:v', f'setpts={1/speed_factor:.6f}*PTS',
            '-an',  # Remove audio (video should be silent anyway)
            '-y',
            str(output_video)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Speed correction applied successfully")
                return True
            else:
                print(f"Speed correction failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error applying speed correction: {e}")
            return False
    
    async def execute_calibrated_sequence(self, page, audio_sequence):
        """Execute video sequence with full timing calibration and drift correction"""
        
        print(f"Starting calibrated video sequence")
        print(f"Total duration: {audio_sequence['total_duration']:.2f}s")
        print(f"Audio steps: {len(audio_sequence['sequence'])}")
        
        # Calibrate browser timing first
        await self.calibrate_browser_timing(page)
        
        # Record start time AFTER calibration
        self.start_time = time.time()
        total_expected_duration = audio_sequence['total_duration']
        
        # Reset drift tracking
        self.cumulative_drift = 0.0
        self.timing_measurements = []
        
        # Inject audio sequence data into page
        await page.evaluate(f"""
            window.audioSequence = {json.dumps(audio_sequence)};
            console.log('Calibrated mode: Audio sequence loaded');
        """)
        
        # Execute each step with calibration and drift correction
        for i, step in enumerate(audio_sequence['sequence'], 1):
            step_type = step['type']
            step_start = step['start_time']
            step_duration = step.get('total_duration', step.get('duration', 0))
            step_id = step.get('id', f"{step_type}_{i}")
            
            print(f"   Step {i}/{len(audio_sequence['sequence'])}: {step_id} ({step_type})")
            
            await self.execute_calibrated_step(page, step, i)
            
            # Minimal delay for visual completion
            await asyncio.sleep(0.005)
        
        # Wait for sequence completion with drift compensation
        final_target = total_expected_duration - self.browser_lag_baseline - self.cumulative_drift
        
        while self.get_current_time() < final_target:
            await asyncio.sleep(0.01)
        
        final_time = self.get_current_time()
        total_error = final_time - total_expected_duration
        
        print(f"Calibrated sequence complete!")
        print(f"Expected: {total_expected_duration:.2f}s, Actual: {final_time:.2f}s")
        print(f"Total timing error: {total_error:+.3f}s")
        print(f"Final cumulative drift: {self.cumulative_drift:+.3f}s")
        
        # Final completion
        await page.evaluate("window.showCompletion && window.showCompletion()")
        await asyncio.sleep(0.5)
    
    def print_timing_analysis(self):
        """Print detailed timing analysis from the recording"""
        if not self.timing_measurements:
            return
        
        print(f"\nTiming Analysis ({len(self.timing_measurements)} measurements):")
        print(f"{'Step':<4} {'Expected':<9} {'Actual':<9} {'Error':<9} {'Drift':<9}")
        print("-" * 45)
        
        for measurement in self.timing_measurements:
            print(f"{measurement['step']:<4} "
                  f"{measurement['expected']:<9.3f} "
                  f"{measurement['actual']:<9.3f} "
                  f"{measurement['error']:+9.3f} "
                  f"{measurement['cumulative_drift']:+9.3f}")
        
        # Calculate statistics
        errors = [m['error'] for m in self.timing_measurements]
        avg_error = sum(errors) / len(errors)
        max_error = max(errors)
        min_error = min(errors)
        
        print("-" * 45)
        print(f"Average error: {avg_error:+.3f}s")
        print(f"Error range: {min_error:+.3f}s to {max_error:+.3f}s")
        print(f"Browser lag compensation: {self.browser_lag_baseline:+.3f}s")
    
    async def record_calibrated_video(self, production_json_path, audio_dir, template_path=None, theme=None, output_path=None):
        """Record video with full timing calibration system"""
        
        print(f"Starting calibrated video recording...")
        print(f"Production JSON: {production_json_path}")
        print(f"Audio directory: {audio_dir}")
        
        # Load production JSON
        try:
            with open(production_json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            teil = json_data['exam_info']['teil']
            print(f"Teil: {teil}")
        except Exception as e:
            print(f"Error loading production JSON: {e}")
            return None
        
        # Load Teil-specific configuration
        self.load_teil_config(teil)
        
        # Load audio sequence
        audio_sequence_path = Path(audio_dir) / 'audio_sequence.json'
        try:
            with open(audio_sequence_path, 'r', encoding='utf-8') as f:
                audio_sequence = json.load(f)
            print(f"Audio sequence loaded: {len(audio_sequence['sequence'])} steps")
            print(f"Expected duration: {audio_sequence['total_duration']:.2f}s")
        except Exception as e:
            print(f"Error loading audio sequence: {e}")
            return None
        
        # Template processing
        if template_path is None:
            template_path = self.get_template_path(teil, theme)
        
        if theme is None:
            theme = self.visual_config.get('default_theme', 'energetic')
        
        print(f"Using template: {template_path}")
        print(f"Using theme: {theme}")
        
        try:
            processed_html = self.process_template(template_path, json_data, theme)
            temp_html_path = self.create_temp_html(processed_html)
        except Exception as e:
            print(f"Template processing failed: {e}")
            return None
        
        
        # Determine output path
        if output_path is None:
            output_dir = Path('output/videos')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            base_name = Path(production_json_path).stem.replace('_production', '')
            output_path = output_dir / f"{base_name}_calibrated.webm"
        else:
            # Use the provided output path
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)



        print(f"Output video: {output_path}")
        
        try:
            async with async_playwright() as p:
                print("Launching browser for calibrated recording...")
                
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--enable-font-antialiasing',
                        '--force-device-scale-factor=1'
                    ]
                )
                
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
                
                # Load HTML
                file_url = f'file://{temp_html_path.absolute()}'
                await page.goto(file_url, wait_until='domcontentloaded')
                await page.wait_for_function("document.readyState === 'complete'")
                await asyncio.sleep(1.0)  # Page initialization
                
                # Execute calibrated sequence
                await self.execute_calibrated_sequence(page, audio_sequence)
                
                # Close and process video
                await context.close()
                await browser.close()
                
                # Find recorded video
                recorded_files = list(output_path.parent.glob("*.webm"))
                if recorded_files:
                    latest_video = max(recorded_files, key=lambda x: x.stat().st_mtime)
                    
                    if latest_video != output_path:
                        shutil.move(str(latest_video), str(output_path))
                    
                    # Validate timing and apply correction if needed
                    is_valid, actual_duration, speed_factor = self.validate_recording_timing(
                        output_path, audio_sequence['total_duration'], tolerance=0.5
                    )
                    
                    if not is_valid and speed_factor:
                        corrected_path = output_path.with_suffix('.corrected.webm')
                        if self.apply_speed_correction(output_path, corrected_path, speed_factor):
                            # Replace original with corrected version
                            shutil.move(str(corrected_path), str(output_path))
                            print("Speed correction applied to final video")
                    
                    file_size = output_path.stat().st_size / (1024*1024)
                    print(f"Calibrated video recording complete: {output_path}")
                    print(f"File size: {file_size:.1f} MB")
                    
                    # Print timing analysis
                    self.print_timing_analysis()
                    
                    return output_path
                else:
                    print("No video file found after recording")
                    return None
        
        except Exception as e:
            print(f"Calibrated video recording failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            self.cleanup_temp_files()

async def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Generate timing-calibrated synchronized video')
    parser.add_argument('production_json', help='Path to production JSON file')
    parser.add_argument('--template', help='Path to HTML template')
    parser.add_argument('--theme', help='Theme to use')
    parser.add_argument('--output', help='Output video path')  

    parser.add_argument('--audio-dir', help='Audio directory')
    parser.add_argument('--test-calibration', action='store_true', help='Test calibration only')
    
    args = parser.parse_args()
    
    production_json_path = Path(args.production_json)
    
    if not production_json_path.exists():
        print(f"Production JSON not found: {production_json_path}")
        sys.exit(1)
    
    # Determine audio directory
    if args.audio_dir:
        audio_dir = Path(args.audio_dir)
    else:
        base_name = production_json_path.stem
        audio_dir = Path('output/audio') / base_name
    
    if not audio_dir.exists():
        print(f"Audio directory not found: {audio_dir}")
        sys.exit(1)
    
    print("Timing-Calibrated Video Generator")
    print("=" * 50)
    
    generator = TimingCalibratedVideoGenerator()
    
    try:
        video_path = await generator.record_calibrated_video(
            production_json_path=production_json_path,
            audio_dir=audio_dir,
            template_path=args.template,
            theme=args.theme,
            output_path=args.output
        )
        
        if video_path:
            print("\nCalibrated video generation successful!")
            print(f"Output: {video_path}")
            print("Timing: Calibrated with drift correction")
            print("Next: Run sync_audio_video.py for final MP4")
        else:
            print("\nCalibrated video generation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nVideo generation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())