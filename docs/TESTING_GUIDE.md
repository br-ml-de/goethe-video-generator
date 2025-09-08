# Testing Guide - Progressive Component Development

This guide documents the step-by-step testing approach for building each component of the Goethe Video Generator.

## 🎯 **Testing Philosophy**

Build and test one component at a time to ensure solid foundations before adding complexity.

**Order**: Converter → Audio Generator → Video Recorder → Complete Pipeline

---

## 📦 **Component 1: Content Converter**

### **Goal**: Convert user-friendly JSON to production-ready JSON format

### **Dependencies Needed**
```bash
# Only built-in Python libraries needed:
# - json (built-in)
# - sys (built-in) 
# - pathlib (built-in)
# - datetime (built-in)

# No additional pip installs required!
```

### **Files to Create**
```bash
scripts/convert_content.py              # Main converter script
tests/test_converter.py                 # Unit tests
content/teil1/user-submissions/test_user_input.json  # Test data
```

### **Testing Steps**

#### **1. Manual Test (2 minutes)**
```bash
# Activate environment
source venv/bin/activate

# Test conversion
python scripts/convert_content.py content/teil1/user-submissions/test_user_input.json

# Verify output
ls content/teil1/production-ready/
cat content/teil1/production-ready/test_user_input_production.json
```

#### **2. Unit Tests (2 minutes)**
```bash
# Run comprehensive test suite
python tests/test_converter.py

# Should see: ✅ All tests passed!
```

#### **3. Success Criteria**
- [ ] No error messages during conversion
- [ ] Production JSON file created in correct location
- [ ] Production file has all required fields (`exam_info`, `instructions`, `sections`, `content`, `questions`, `solutions`)
- [ ] Content properly transformed from simple to detailed format
- [ ] All unit tests pass
- [ ] Audio duration calculations work correctly

#### **4. Troubleshooting**
```bash
# If manual test fails:
python --version                        # Check Python version (3.6+)
python -m py_compile scripts/convert_content.py  # Check syntax

# If unit tests fail:
python -c "import sys; sys.path.insert(0, 'scripts'); import convert_content; print('✅ Import works')"
```

---

## 🎵 **Component 2: Audio Generator**

### Quick test with intro and outros
# 1. Verify your audio files are in place
ls -la assets/standard-audio/
# Should show: intro.mp3 and outro.mp3

# 2. Test audio generation with intro/outro
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

# 3. Check the generated audio sequence
ls -la output/audio/test_user_input_production/
# Should now show: intro.mp3, instructions.mp3, text_1.mp3, ..., question_5.mp3, outro.mp3

# 4. Check the timing in the sequence file
cat output/audio/test_user_input_production/audio_sequence.json
# Should show intro at 0.0s, then content, then outro at the end

# 5. Verify total duration increased
# Look for: "Total duration: XXX seconds" (should be ~30s longer than before)







### **Goal**: Generate German speech audio using Amazon Polly

### **Dependencies Needed**
```bash
pip install boto3 pydub
```

### **Prerequisites**
- [ ] Component 1 (Converter) working
- [ ] AWS credentials configured (`aws configure`)
- [ ] Amazon Polly access in us-east-1 region

### **Files to Create**
```bash
scripts/generate_audio.py               # Audio generation script
tests/test_audio_generator.py           # Unit tests for audio
config/polly_config.json               # Polly configuration
```

### **Testing Steps**

#### **1. AWS Connection Test**
```bash
# 1. Test AWS credentials exist
aws sts get-caller-identity

# Test Polly access
python -c "import boto3; client = boto3.client('polly', region_name='us-east-1'); print('✅ AWS connection works')"

# Test from Python
python -c "import boto3; client = boto3.client('polly', region_name='us-east-1'); print('✅ Polly client created')"

# Test AWS connection with listing voices 
python -c "import boto3; boto3.client('polly', region_name='us-east-1').describe_voices(LanguageCode='de-DE'); print('✅ AWS works')"

# 4. If all pass, move to Phase 3

# Move to Phase 3 (if AWS works)
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

# List available German voices
aws polly describe-voices --language-code de-DE
```

#### **2. Manual Audio Test**
```bash
# Generate audio from existing production JSON
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

# Verify audio files created
ls output/audio/test_user_input/
```

#### **3. Audio Quality Test**
```bash
# Play audio files to verify quality
# Instructions: [instructions.mp3]
# Text 1: [text_1.mp3] 
# Question 1: [question_1.mp3]
# etc.

# On Mac:
afplay output/audio/test_user_input_production/text_1.mp3

# On Linux with audio:
# mpg123 output/audio/test_user_input_production/text_1.mp3

# Check the audio sequence timing:
cat output/audio/test_user_input_production/audio_sequence.json

```

#### **4. Success Criteria**
- [ ] 13 audio files generated (1 instructions + 5 texts + 5 questions + 2 extras)
- [ ] Audio files are clear German speech
- [ ] Different voices used appropriately
- [ ] `audio_sequence.json` created with timing data
- [ ] Total duration matches expectations (~10-12 minutes)
- [ ] No Polly API errors

---

## 🎬 **Component 3: Video Generator**
### Prereqs for testing
# 1. Install Playwright
pip install playwright

# 2. Install Chromium browser
playwright install chromium

# 3. Verify template is saved
ls templates/styles/teil1_test.html  # Should exist

# 4. Verify audio files exist
ls output/audio/test_user_input_production/  # Should have MP3s + JSON


### Basic Test: 
# Generate video with your working data
python scripts/generate_video.py content/teil1/production-ready/test_user_input_production.json

# Expected output:
# 🎬 Starting video recording...
# 📄 Production JSON: [path]
# 🎵 Audio directory: [path]
# ✅ Production JSON loaded
# ✅ Audio sequence loaded (13 steps)
# 🎨 Using template: templates/styles/teil1_test.html
# 📝 Temporary HTML created: [temp]
# 🚀 Launching browser...
# 📂 Loading HTML: [file URL]
# ✅ Page loaded and ready
# 🎬 Executing video sequence (13 steps)
# [... step by step progress ...]
# ✅ Video recording complete: output/videos/test_user_input.webm




### Full test 
### **Goal**: Record synchronized video using Playwright browser automation


### **Dependencies Needed**
```bash
pip install playwright
playwright install chromium
```

### **Prerequisites**
- [ ] Component 1 & 2 working
- [ ] HTML template created
- [ ] Audio files generated

### **Files to Create**
```bash
scripts/generate_video.py               # Video recording script
tests/test_video_generator.py           # Unit tests
templates/styles/teil1_current.html     # HTML video template
```

### **Testing Steps**

#### **1. Playwright Installation Test**
```bash
# Verify Playwright works
python -c "import playwright; print('✅ Playwright imported')"
playwright --version
```







#### **2. Template Processing Test**
```bash
# Test HTML template processing
python -c "
from scripts.generate_video import VideoGenerator
import json
with open('content/teil1/production-ready/test_user_input_production.json') as f:
    data = json.load(f)
generator = VideoGenerator()
html = generator.process_template('templates/styles/teil1_current.html', data)
print('✅ Template processing works')
"
```

#### **3. Video Recording Test**
```bash
# Generate complete video
python scripts/generate_video.py content/teil1/production-ready/test_user_input_production.json

# Verify video created
ls output/videos/
```

#### **4. Success Criteria**
- [ ] Video file created (`.webm` format)
- [ ] Video duration matches audio sequence
- [ ] Visual transitions synchronized with audio timing
- [ ] All content sections visible
- [ ] Questions and options clearly readable
- [ ] Video quality HD (1280x720)

---

## 🔄 **Component 4: Complete Pipeline**
# Step 1: Convert user JSON to production JSON (with gender enhancement)
python scripts/convert_content.py content/teil1/test-content/test_user_input.json

# Step 2: Generate audio with smart voice distribution
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

# Step 3: Generate synchronized video
python scripts/generate_video_synchronized.py content/teil1/production-ready/test_user_input_production.json

# or as a one-liner
python scripts/convert_content.py content/teil1/test-content/test_user_input.json && \
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json && \
python scripts/generate_video_synchronized.py content/teil1/production-ready/test_user_input_production.json && \
echo "🎉 Complete Pipeline Success!"



# Make sure everything is set up correctly
python scripts/synchronized_pipeline.py --check-prereqs

# Test if synchronization components work
python scripts/synchronized_pipeline.py content/teil1/test-content/test_user_input.json --test-sync --verbose

# Generate video with detailed timing output
python scripts/generate_video_synchronized.py content/teil1/production-ready/test_user_input_production.json --verbose

# Complete pipeline: User JSON → Final MP4
python scripts/synchronized_pipeline.py content/teil1/test-content/test_user_input.json --verbose

### Prereqs
# 1. Install FFmpeg (required for audio-video combination)
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt install ffmpeg

# Windows: Download from https://ffmpeg.org/

# 2. Verify FFmpeg installation
ffmpeg -version

### Testing synchronization
# 1. Check that all required files exist
python scripts/sync_audio_video.py content/teil1/production-ready/test_user_input_production.json --check-only

# Should show:
# ✅ Production JSON: [path]
# ✅ Audio directory: [path]
# ✅ Audio sequence: [path]
# ✅ Video file: [path]

# 2. Create the final synchronized video
python scripts/sync_audio_video.py content/teil1/production-ready/test_user_input_production.json

# Expected output:
# 🎵 Creating master audio track...
# 💾 Exporting master audio (187.3s)...
# ✅ Master audio created
# 🎬 Combining audio and video...
# 🔧 Running FFmpeg command...
# ✅ Audio-video combination successful!
# 🎉 Final video created successfully!
# 📁 Location: output/final/test_user_input_final.mp4


### **Goal**: End-to-end automation from user JSON to final video

### **Dependencies**
- [ ] All previous components working
- [ ] All scripts integrated

### **Files to Create**
```bash
scripts/main_pipeline.py                # Complete orchestration
tests/test_complete_pipeline.py         # End-to-end tests
```

### **Testing Steps**

# 1. Save the complete pipeline script (if you haven't already)
# Copy complete_pipeline_script artifact → scripts/complete_pipeline.py

# 2. Run the full integration test
python scripts/complete_pipeline.py content/teil1/user-submissions/test_user_input.json --verbose

# Complete Pipeline Test
# 1. Clean previous output (optional)
rm -rf output/audio/test_user_input_production/
rm -rf output/videos/test_user_input*
rm -rf output/final/test_user_input*

# 2. Convert user content to production format
python scripts/convert_content.py content/teil1/test-content/test_user_input.json

# 3. Generate audio with 5s thinking time + 2s buffers
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

# 4. Generate silent video with synchronized timing
python scripts/generate_video_synchronized.py content/teil1/production-ready/test_user_input_production.json

# 5. Create final MP4 with synchronized audio
python scripts/sync_audio_video.py content/teil1/production-ready/test_user_input_production.json


# Synchronzied Pipeline
# Run the complete pipeline
python scripts/synchronized_pipeline.py content/teil1/test-content/test_user_input.json

# Or with verbose output to see everything
python scripts/synchronized_pipeline.py content/teil1/test-content/test_user_input.json --verbose





#### **1. Single File Pipeline Test**
```bash
# Complete end-to-end test
python scripts/main_pipeline.py content/teil1/user-submissions/test_user_input.json

# Should produce:
# - Production JSON
# - Audio files
# - Final video
```

#### **2. Batch Processing Test**
```bash
# Create multiple test files
cp content/teil1/user-submissions/test_user_input.json content/teil1/user-submissions/test_2.json
cp content/teil1/user-submissions/test_user_input.json content/teil1/user-submissions/test_3.json

# Batch process
python scripts/main_pipeline.py content/teil1/user-submissions/ --batch
```

#### **3. Success Criteria**
- [ ] Complete automation works without manual intervention
- [ ] Error handling and recovery
- [ ] Progress reporting
- [ ] Multiple file processing
- [ ] Clean error messages
- [ ] Consistent output quality

---

## 📊 **Testing Checklist Template**

For each component, use this checklist:

```markdown
## Component: [NAME]
Date: [DATE]
Tester: [YOUR NAME]

### Setup
- [ ] Dependencies installed
- [ ] Files created
- [ ] Prerequisites met

### Manual Testing
- [ ] Basic functionality works
- [ ] No error messages
- [ ] Output files created
- [ ] Output quality acceptable

### Unit Testing
- [ ] All tests pass
- [ ] Edge cases covered
- [ ] Error conditions handled

### Integration
- [ ] Works with previous components
- [ ] No regressions introduced
- [ ] Performance acceptable

### Issues Found
- [ ] [List any issues]
- [ ] [Resolution steps taken]

### Sign-off
- [ ] Component ready for next phase
- [ ] Documentation updated
- [ ] Code committed
```

---

## 🔧 **General Troubleshooting**

### **Common Issues**
# code to regenerate - remove old stuff
rm -rf output/audio/test_user_input_production
python scripts/generate_audio.py content/teil1/production-ready/test_user_input_production.json

### Diagnosing timing 
# Check the audio sequence timing to see where outro is placed
cat output/audio/test_user_input_production/audio_sequence.json | grep -A5 -B5 "outro"

# Check the overall sequence structure
cat output/audio/test_user_input_production/audio_sequence.json | jq '.sequence[] | {type: .type, start_time: .start_time}'

# Regenerate the final video with intro/outro support
python scripts/sync_audio_video.py content/teil1/production-ready/test_user_input_production.json


#### **Import Errors**
```bash
# Add scripts to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"

# Or use absolute imports
python -m scripts.convert_content file.json
```

#### **File Path Issues**
```bash
# Always run from project root
cd goethe-video-generator
python scripts/script_name.py
```

#### **Permission Issues**
```bash
# Make scripts executable
chmod +x scripts/*.py
```

#### **AWS Issues**
```bash
# Verify credentials
aws sts get-caller-identity

# Check region
aws configure get region
```

---

## 📈 **Progress Tracking**

Track your progress through each component:

- [ ] **Phase 1**: Content Converter ✅ Tested & Working
- [ ] **Phase 2**: Audio Generator ⏳ In Progress
- [ ] **Phase 3**: Video Generator ⏳ Not Started  
- [ ] **Phase 4**: Complete Pipeline ⏳ Not Started

---

## 🎯 **Benefits of This Approach**

1. **Solid Foundation**: Each component thoroughly tested before building next
2. **Clear Debugging**: Issues isolated to specific components
3. **Progress Visibility**: Clear milestones and checkpoints
4. **Reproducible**: Documented steps for future reference
5. **Confidence**: Know each piece works before integration

**Follow this guide to build a robust, well-tested video generation system!** 🎬