# Create the updated main application file
app_content = '''import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
import tempfile
import shutil
from datetime import datetime
import threading
import time

# Import our lightweight modules
from modules.lightweight_tts import LightweightTTS
from modules.simple_video_generator import SimpleVideoGenerator
from modules.content_processor import ContentProcessor
from modules.news_scraper import NewsScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize processors
tts_processor = LightweightTTS()
video_generator = SimpleVideoGenerator()
content_processor = ContentProcessor()
news_scraper = NewsScraper()

# Global variable to track processing status
processing_status = {}

@app.route('/')
def index():
    """Main page with the video generation interface"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_video():
    """Generate video from text or URL"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Generate unique job ID
        job_id = f"job_{int(time.time())}"
        processing_status[job_id] = {'status': 'starting', 'progress': 0}
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_video_generation,
            args=(job_id, data)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id, 'status': 'started'})
        
    except Exception as e:
        logger.error(f"Error starting video generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_video_generation(job_id, data):
    """Background process for video generation"""
    try:
        processing_status[job_id] = {'status': 'processing', 'progress': 10}
        
        # Extract content based on input type
        if data.get('input_type') == 'url':
            url = data.get('url')
            if not url:
                raise ValueError("URL is required")
            
            processing_status[job_id] = {'status': 'processing', 'progress': 20, 'message': 'Scraping content...'}
            content_data = news_scraper.extract_article(url)
            
        elif data.get('input_type') == 'text':
            text = data.get('text')
            if not text:
                raise ValueError("Text is required")
                
            content_data = {
                'title': data.get('title', 'Generated Video'),
                'content': text,
                'summary': text[:200] + '...' if len(text) > 200 else text
            }
        else:
            raise ValueError("Invalid input type")
            
        processing_status[job_id] = {'status': 'processing', 'progress': 40, 'message': 'Processing content...'}
        
        # Process content into slides
        slides = content_processor.create_slides(content_data)
        
        processing_status[job_id] = {'status': 'processing', 'progress': 60, 'message': 'Generating speech...'}
        
        # Generate TTS audio
        audio_files = []
        for i, slide in enumerate(slides):
            audio_file = tts_processor.generate_speech(
                slide['text'], 
                language=data.get('language', 'en'),
                output_file=f"temp_audio_{job_id}_{i}.mp3"
            )
            audio_files.append(audio_file)
            
        processing_status[job_id] = {'status': 'processing', 'progress': 80, 'message': 'Creating video...'}
        
        # Generate video
        video_file = video_generator.create_video(
            slides=slides,
            audio_files=audio_files,
            output_file=f"output_{job_id}.mp4"
        )
        
        processing_status[job_id] = {
            'status': 'completed', 
            'progress': 100, 
            'message': 'Video generated successfully!',
            'video_file': video_file
        }
        
    except Exception as e:
        logger.error(f"Error in video generation {job_id}: {str(e)}")
        processing_status[job_id] = {
            'status': 'error', 
            'progress': 0, 
            'message': str(e)
        }

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get processing status for a job"""
    status = processing_status.get(job_id, {'status': 'not_found'})
    return jsonify(status)

@app.route('/api/download/<job_id>')
def download_video(job_id):
    """Download the generated video"""
    status = processing_status.get(job_id, {})
    
    if status.get('status') != 'completed':
        return jsonify({'error': 'Video not ready'}), 404
        
    video_file = status.get('video_file')
    if not video_file or not os.path.exists(video_file):
        return jsonify({'error': 'Video file not found'}), 404
        
    return send_file(
        video_file,
        as_attachment=True,
        download_name=f'generated_video_{job_id}.mp4',
        mimetype='video/mp4'
    )

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# Cleanup old files periodically
def cleanup_old_files():
    """Clean up old temporary files"""
    try:
        current_time = time.time()
        for filename in os.listdir('.'):
            if filename.startswith(('temp_', 'output_')) and filename.endswith(('.mp3', '.mp4')):
                file_path = os.path.join('.', filename)
                if os.path.getmtime(file_path) < current_time - 3600:  # 1 hour old
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")

# Schedule cleanup every hour
def start_cleanup_scheduler():
    def scheduler():
        while True:
            time.sleep(3600)  # 1 hour
            cleanup_old_files()
    
    cleanup_thread = threading.Thread(target=scheduler)
    cleanup_thread.daemon = True
    cleanup_thread.start()

if __name__ == '__main__':
    start_cleanup_scheduler()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''

# Save the main application file
with open('app.py', 'w') as f:
    f.write(app_content)

print("✅ Updated app.py created with lightweight dependencies")
print("Key improvements:")
print("- Replaced heavy Coqui TTS with lightweight gTTS")
print("- Removed MoviePy dependency (causes deployment issues)")
print("- Added proper error handling and background processing")
print("- Optimized for Render deployment")