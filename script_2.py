# Create the lightweight TTS module
lightweight_tts_content = '''"""
Lightweight Text-to-Speech module using gTTS (Google Text-to-Speech)
This avoids the heavy dependencies and deployment issues of Coqui TTS
"""

import os
import logging
from gtts import gTTS
import tempfile
import time

logger = logging.getLogger(__name__)

class LightweightTTS:
    def __init__(self):
        """Initialize the lightweight TTS processor"""
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese'
        }
        
    def generate_speech(self, text, language='en', output_file=None, slow=False):
        """
        Generate speech from text using Google TTS
        
        Args:
            text (str): Text to convert to speech
            language (str): Language code (e.g., 'en', 'es', 'fr')
            output_file (str): Output file path
            slow (bool): Whether to use slow speech
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            if not text.strip():
                raise ValueError("Text cannot be empty")
                
            # Validate language
            if language not in self.supported_languages:
                logger.warning(f"Language '{language}' not supported, using English")
                language = 'en'
                
            # Create output filename if not provided
            if not output_file:
                timestamp = int(time.time())
                output_file = f"tts_output_{timestamp}.mp3"
                
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # Save to file
            tts.save(output_file)
            
            logger.info(f"Generated speech for {len(text)} characters in {language}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise
            
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages
        
    def estimate_duration(self, text, language='en'):
        """
        Estimate audio duration in seconds
        Average speaking rate is about 150-160 words per minute
        """
        words = len(text.split())
        # Approximate duration in seconds (150 words per minute)
        duration = (words / 150) * 60
        return max(duration, 1.0)  # Minimum 1 second
'''

# Create the modules directory
os.makedirs('modules', exist_ok=True)

# Save the lightweight TTS module
with open('modules/lightweight_tts.py', 'w') as f:
    f.write(lightweight_tts_content)

# Create __init__.py for the modules package
with open('modules/__init__.py', 'w') as f:
    f.write('# Modules package\n')

print("✅ Created lightweight TTS module using gTTS")
print("- No heavy dependencies")
print("- Works reliably on cloud platforms")
print("- Supports 10+ languages")
print("- Quick deployment")