# Modules package for Automated Video Generator
# Contains all core processing modules

__version__ = "1.0.0"
__author__ = "Open Source Community"

# Import main classes for easy access
from .voice_synthesizer import VoiceSynthesizer
from .content_processor import ContentProcessor
from .image_generator import ImageGenerator
from .video_generator import VideoGenerator
from .news_scraper import NewsScraper

__all__ = [
    'VoiceSynthesizer',
    'ContentProcessor', 
    'ImageGenerator',
    'VideoGenerator',
    'NewsScraper'
]