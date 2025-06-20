# Voice Synthesizer Module - Open Source TTS with Voice Cloning
# Uses Coqui XTTS for natural-sounding speech synthesis

import os
import logging
import torch
import torchaudio
import numpy as np
from pathlib import Path
import tempfile
from typing import Optional, Dict, Any

try:
    from TTS.api import TTS
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
except ImportError:
    print("Warning: Coqui TTS not installed. Install with: pip install coqui-tts")

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """
    Open source voice synthesis using Coqui XTTS v2
    Supports voice cloning with just 6 seconds of audio
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize TTS model
        self.tts_model = None
        self.xtts_model = None
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize TTS models"""
        try:
            logger.info("Initializing Coqui TTS models...")
            
            # Initialize XTTS v2 for voice cloning
            self.tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            
            logger.info(f"TTS models loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing TTS models: {str(e)}")
            # Fallback to system TTS or basic implementation
            self._initialize_fallback_tts()
    
    def _initialize_fallback_tts(self):
        """Initialize fallback TTS using system capabilities"""
        try:
            import pyttsx3
            self.fallback_engine = pyttsx3.init()
            logger.info("Fallback TTS engine initialized")
        except ImportError:
            logger.warning("No TTS engine available. Install coqui-tts or pyttsx3")
            self.fallback_engine = None
    
    def generate_speech(self, text: str, voice_sample: Optional[str] = None, 
                       output_path: str = None, language: str = "en") -> str:
        """
        Generate speech from text with optional voice cloning
        
        Args:
            text: Text to synthesize
            voice_sample: Path to voice sample for cloning (optional)
            output_path: Output audio file path
            language: Language code for synthesis
            
        Returns:
            Path to generated audio file
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix=".wav")
        
        try:
            if self.tts_model and voice_sample and os.path.exists(voice_sample):
                # Use voice cloning
                return self._clone_voice_synthesis(text, voice_sample, output_path, language)
            elif self.tts_model:
                # Use default TTS voice
                return self._default_synthesis(text, output_path, language)
            else:
                # Use fallback TTS
                return self._fallback_synthesis(text, output_path)
                
        except Exception as e:
            logger.error(f"Error in speech generation: {str(e)}")
            return self._fallback_synthesis(text, output_path)
    
    def _clone_voice_synthesis(self, text: str, voice_sample: str, 
                              output_path: str, language: str) -> str:
        """Generate speech using voice cloning"""
        try:
            logger.info(f"Generating speech with voice cloning: {len(text)} characters")
            
            # Split long text into chunks for better processing
            chunks = self._split_text(text, max_length=500)
            audio_segments = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                    
                # Generate audio for chunk
                chunk_output = tempfile.mktemp(suffix=f"_chunk_{i}.wav")
                
                self.tts_model.tts_to_file(
                    text=chunk,
                    speaker_wav=voice_sample,
                    language=language,
                    file_path=chunk_output
                )
                
                # Load and store audio segment
                audio, sr = torchaudio.load(chunk_output)
                audio_segments.append(audio)
                
                # Clean up chunk file
                os.unlink(chunk_output)
            
            # Concatenate all audio segments
            if audio_segments:
                combined_audio = torch.cat(audio_segments, dim=1)
                torchaudio.save(output_path, combined_audio, sr)
            
            logger.info(f"Voice cloning completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in voice cloning: {str(e)}")
            # Fallback to default synthesis
            return self._default_synthesis(text, output_path, language)
    
    def _default_synthesis(self, text: str, output_path: str, language: str) -> str:
        """Generate speech using default TTS voice"""
        try:
            logger.info(f"Generating speech with default voice: {len(text)} characters")
            
            # Use built-in voice from XTTS
            self.tts_model.tts_to_file(
                text=text,
                language=language,
                file_path=output_path
            )
            
            logger.info(f"Default synthesis completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in default synthesis: {str(e)}")
            return self._fallback_synthesis(text, output_path)
    
    def _fallback_synthesis(self, text: str, output_path: str) -> str:
        """Fallback synthesis using system TTS"""
        try:
            if self.fallback_engine:
                logger.info("Using fallback TTS engine")
                
                # Configure voice properties
                voices = self.fallback_engine.getProperty('voices')
                if voices:
                    self.fallback_engine.setProperty('voice', voices[0].id)
                
                self.fallback_engine.setProperty('rate', 150)  # Speech rate
                self.fallback_engine.setProperty('volume', 0.9)  # Volume level
                
                # Save to file
                self.fallback_engine.save_to_file(text, output_path)
                self.fallback_engine.runAndWait()
                
                logger.info(f"Fallback synthesis completed: {output_path}")
                return output_path
            else:
                # Create silent audio as last resort
                return self._create_silent_audio(output_path, duration=5.0)
                
        except Exception as e:
            logger.error(f"Error in fallback synthesis: {str(e)}")
            return self._create_silent_audio(output_path, duration=5.0)
    
    def _create_silent_audio(self, output_path: str, duration: float = 5.0) -> str:
        """Create silent audio file as fallback"""
        try:
            sample_rate = 22050
            samples = int(sample_rate * duration)
            silent_audio = torch.zeros(1, samples)
            torchaudio.save(output_path, silent_audio, sample_rate)
            logger.info(f"Created silent audio: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating silent audio: {str(e)}")
            return output_path
    
    def clone_voice(self, voice_sample_path: str, test_text: str, 
                   output_path: str = None) -> str:
        """
        Test voice cloning with a sample
        
        Args:
            voice_sample_path: Path to voice sample audio
            test_text: Text to synthesize for testing
            output_path: Output path for test audio
            
        Returns:
            Path to generated test audio
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix="_voice_test.wav")
        
        return self.generate_speech(
            text=test_text,
            voice_sample=voice_sample_path,
            output_path=output_path
        )
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio, sr = torchaudio.load(audio_path)
            duration = audio.shape[1] / sr
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0.0
    
    def _split_text(self, text: str, max_length: int = 500) -> list:
        """Split text into chunks for processing"""
        if len(text) <= max_length:
            return [text]
        
        # Split by sentences first
        sentences = text.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        # XTTS v2 supported languages
        return [
            "en",  # English
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "pl",  # Polish
            "tr",  # Turkish
            "ru",  # Russian
            "nl",  # Dutch
            "cs",  # Czech
            "ar",  # Arabic
            "zh-cn",  # Chinese (Simplified)
            "ja",  # Japanese
            "hu",  # Hungarian
            "ko",  # Korean
            "hi"   # Hindi
        ]
    
    def estimate_generation_time(self, text: str) -> float:
        """Estimate time needed for speech generation"""
        # Rough estimate: 1 second per 10-15 words
        word_count = len(text.split())
        estimated_seconds = word_count / 12  # Conservative estimate
        return max(estimated_seconds, 2.0)  # Minimum 2 seconds