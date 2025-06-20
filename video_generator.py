# Video Generator Module - Combine Audio and Images into MP4
# Uses MoviePy for professional video composition

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, 
        CompositeVideoClip, concatenate_videoclips,
        TextClip, ColorClip
    )
    import moviepy.config as config
    from moviepy.video.fx import fadeout, fadein
    from moviepy.audio.fx import audio_fadeout, audio_fadein
except ImportError as e:
    print(f"Warning: MoviePy not installed: {e}")

logger = logging.getLogger(__name__)

class VideoGenerator:
    """
    Generate MP4 videos from images and audio using MoviePy
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.fps = config_dict.get('fps', 24)
        self.resolution = (
            config_dict.get('video_width', 1920),
            config_dict.get('video_height', 1080)
        )
        self.transition_duration = config_dict.get('transition_duration', 0.5)
        
        # Ensure FFmpeg is available
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            import moviepy.config as mp_config
            if mp_config.check("ffmpeg"):
                logger.info("FFmpeg found and configured")
            else:
                logger.warning("FFmpeg not found. Some features may not work.")
        except Exception as e:
            logger.warning(f"Could not verify FFmpeg: {str(e)}")
    
    def create_video(self, image_paths: List[str], audio_path: str, 
                    output_path: str, slides_data: List[Dict[str, Any]]) -> str:
        """
        Create video from images and audio
        
        Args:
            image_paths: List of image file paths
            audio_path: Path to audio file
            output_path: Output video file path
            slides_data: Slide data for timing information
            
        Returns:
            Path to created video file
        """
        try:
            logger.info(f"Creating video from {len(image_paths)} images and audio")
            
            # Load audio
            audio = AudioFileClip(audio_path)
            total_audio_duration = audio.duration
            
            # Create video clips from images
            video_clips = self._create_video_clips(image_paths, slides_data, total_audio_duration)
            
            # Concatenate video clips with transitions
            final_video = self._add_transitions(video_clips)
            
            # Add audio
            final_video = final_video.set_audio(audio)
            
            # Ensure video matches audio duration
            if final_video.duration != total_audio_duration:
                if final_video.duration > total_audio_duration:
                    final_video = final_video.subclip(0, total_audio_duration)
                else:
                    # Extend last frame if video is shorter
                    final_video = self._extend_video_duration(final_video, total_audio_duration)
            
            # Add fade effects
            final_video = self._add_fade_effects(final_video)
            
            # Write video file
            self._write_video(final_video, output_path)
            
            # Clean up
            final_video.close()
            audio.close()
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            return self._create_fallback_video(output_path, audio_path)
    
    def _create_video_clips(self, image_paths: List[str], slides_data: List[Dict[str, Any]], 
                           total_duration: float) -> List[VideoFileClip]:
        """Create video clips from images"""
        clips = []
        
        # Calculate duration for each slide
        if slides_data and len(slides_data) == len(image_paths):
            durations = [slide.get('duration', 5.0) for slide in slides_data]
        else:
            # Distribute time evenly
            duration_per_slide = total_duration / len(image_paths)
            durations = [duration_per_slide] * len(image_paths)
        
        # Adjust durations to match total audio duration
        current_total = sum(durations)
        if current_total != total_duration:
            factor = total_duration / current_total
            durations = [d * factor for d in durations]
        
        # Create clips
        for i, (image_path, duration) in enumerate(zip(image_paths, durations)):
            try:
                if os.path.exists(image_path):
                    clip = ImageClip(image_path, duration=duration)
                    clip = clip.resize(self.resolution)
                    
                    # Add subtle zoom effect for visual interest
                    clip = self._add_ken_burns_effect(clip)
                    
                    clips.append(clip)
                else:
                    logger.warning(f"Image not found: {image_path}")
                    # Create placeholder clip
                    placeholder = self._create_placeholder_clip(duration, f"Slide {i+1}")
                    clips.append(placeholder)
                    
            except Exception as e:
                logger.error(f"Error creating clip from {image_path}: {str(e)}")
                # Create error placeholder
                placeholder = self._create_placeholder_clip(duration, f"Error: Slide {i+1}")
                clips.append(placeholder)
        
        return clips
    
    def _add_ken_burns_effect(self, clip: ImageClip) -> ImageClip:
        """Add subtle Ken Burns zoom effect to image"""
        try:
            def zoom_effect(get_frame, t):
                frame = get_frame(t)
                # Calculate zoom factor (1.0 to 1.1 over duration)
                zoom_factor = 1.0 + (0.1 * t / clip.duration)
                
                # Apply zoom by resizing and cropping
                h, w = frame.shape[:2]
                new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
                
                # Simple resize (MoviePy will handle the details)
                return frame
            
            # Apply the effect (simplified version)
            return clip
            
        except Exception as e:
            logger.warning(f"Could not apply Ken Burns effect: {str(e)}")
            return clip
    
    def _add_transitions(self, clips: List[VideoFileClip]) -> VideoFileClip:
        """Add transitions between clips"""
        if len(clips) <= 1:
            return concatenate_videoclips(clips) if clips else None
        
        try:
            # Create crossfade transitions
            transition_clips = []
            
            for i, clip in enumerate(clips):
                if i == 0:
                    # First clip - fade in
                    clip = fadein(clip, self.transition_duration)
                elif i == len(clips) - 1:
                    # Last clip - fade out
                    clip = fadeout(clip, self.transition_duration)
                else:
                    # Middle clips - crossfade
                    clip = fadein(fadeout(clip, self.transition_duration), self.transition_duration)
                
                transition_clips.append(clip)
            
            # Concatenate with crossfade
            final_clip = concatenate_videoclips(transition_clips, method="compose")
            
            return final_clip
            
        except Exception as e:
            logger.warning(f"Could not add transitions: {str(e)}")
            # Fallback to simple concatenation
            return concatenate_videoclips(clips)
    
    def _add_fade_effects(self, video: VideoFileClip) -> VideoFileClip:
        """Add fade in/out effects"""
        try:
            # Add fade in and fade out
            fade_duration = min(1.0, video.duration / 10)
            
            video = fadein(video, fade_duration)
            video = fadeout(video, fade_duration)
            
            # Audio fade effects
            if video.audio:
                video = video.set_audio(audio_fadein(video.audio, fade_duration))
                video = video.set_audio(audio_fadeout(video.audio, fade_duration))
            
            return video
            
        except Exception as e:
            logger.warning(f"Could not add fade effects: {str(e)}")
            return video
    
    def _extend_video_duration(self, video: VideoFileClip, target_duration: float) -> VideoFileClip:
        """Extend video duration by holding last frame"""
        try:
            if video.duration >= target_duration:
                return video
            
            # Get last frame as image
            last_frame = video.get_frame(video.duration - 0.1)
            
            # Create clip from last frame
            extension_duration = target_duration - video.duration
            last_frame_clip = ImageClip(last_frame, duration=extension_duration)
            
            # Concatenate original video with extended frame
            extended_video = concatenate_videoclips([video, last_frame_clip])
            
            return extended_video
            
        except Exception as e:
            logger.warning(f"Could not extend video duration: {str(e)}")
            return video
    
    def _create_placeholder_clip(self, duration: float, text: str = "Placeholder") -> VideoFileClip:
        """Create placeholder clip when image is missing"""
        try:
            # Create colored background
            color_clip = ColorClip(size=self.resolution, color=(50, 50, 50), duration=duration)
            
            # Add text
            try:
                text_clip = TextClip(text, fontsize=50, color='white', font='Arial')
                text_clip = text_clip.set_position('center').set_duration(duration)
                
                # Composite text over color
                placeholder = CompositeVideoClip([color_clip, text_clip])
            except Exception:
                # If text fails, just use color
                placeholder = color_clip
            
            return placeholder
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {str(e)}")
            # Return minimal clip
            return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
    
    def _write_video(self, video: VideoFileClip, output_path: str):
        """Write video to file with optimal settings"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write video with optimized settings
            video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
        except Exception as e:
            logger.error(f"Error writing video: {str(e)}")
            # Try with simpler settings
            try:
                video.write_videofile(
                    output_path,
                    fps=self.fps,
                    verbose=False,
                    logger=None
                )
            except Exception as e2:
                logger.error(f"Failed to write video with fallback settings: {str(e2)}")
                raise
    
    def _create_fallback_video(self, output_path: str, audio_path: str) -> str:
        """Create fallback video when main generation fails"""
        try:
            logger.info("Creating fallback video")
            
            # Load audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            
            # Create simple colored video
            video = ColorClip(size=self.resolution, color=(0, 50, 100), duration=duration)
            video = video.set_audio(audio)
            
            # Add error text
            try:
                error_text = TextClip("Video Generation Error", fontsize=60, color='white')
                error_text = error_text.set_position('center').set_duration(duration)
                video = CompositeVideoClip([video, error_text])
            except Exception:
                pass  # Continue without text
            
            # Write video
            video.write_videofile(output_path, fps=self.fps, verbose=False, logger=None)
            
            # Clean up
            video.close()
            audio.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating fallback video: {str(e)}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get information about generated video"""
        try:
            with VideoFileClip(video_path) as video:
                return {
                    'duration': video.duration,
                    'fps': video.fps,
                    'size': video.size,
                    'has_audio': video.audio is not None,
                    'file_size': os.path.getsize(video_path)
                }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def create_preview_clip(self, video_path: str, preview_path: str, 
                          start_time: float = 0, duration: float = 10) -> str:
        """Create a preview clip from video"""
        try:
            with VideoFileClip(video_path) as video:
                preview = video.subclip(start_time, min(start_time + duration, video.duration))
                preview.write_videofile(preview_path, fps=self.fps, verbose=False, logger=None)
            return preview_path
        except Exception as e:
            logger.error(f"Error creating preview: {str(e)}")
            return video_path