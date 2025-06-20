# Automated Video Generator - Complete README

An open-source application that transforms text articles and news content into professional videos with AI-powered narration and automatic slide generation.

## Features

- **Advanced Text-to-Speech**: Uses Coqui XTTS v2 for natural-sounding voice synthesis
- **Voice Cloning**: Clone any voice with just 6 seconds of audio sample
- **Automatic Content Processing**: Intelligent article extraction and slide generation
- **Professional Video Output**: MP4 videos with smooth transitions and professional styling
- **Web Interface**: Easy-to-use web application
- **Multiple Input Methods**: Text input, URL scraping, or file upload
- **Multi-language Support**: 17+ languages including English, Spanish, French, German, etc.

## Technology Stack

### Backend
- **Flask** - Web framework
- **Coqui XTTS v2** - Text-to-speech and voice cloning
- **MoviePy** - Video processing and composition
- **Newspaper3k** - Web scraping and article extraction
- **BeautifulSoup4** - HTML parsing and content extraction
- **NLTK/spaCy** - Natural language processing
- **Pillow** - Image generation and processing

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript** - Interactive user interface
- **Font Awesome** - Icons and visual elements

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for video processing)
- Git

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/automated-video-generator.git
cd automated-video-generator
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install additional models**
```bash
# Download spaCy model for NLP
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

5. **Install FFmpeg**

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Deployment

### Deploy to Render (Recommended - Free)

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com)
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment: Python 3

3. **Add environment variables** (if needed):
   - `PYTHON_VERSION`: `3.11.0`
   - `SECRET_KEY`: Your secret key

4. **Deploy** - Render will automatically build and deploy your application

### Deploy to Railway

1. **Fork this repository**

2. **Deploy to Railway**:
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2Fyourusername%2Fautomated-video-generator)

3. **Configure environment variables** as needed

### Deploy to Heroku

1. **Install Heroku CLI** and login
```bash
heroku login
```

2. **Create Heroku app**
```bash
heroku create your-app-name
```

3. **Add buildpacks**
```bash
heroku buildpacks:add --index 1 heroku/python
heroku buildpacks:add --index 2 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
```

4. **Deploy**
```bash
git push heroku main
```

### Deploy to DigitalOcean App Platform

1. **Create new app** on DigitalOcean
2. **Connect GitHub repository**
3. **Configure build and run commands**:
   - Build: `pip install -r requirements.txt`
   - Run: `gunicorn app:app`

## Configuration

Edit `config.yaml` to customize:

```yaml
# Video settings
video:
  width: 1920
  height: 1080
  fps: 24

# Slide settings
slides:
  max_slides: 8
  words_per_slide: 50

# TTS settings
tts:
  model: "xtts_v2"
  language: "en"
```

## Usage

### Web Interface

1. **Open the application** in your browser
2. **Choose input method**:
   - **Text Tab**: Paste article text directly
   - **URL Tab**: Enter article URL for automatic extraction
   - **Voice Tab**: Upload audio sample for voice cloning (optional)

3. **Configure settings**:
   - Select language
   - Adjust slide count and content density
   
4. **Generate video**:
   - Click "Generate Video"
   - Monitor progress through the pipeline
   - Download completed MP4 video

### API Usage

The application provides REST API endpoints:

```python
import requests

# Generate video from text
response = requests.post('http://localhost:5000/api/generate_video', 
    json={
        'text': 'Your article text here...',
        'title': 'Video Title',
        'language': 'en'
    }
)

job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:5000/api/job_status/{job_id}')

# Download video when complete
video = requests.get(f'http://localhost:5000/api/download/{job_id}')
```

## Performance Optimization

### For Better Performance:

1. **Use GPU acceleration** (if available):
   - Install CUDA-compatible PyTorch
   - The application will automatically use GPU for TTS

2. **Increase memory** for hosting:
   - Minimum 2GB RAM recommended
   - 4GB+ for optimal performance

3. **Configure caching**:
   - Enable file system caching for models
   - Use Redis for session storage (optional)

## Troubleshooting

### Common Issues:

**"FFmpeg not found"**
- Install FFmpeg and ensure it's in your PATH
- On Render/Heroku, use appropriate buildpacks

**"CUDA out of memory"**
- Reduce batch size in config
- Use CPU-only mode: `device: "cpu"` in config

**"TTS model download fails"**
- Check internet connection
- Manually download models to `models/` directory

**"Voice cloning not working"**
- Ensure audio sample is 6+ seconds
- Use high-quality audio (WAV/FLAC preferred)
- Check microphone quality

### Getting Help:

1. **Check logs** in the application or hosting platform
2. **Review configuration** in `config.yaml`
3. **Open an issue** on GitHub with error details

## Contributing

We welcome contributions! Please:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make changes** and test thoroughly
4. **Submit a pull request** with detailed description

### Development Guidelines:

- Follow Python PEP 8 style guide
- Add tests for new features
- Update documentation
- Ensure cross-platform compatibility

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Coqui AI** - For the excellent XTTS TTS models
- **MoviePy** - For powerful video processing capabilities
- **Newspaper3k** - For robust article extraction
- **Flask** - For the web framework
- **Open Source Community** - For making this possible

## Roadmap

### Upcoming Features:
- [ ] Multiple voice options per video
- [ ] Background music integration
- [ ] Advanced video templates
- [ ] Batch processing for multiple articles
- [ ] Integration with content management systems
- [ ] Mobile app version
- [ ] Cloud storage integration

### Performance Improvements:
- [ ] Distributed processing
- [ ] Advanced caching mechanisms
- [ ] WebRTC for real-time preview
- [ ] Progressive video generation

---

**Built with ❤️ by the open source community**

For support, please open an issue or join our community discussions.