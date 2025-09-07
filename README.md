# Goethe Video Generator

🎬 Automated video generation for German A2 listening exercises using Amazon Polly and Playwright.

## Quick Start

```bash
# 1. Setup
python scripts/setup.py
aws configure

# 2. Test
python scripts/convert_content.py content/teil1/user-submissions/test_user_input.json

# 3. Generate video (when ready)
python scripts/main_pipeline.py content/teil1/user-submissions/your_file.json
```

## What This Does

Transforms simple German text into professional educational videos:
- **Input**: User-friendly JSON with German texts and questions
- **Output**: 10-12 minute HD video with synchronized German audio
- **Quality**: Professional exam preparation content for YouTube

## Project Status

- ✅ **Phase 1**: Content converter (user JSON → production JSON)
- 🚧 **Phase 2**: Audio generation (Amazon Polly)
- ⏳ **Phase 3**: Video recording (Playwright)
- ⏳ **Phase 4**: Complete pipeline

## Documentation

- 📋 **[Complete Setup Guide](docs/SETUP.md)** - Full installation instructions
- 👥 **[Content Creator Guide](docs/CONTENT_CREATOR_GUIDE.md)** - For content creators
- 🔧 **[Technical Documentation](docs/TECHNICAL_GUIDE.md)** - Architecture and details
- 🆘 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and fixes

## Project Structure

```
├── scripts/                    # Python processing scripts
│   ├── convert_content.py     # User JSON → Production JSON
│   ├── generate_audio.py      # Amazon Polly audio generation
│   ├── generate_video.py      # Playwright video recording
│   └── main_pipeline.py       # Complete automation
├── templates/
│   ├── content-creator/       # Templates for content creators
│   └── styles/               # HTML video templates
├── content/
│   ├── teil1/user-submissions/    # User-created content
│   └── teil1/production-ready/    # Auto-generated production files
├── output/
│   ├── audio/                # Generated MP3 files
│   └── videos/               # Final video files
└── docs/                     # Documentation
```

## Technology Stack

- **Python 3.8+** - Core processing
- **Amazon Polly** - German text-to-speech
- **Playwright** - Browser-based video recording
- **HTML/CSS** - Video template rendering

## Goals

Create 40+ professional German A2 listening videos for YouTube channel growth from 6 to 1,000+ subscribers.

## Contributing

See [Content Creator Guide](docs/CONTENT_CREATOR_GUIDE.md) for content creation workflow.

## License

Private project for educational content creation.