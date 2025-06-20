# Automated Video Generator - Main Flask Application
# Open Source Alternative to Commercial Video Generation Services

from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime
import yaml
import threading
import json

# Import our custom modules
from modules.voice_synthesizer import VoiceSynthesizer
from modules.content_processor import ContentProcessor
from modules.image_generator import ImageGenerator
from modules.video_generator import VideoGenerator
from modules.news_scraper import NewsScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure directories exist
os.makedirs('temp', exist_ok=True)
os.makedirs('output', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize modules
voice_synthesizer = VoiceSynthesizer(config)
content_processor = ContentProcessor(config)
image_generator = ImageGenerator(config)
video_generator = VideoGenerator(config)
news_scraper = NewsScraper(config)

# Store generation jobs
generation_jobs = {}

@app.route('/')
def index():
    """Main page for the video generator"""
    return render_template('index.html')

@app.route('/api/generate_video', methods=['POST'])
def generate_video():
    """Generate video from text content or URL"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or ('text' not in data and 'url' not in data):
            return jsonify({'error': 'Text content or URL required'}), 400
        
        # Generate unique job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(data))}"
        
        # Start generation in background thread
        thread = threading.Thread(
            target=generate_video_async,
            args=(job_id, data)
        )
        thread.start()
        
        # Store job info
        generation_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting video generation...',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Video generation started'
        })
        
    except Exception as e:
        logger.error(f"Error starting video generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_video_async(job_id, data):
    """Async video generation process"""
    try:
        # Update job status
        generation_jobs[job_id]['status'] = 'processing'
        generation_jobs[job_id]['progress'] = 10
        generation_jobs[job_id]['message'] = 'Processing content...'
        
        # Extract content
        if 'url' in data:
            content = news_scraper.extract_article(data['url'])
        else:
            content = {
                'title': data.get('title', 'Generated Video'),
                'text': data['text'],
                'author': data.get('author', ''),
                'publish_date': data.get('publish_date', ''),
                'top_image': data.get('image_url', '')
            }
        
        generation_jobs[job_id]['progress'] = 30
        generation_jobs[job_id]['message'] = 'Processing text content...'
        
        # Process content into slides
        slides = content_processor.create_slides(content)
        
        generation_jobs[job_id]['progress'] = 50
        generation_jobs[job_id]['message'] = 'Generating audio narration...'
        
        # Generate voice narration
        voice_sample = data.get('voice_sample')
        audio_path = voice_synthesizer.generate_speech(
            content['text'], 
            voice_sample=voice_sample,
            output_path=f"temp/{job_id}_audio.wav"
        )
        
        generation_jobs[job_id]['progress'] = 70
        generation_jobs[job_id]['message'] = 'Creating visual slides...'
        
        # Generate images for slides
        image_paths = []
        for i, slide in enumerate(slides):
            img_path = image_generator.create_slide_image(
                slide, 
                output_path=f"temp/{job_id}_slide_{i}.png"
            )
            image_paths.append(img_path)
        
        generation_jobs[job_id]['progress'] = 90
        generation_jobs[job_id]['message'] = 'Composing final video...'
        
        # Generate final video
        output_path = f"output/{job_id}_video.mp4"
        video_generator.create_video(
            image_paths=image_paths,
            audio_path=audio_path,
            output_path=output_path,
            slides_data=slides
        )
        
        # Update job completion
        generation_jobs[job_id]['status'] = 'completed'
        generation_jobs[job_id]['progress'] = 100
        generation_jobs[job_id]['message'] = 'Video generation completed!'
        generation_jobs[job_id]['output_path'] = output_path
        generation_jobs[job_id]['download_url'] = url_for('download_video', job_id=job_id)
        
        # Clean up temporary files
        cleanup_temp_files(job_id)
        
    except Exception as e:
        logger.error(f"Error in video generation for job {job_id}: {str(e)}")
        generation_jobs[job_id]['status'] = 'error'
        generation_jobs[job_id]['message'] = f'Error: {str(e)}'

@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    """Get status of a generation job"""
    if job_id not in generation_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(generation_jobs[job_id])

@app.route('/api/download/<job_id>')
def download_video(job_id):
    """Download generated video"""
    if job_id not in generation_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = generation_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Video not ready'}), 400
    
    output_path = job['output_path']
    if not os.path.exists(output_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    return send_file(output_path, as_attachment=True, download_name=f"{job_id}.mp4")

@app.route('/api/voice_clone', methods=['POST'])
def voice_clone():
    """Clone voice from uploaded audio sample"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = f"voice_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = os.path.join('temp', filename)
        audio_file.save(audio_path)
        
        # Test voice cloning
        test_text = "This is a test of the voice cloning capability."
        cloned_audio_path = voice_synthesizer.clone_voice(
            audio_path, 
            test_text,
            output_path=f"temp/test_clone_{filename}"
        )
        
        return jsonify({
            'success': True,
            'voice_sample_path': audio_path,
            'test_audio_url': url_for('serve_temp_file', filename=os.path.basename(cloned_audio_path))
        })
        
    except Exception as e:
        logger.error(f"Error in voice cloning: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/temp/<filename>')
def serve_temp_file(filename):
    """Serve temporary files"""
    return send_file(os.path.join('temp', filename))

@app.route('/api/scrape_article', methods=['POST'])
def scrape_article():
    """Preview article content from URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL required'}), 400
        
        article = news_scraper.extract_article(data['url'])
        return jsonify({
            'title': article.get('title', ''),
            'text': article.get('text', '')[:500] + '...',  # Preview first 500 chars
            'author': article.get('author', ''),
            'publish_date': article.get('publish_date', ''),
            'top_image': article.get('top_image', '')
        })
        
    except Exception as e:
        logger.error(f"Error scraping article: {str(e)}")
        return jsonify({'error': str(e)}), 500

def cleanup_temp_files(job_id):
    """Clean up temporary files for a job"""
    try:
        temp_dir = Path('temp')
        for file in temp_dir.glob(f"{job_id}_*"):
            file.unlink()
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)