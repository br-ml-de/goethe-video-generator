#!/usr/bin/env python3
"""
Synchronize audio with video to create final educational content.
Combines silent video with timed German audio sequence.
"""

import json
import sys
import subprocess
import tempfile
from pathlib import Path
from pydub import AudioSegment
import argparse

class AudioVideoSynchronizer:
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
            print("❌ FFmpeg not found. Please install FFmpeg:")
            print("   macOS: brew install ffmpeg")
            print("   Ubuntu: sudo apt install ffmpeg")
            print("   Windows: Download from https://ffmpeg.org/")
            return False
    
    def create_master_audio_track(self, audio_dir, audio_sequence):
        """
        Create a single master audio track from individual MP3 files.
        
        Args:
            audio_dir: Directory containing individual audio files
            audio_sequence: Audio sequence data with timing
            
        Returns:
            Path to master audio file
        """
        print("🎵 Creating master audio track...")
        
        # Start with silence
        master_audio = AudioSegment.silent(duration=0)
        current_time = 0.0
        
        for i, step in enumerate(audio_sequence['sequence'], 1):
            step_type = step['type']
            step_start = step.get('start_time', current_time)
            
            print(f"   Step {i}: {step_type} at {step_start:.1f}s")
            
            # Add silence to reach the correct start time if needed
            if step_start > current_time:
                silence_duration = (step_start - current_time) * 1000  # Convert to ms
                master_audio += AudioSegment.silent(duration=int(silence_duration))
                current_time = step_start
            
            # Load and add the audio file
            if step_type == 'intro':
                audio_file = audio_dir / 'intro.mp3'
            elif step_type == 'instructions':
                audio_file = audio_dir / 'instructions.mp3'
            elif step_type == 'text':
                audio_file = audio_dir / f'text_{step["number"]}.mp3'
            elif step_type == 'question':
                audio_file = audio_dir / f'question_{step["number"]}.mp3'
            elif step_type == 'outro':
                audio_file = audio_dir / 'outro.mp3'
            else:
                print(f"   ⚠️  Unknown step type: {step_type}")
                continue

            
            if audio_file.exists():
                try:
                    audio_segment = AudioSegment.from_mp3(audio_file)
                    
                    # For text steps, play twice with pause
                    if step_type == 'text':
                        pause_between = step.get('pause_between', 3.0) * 1000  # Convert to ms
                        # First play
                        master_audio += audio_segment
                        # Pause
                        master_audio += AudioSegment.silent(duration=int(pause_between))
                        # Second play
                        master_audio += audio_segment
                        
                        duration = len(audio_segment) * 2 + pause_between
                    else:
                        # Single play for intro, instructions, questions, outro
                        master_audio += audio_segment
                        duration = len(audio_segment)
                    
                    current_time += duration / 1000.0  # Convert back to seconds
                    
                    # Add thinking time for questions
                    if step_type == 'question':
                        thinking_time = step.get('thinking_time', 0) * 1000  # Convert to ms
                        if thinking_time > 0:
                            master_audio += AudioSegment.silent(duration=int(thinking_time))
                            current_time += thinking_time / 1000.0
                    
                except Exception as e:
                    print(f"   ❌ Error loading audio file {audio_file}: {e}")
                    continue
            else:
                print(f"   ❌ Audio file not found: {audio_file}")
                continue
        
        # Save master audio track
        master_audio_path = tempfile.NamedTemporaryFile(
            suffix='.wav', delete=False
        )
        master_audio_path.close()
        
        master_audio_file = Path(master_audio_path.name)
        self.temp_files.append(master_audio_file)
        
        print(f"💾 Exporting master audio ({len(master_audio)/1000:.1f}s)...")
        master_audio.export(str(master_audio_file), format="wav")
        
        print(f"✅ Master audio created: {master_audio_file}")
        print(f"📊 Duration: {len(master_audio)/1000:.1f} seconds")
        
        return master_audio_file
    
    def combine_audio_video(self, video_path, audio_path, output_path):
        """
        Combine video and audio using FFmpeg.
        
        Args:
            video_path: Path to silent video file
            audio_path: Path to master audio file
            output_path: Path for final output video
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🎬 Combining audio and video...")
        print(f"📹 Video: {video_path}")
        print(f"🎵 Audio: {audio_path}")
        print(f"🎯 Output: {output_path}")
        
        # FFmpeg command to combine audio and video
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'libx264',          # ← Re-encode to H.264
            '-c:a', 'aac',
            '-preset', 'medium',        # ← Add encoding settings
            '-crf', '23',               # ← Quality setting
            '-shortest',
            '-y',
            str(output_path)
        ]
        
        print("🔧 Running FFmpeg command...")
        print(f"   {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Audio-video combination successful!")
                return True
            else:
                print("❌ FFmpeg failed:")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running FFmpeg: {e}")
            return False
    
    def sync_audio_video(self, production_json_path, video_path=None, output_path=None):
        """
        Main function to synchronize audio with video.
        
        Args:
            production_json_path: Path to production JSON file
            video_path: Optional custom video path
            output_path: Optional custom output path
            
        Returns:
            Path to final video file if successful, None otherwise
        """
        print("🎬 Audio-Video Synchronization")
        print("=" * 50)
        
        production_json_path = Path(production_json_path)
        
        # Determine audio directory
        base_name = production_json_path.stem
        audio_dir = Path('output/audio') / base_name
        
        if not audio_dir.exists():
            print(f"❌ Audio directory not found: {audio_dir}")
            return None
        
        # Load audio sequence
        audio_sequence_path = audio_dir / 'audio_sequence.json'
        if not audio_sequence_path.exists():
            print(f"❌ Audio sequence not found: {audio_sequence_path}")
            return None
        
        try:
            with open(audio_sequence_path, 'r', encoding='utf-8') as f:
                audio_sequence = json.load(f)
            print(f"✅ Audio sequence loaded ({len(audio_sequence['sequence'])} steps)")
        except Exception as e:
            print(f"❌ Error loading audio sequence: {e}")
            return None
        
        # Determine video path
        if video_path is None:
            video_path = Path('output/videos') / f"{base_name.replace('_production', '')}.webm"
        else:
            video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            print("💡 Run generate_video.py first!")
            return None
        
        print(f"📹 Using video: {video_path}")
        
        # Determine output path
        if output_path is None:
            output_dir = Path('output/final')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{base_name.replace('_production', '')}_final.mp4"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check FFmpeg availability
        if not self.check_ffmpeg():
            return None
        
        try:
            # Create master audio track
            master_audio_path = self.create_master_audio_track(audio_dir, audio_sequence)
            
            # Combine audio and video
            success = self.combine_audio_video(video_path, master_audio_path, output_path)
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n🎉 Final video created successfully!")
                print(f"📁 Location: {output_path}")
                print(f"📊 File size: {file_size:.1f} MB")
                print(f"🎬 Ready for YouTube upload!")
                return output_path
            else:
                print(f"\n❌ Final video creation failed!")
                return None
                
        except Exception as e:
            print(f"\n💥 Synchronization failed: {e}")
            return None
        
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Synchronize audio with video')
    parser.add_argument('production_json', help='Path to production JSON file')
    parser.add_argument('--video', help='Path to video file (optional)')
    parser.add_argument('--output', help='Output path for final video (optional)')
    parser.add_argument('--check-only', action='store_true', help='Only check if files exist')
    
    args = parser.parse_args()
    
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
        
        # Check audio directory
        audio_dir = Path('output/audio') / base_name
        if audio_dir.exists():
            print(f"✅ Audio directory: {audio_dir}")
            
            # Check audio files
            audio_files = list(audio_dir.glob('*.mp3'))
            print(f"   📁 Found {len(audio_files)} MP3 files")
            
            sequence_file = audio_dir / 'audio_sequence.json'
            if sequence_file.exists():
                print(f"✅ Audio sequence: {sequence_file}")
            else:
                print(f"❌ Audio sequence: {sequence_file}")
        else:
            print(f"❌ Audio directory: {audio_dir}")
        
        # Check video file
        video_path = Path('output/videos') / f"{base_name.replace('_production', '')}.webm"
        if video_path.exists():
            print(f"✅ Video file: {video_path}")
        else:
            print(f"❌ Video file: {video_path}")
        
        return True
    
    # Run synchronization
    synchronizer = AudioVideoSynchronizer()
    
    try:
        final_video = synchronizer.sync_audio_video(
            production_json_path=args.production_json,
            video_path=args.video,
            output_path=args.output
        )
        
        if final_video:
            print("\n🎊 Success! Your German listening exercise video is ready!")
            sys.exit(0)
        else:
            print("\n💥 Synchronization failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Synchronization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()