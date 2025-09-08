#!/usr/bin/env python3
"""Simple WebM to MP4 converter for synchronized videos"""

import subprocess
import sys
from pathlib import Path

def convert_webm_to_mp4(webm_path, mp4_path=None):
    webm_path = Path(webm_path)
    
    if mp4_path is None:
        mp4_path = webm_path.with_suffix('.mp4')
    else:
        mp4_path = Path(mp4_path)
    
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'ffmpeg', '-i', str(webm_path),
        '-c:v', 'libx264', '-c:a', 'aac',
        '-y', str(mp4_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Converted: {mp4_path}")
            return True
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_to_mp4.py <webm_file>")
        sys.exit(1)
    
    convert_webm_to_mp4(sys.argv[1])