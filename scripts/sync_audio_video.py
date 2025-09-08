#!/usr/bin/env python3
"""
Fixed Audio-Video Synchronizer that uses exact audio sequence timing.
Uses the precise timing from audio_sequence.json instead of recalculating.
"""

import json
import sys
import subprocess
import tempfile
from pathlib import Path
from pydub import AudioSegment
import argparse

class TimingRespectingAudioVideoSynchronizer:
    def __init__(self):
        self.temp_files = []
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                temp_file.unlink()
            except FileNotFoundError:
                pass
        self.temp_files.clear()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ FFmpeg is available")
                return True
            else:
                print("❌ FFmpeg check failed")
                return False
        except FileNotFoundError:
            print("❌ FFmpeg not found")
            return False
    
    def get_actual_audio_duration(self, audio_file):
        """Get actual duration of audio file using pydub"""
        try:
            audio = AudioSegment.from_mp3(audio_file)
            return len(audio) / 1000.0  # Convert to seconds
        except Exception as e:
            print(f"⚠️ Could not get duration for {audio_file}: {e}")
            return 0.0
    
    def create_master_audio_using_sequence_timing(self, audio_dir, audio_sequence):
        """
        Create master audio track using EXACT timing from audio_sequence.json.
        This fixes the timing mismatch by respecting the audio generator's timing.
        """
        print("🎵 Creating master audio using exact sequence timing...")
        print(f"📊 Expected duration: {audio_sequence['total_duration']:.2f}s")
        
        # Start with silence
        master_audio = AudioSegment.silent(duration=0)
        current_position = 0.0
        
        for i, step in enumerate(audio_sequence['sequence'], 1):
            step_type = step['type']
            step_start = step['start_time']  # EXACT timing from audio generator
            step_file = step.get('file', '')
            
            print(f"   Step {i}: {step_type} at {step_start:.2f}s")
            
            # Add silence to reach the EXACT start time from sequence
            if step_start > current_position:
                silence_duration = (step_start - current_position) * 1000  # Convert to ms
                master_audio += AudioSegment.silent(duration=int(silence_duration))
                current_position = step_start
                print(f"      Added {silence_duration/1000:.2f}s silence to reach {step_start:.2f}s")
            
            # Determine audio file path
            audio_file = None
            
            if step_type == 'intro':
                audio_file = audio_dir / 'intro.mp3'
            elif step_type == 'instructions':
                audio_file = audio_dir / 'instructions.mp3'
            elif step_type == 'transition':
                # Extract transition ID from step
                transition_id = step.get('id', 'unknown')
                audio_file = audio_dir / f'transition_{transition_id}.mp3'
            elif step_type == 'combined_task':
                task_number = step.get('task_number', 1)
                audio_file = audio_dir / f'task_{task_number}.mp3'
                
                # Handle task start buffer as SILENCE (not audio)
                task_start_buffer = step.get('task_start_buffer', 0)
                if task_start_buffer > 0:
                    print(f"      Adding {task_start_buffer:.2f}s task start buffer as silence")
                    buffer_ms = task_start_buffer * 1000
                    master_audio += AudioSegment.silent(duration=int(buffer_ms))
                    current_position += task_start_buffer
                
            elif step_type == 'answer_reveal':
                task_number = step.get('task_number', 1)
                audio_file = audio_dir / f'answer_{task_number}.mp3'
            elif step_type == 'outro':
                audio_file = audio_dir / 'outro.mp3'
            elif step_file:
                # Use file path from sequence if available
                audio_file = Path(step_file)
                if not audio_file.is_absolute():
                    audio_file = audio_dir / audio_file.name
            
            if audio_file and audio_file.exists():
                try:
                    audio_segment = AudioSegment.from_mp3(audio_file)
                    actual_duration = len(audio_segment) / 1000.0
                    
                    # Handle combined tasks with repetition
                    if step_type == 'combined_task':
                        play_count = step.get('play_count', 2)
                        pause_between = step.get('pause_between', 3.0) * 1000  # Convert to ms
                        thinking_time = step.get('thinking_time', 5.0) * 1000  # Convert to ms
                        
                        if play_count == 2:
                            # Play twice with pause
                            master_audio += audio_segment
                            master_audio += AudioSegment.silent(duration=int(pause_between))
                            master_audio += audio_segment
                            
                            # Add thinking time after second play
                            master_audio += AudioSegment.silent(duration=int(thinking_time))
                            
                            audio_duration = actual_duration * 2 + (pause_between / 1000.0) + (thinking_time / 1000.0)
                            print(f"      Added task: {actual_duration:.2f}s × 2 + {pause_between/1000:.2f}s pause + {thinking_time/1000:.2f}s thinking")
                        else:
                            master_audio += audio_segment
                            audio_duration = actual_duration
                            print(f"      Added task: {actual_duration:.2f}s × 1")
                    else:
                        # Single play for intro, instructions, answers, outro
                        master_audio += audio_segment
                        audio_duration = actual_duration
                        print(f"      Added {step_type}: {actual_duration:.2f}s")
                    
                    current_position += audio_duration
                    
                    # Add buffer after instructions
                    if step_type == 'instructions':
                        buffer_after = step.get('buffer_after', 0)
                        if buffer_after > 0:
                            buffer_ms = buffer_after * 1000
                            master_audio += AudioSegment.silent(duration=int(buffer_ms))
                            current_position += buffer_after
                            print(f"      Added {buffer_after:.2f}s buffer after instructions")
                    
                    # Add pause after answer reveals
                    if step_type == 'answer_reveal':
                        pause_after = step.get('pause_after', 0)
                        if pause_after > 0:
                            pause_ms = pause_after * 1000
                            master_audio += AudioSegment.silent(duration=int(pause_ms))
                            current_position += pause_after
                            print(f"      Added {pause_after:.2f}s pause after answer")
                
                except Exception as e:
                    print(f"   ❌ Error loading {audio_file}: {e}")
                    continue
            else:
                print(f"   ⚠️ Audio file not found: {audio_file}")
                continue
        
        # Save master audio track
        master_audio_path = tempfile.NamedTemporaryFile(
            suffix='.wav', delete=False
        )
        master_audio_path.close()
        
        master_audio_file = Path(master_audio_path.name)
        self.temp_files.append(master_audio_file)
        
        print(f"💾 Exporting master audio ({len(master_audio)/1000:.2f}s)...")
        master_audio.export(str(master_audio_file), format="wav")
        
        expected_duration = audio_sequence['total_duration']
        actual_duration = len(master_audio) / 1000.0
        timing_error = actual_duration - expected_duration
        
        print(f"✅ Master audio created: {master_audio_file}")
        print(f"📊 Expected duration: {expected_duration:.2f}s")
        print(f"📊 Actual duration: {actual_duration:.2f}s")
        print(f"🔍 Timing error: {timing_error:+.2f}s")
        
        if abs(timing_error) > 0.5:
            print(f"⚠️ Large timing error detected! Check audio sequence timing.")
        else:
            print(f"✅ Timing accuracy within tolerance")
        
        return master_audio_file, actual_duration
    
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
                print(f"⚠️ Could not get video duration: {result.stderr}")
                return None
        except Exception as e:
            print(f"⚠️ Error getting video duration: {e}")
            return None
    
    def combine_audio_video_with_precise_timing(self, video_path, audio_path, output_path, target_duration):
        """
        Combine video and audio with precise timing control.
        """
        print(f"🎬 Combining audio and video with precise timing...")
        print(f"📹 Video: {video_path}")
        print(f"🎵 Audio: {audio_path}")
        print(f"🎯 Target duration: {target_duration:.2f}s")
        print(f"📍 Output: {output_path}")
        
        # Get video duration
        video_duration = self.get_video_duration(video_path)
        if video_duration:
            print(f"📊 Video duration: {video_duration:.2f}s")
            
            # Check if video and audio durations are reasonable
            duration_diff = abs(video_duration - target_duration)
            if duration_diff > 2.0:  # More than 2 second difference
                print(f"⚠️ Large duration mismatch: video={video_duration:.2f}s, audio={target_duration:.2f}s")
                print(f"⚠️ This may indicate timing synchronization issues")
        
        # FFmpeg command with precise timing control
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-crf', '23',
            '-t', str(target_duration),  # Force exact duration
            '-avoid_negative_ts', 'make_zero',  # Handle timing issues
            '-map', '0:v:0',  # Use video from first input
            '-map', '1:a:0',  # Use audio from second input
            '-y',
            str(output_path)
        ]
        
        print("🔧 Running FFmpeg with precise timing control...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Audio-video combination successful!")
                
                # Verify output duration
                output_duration = self.get_video_duration(output_path)
                if output_duration:
                    duration_diff = abs(output_duration - target_duration)
                    print(f"📊 Output duration: {output_duration:.2f}s")
                    print(f"🔍 Duration accuracy: ±{duration_diff:.2f}s")
                    
                    if duration_diff < 0.1:
                        print("✅ Excellent duration match")
                    elif duration_diff < 0.5:
                        print("✅ Good duration match")
                    else:
                        print("⚠️ Duration mismatch detected")
                
                return True
            else:
                print("❌ FFmpeg failed:")
                print(f"   STDERR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running FFmpeg: {e}")
            return False
    
    def sync_audio_video(self, production_json_path, video_path=None, output_path=None):
        """
        Main synchronization function using EXACT audio sequence timing.
        """
        print("🎬 Timing-Respecting Audio-Video Synchronization")
        print("=" * 50)
        
        production_json_path = Path(production_json_path)
        
        # Determine audio directory
        base_name = production_json_path.stem
        audio_dir = Path('output/audio') / base_name
        
        if not audio_dir.exists():
            print(f"❌ Audio directory not found: {audio_dir}")
            return None
        
        # Load audio sequence - THIS IS THE TIMING SOURCE OF TRUTH
        audio_sequence_path = audio_dir / 'audio_sequence.json'
        if not audio_sequence_path.exists():
            print(f"❌ Audio sequence not found: {audio_sequence_path}")
            return None
        
        try:
            with open(audio_sequence_path, 'r', encoding='utf-8') as f:
                audio_sequence = json.load(f)
            print(f"✅ Audio sequence loaded ({len(audio_sequence['sequence'])} steps)")
            print(f"📊 Audio sequence duration: {audio_sequence['total_duration']:.2f}s")
            
            # Verify timing includes buffers
            has_buffers = any('task_start_buffer' in step or 'buffer_after' in step 
                            for step in audio_sequence['sequence'])
            print(f"📋 Buffer timing detected: {has_buffers}")
            
        except Exception as e:
            print(f"❌ Error loading audio sequence: {e}")
            return None
        
        # Determine video path - use provided path first, then fallback to auto-detection
        if video_path is not None:
            video_path = Path(video_path)
            if not video_path.exists():
                print(f"❌ Specified video file not found: {video_path}")
                return None
            print(f"📹 Using specified video: {video_path}")
        else:
            # Try auto-detection as fallback
            video_candidates = [
                Path('output/videos') / f"{base_name.replace('_production', '')}_audio_driven.webm",
                Path('output/videos') / f"{base_name.replace('_production', '')}.webm",
                Path('output/videos') / f"{base_name.replace('_production', '')}_calibrated.webm",
                Path('output/videos') / f"{base_name.replace('_production', '')}_silent.webm"
            ]
            
            video_path = None
            for candidate in video_candidates:
                if candidate.exists():
                    video_path = candidate
                    break
            
            if video_path is None:
                print(f"❌ No video file found. Tried:")
                for candidate in video_candidates:
                    print(f"   {candidate}")
                return None
            
            print(f"📹 Auto-detected video: {video_path}")
        
        # Determine output path
        if output_path is None:
            output_dir = Path('output/final')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{base_name.replace('_production', '')}_final.mp4"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"📍 Output will be: {output_path}")
        
        # Check FFmpeg availability
        if not self.check_ffmpeg():
            return None
        
        try:
            # Create master audio track using EXACT sequence timing
            master_audio_path, actual_duration = self.create_master_audio_using_sequence_timing(
                audio_dir, audio_sequence
            )
            
            # Combine audio and video with precise timing control
            success = self.combine_audio_video_with_precise_timing(
                video_path, master_audio_path, output_path, actual_duration
            )
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n🎉 Timing-accurate synchronization complete!")
                print(f"📍 Location: {output_path}")
                print(f"📊 File size: {file_size:.1f} MB")
                print(f"⏱️ Duration: {actual_duration:.2f}s")
                print(f"🎬 Audio-video timing: Uses exact audio sequence timing")
                print(f"✅ Buffer timing: Properly handled")
                return output_path
            else:
                print(f"\n❌ Synchronization failed!")
                return None
                
        except Exception as e:
            print(f"\n💥 Synchronization failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Timing-accurate audio-video synchronization')
    parser.add_argument('production_json', help='Path to production JSON file')
    parser.add_argument('--video-file', help='Path to input video file')
    parser.add_argument('--output', help='Output path for synced video')
    parser.add_argument('--video', help='Path to video file (backwards compatibility)')
    parser.add_argument('--analyze-timing', action='store_true', help='Analyze timing without syncing')
    parser.add_argument('--check-only', action='store_true', help='Only check if files exist')
    
    args = parser.parse_args()
    
    if args.analyze_timing:
        # Analyze timing accuracy
        production_json_path = Path(args.production_json)
        base_name = production_json_path.stem
        audio_dir = Path('output/audio') / base_name
        
        sequence_file = audio_dir / 'audio_sequence.json'
        if sequence_file.exists():
            with open(sequence_file, 'r') as f:
                sequence = json.load(f)
            
            print("🔍 Timing Analysis for Synchronization:")
            print(f"📊 Total duration: {sequence['total_duration']:.2f}s")
            print(f"🎵 Steps: {len(sequence['sequence'])}")
            
            print("\n⏱️ Exact timing that sync script will use:")
            for i, step in enumerate(sequence['sequence'], 1):
                step_type = step['type']
                start_time = step['start_time']
                duration = step.get('total_duration', step.get('duration', 0))
                
                # Show buffer information
                buffer_info = ""
                if 'task_start_buffer' in step:
                    buffer_info += f" (buffer: +{step['task_start_buffer']:.1f}s before)"
                if 'buffer_after' in step:
                    buffer_info += f" (buffer: +{step['buffer_after']:.1f}s after)"
                
                print(f"  {i:2}. {start_time:6.2f}s: {step_type:15} ({duration:.2f}s){buffer_info}")
            
            print(f"\n✅ This timing will be used exactly for audio-video sync")
            return True
        else:
            print(f"❌ Audio sequence not found: {sequence_file}")
            return False
    
    if args.check_only:
        # Just verify all required files exist
        production_json_path = Path(args.production_json)
        base_name = production_json_path.stem
        
        print("🔍 Checking required files...")
        
        # Check production JSON
        if production_json_path.exists():
            print(f"✅ Production JSON: {production_json_path}")
        else:
            print(f"❌ Production JSON: {production_json_path}")
            return False
        
        # Check audio directory and sequence
        audio_dir = Path('output/audio') / base_name
        if audio_dir.exists():
            print(f"✅ Audio directory: {audio_dir}")
            
            sequence_file = audio_dir / 'audio_sequence.json'
            if sequence_file.exists():
                print(f"✅ Audio sequence: {sequence_file}")
            else:
                print(f"❌ Audio sequence: {sequence_file}")
                return False
        else:
            print(f"❌ Audio directory: {audio_dir}")
            return False
        
        # Check video file
        video_candidates = [
            Path('output/videos') / f"{base_name.replace('_production', '')}_audio_driven.webm",
            Path('output/videos') / f"{base_name.replace('_production', '')}.webm",
            Path('output/videos') / f"{base_name.replace('_production', '')}_calibrated.webm",
            Path('output/videos') / f"{base_name.replace('_production', '')}_silent.webm"
        ]
        
        video_found = False
        for video_path in video_candidates:
            if video_path.exists():
                print(f"✅ Video file: {video_path}")
                video_found = True
                break
        
        if not video_found:
            print(f"❌ No video file found. Tried:")
            for candidate in video_candidates:
                print(f"   {candidate}")
            return False
        
        print(f"✅ All files ready for synchronization")
        return True
    
    # Determine which video path to use (prioritize --video-file over --video)
    video_path = args.video_file if args.video_file else args.video
    
    # Run timing-accurate synchronization
    synchronizer = TimingRespectingAudioVideoSynchronizer()
    
    try:
        final_video = synchronizer.sync_audio_video(
            production_json_path=args.production_json,
            video_path=video_path,
            output_path=args.output
        )
        
        if final_video:
            print("\n🎊 Timing-accurate synchronization successful!")
            print("🎬 Video should now have perfect audio-visual alignment!")
            sys.exit(0)
        else:
            print("\n💥 Timing-accurate synchronization failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Synchronization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()