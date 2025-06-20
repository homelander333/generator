# Image Generator Module - Create Visual Slides and Graphics
# Generates professional slide images with text and styling

import os
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import requests
    from io import BytesIO
    import colorsys
    import random
except ImportError as e:
    print(f"Warning: PIL or other dependencies not installed: {e}")

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generate slide images with professional styling
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.width = config.get('slide_width', 1920)
        self.height = config.get('slide_height', 1080)
        self.output_dir = Path("temp")
        self.output_dir.mkdir(exist_ok=True)
        
        # Color schemes
        self.color_schemes = {
            'modern': {
                'primary': '#2C3E50',
                'secondary': '#3498DB',
                'accent': '#E74C3C',
                'text': '#FFFFFF',
                'background': '#34495E'
            },
            'corporate': {
                'primary': '#1B365D',
                'secondary': '#4A90A4',
                'accent': '#87CEEB',
                'text': '#FFFFFF',
                'background': '#2C3E50'
            },
            'warm': {
                'primary': '#8B4513',
                'secondary': '#D2691E',
                'accent': '#FFD700',
                'text': '#FFFFFF',
                'background': '#A0522D'
            },
            'cool': {
                'primary': '#2F4F4F',
                'secondary': '#4682B4',
                'accent': '#00CED1',
                'text': '#FFFFFF',
                'background': '#708090'
            }
        }
        
        # Load fonts
        self._load_fonts()
    
    def _load_fonts(self):
        """Load available fonts"""
        self.fonts = {}
        
        try:
            # Try to load system fonts
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/Windows/Fonts/arial.ttf",         # Windows
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/usr/share/fonts/TTF/arial.ttf",   # Some Linux
            ]
            
            default_font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    default_font_path = path
                    break
            
            if default_font_path:
                self.fonts['title'] = ImageFont.truetype(default_font_path, 72)
                self.fonts['subtitle'] = ImageFont.truetype(default_font_path, 48)
                self.fonts['content'] = ImageFont.truetype(default_font_path, 36)
                self.fonts['small'] = ImageFont.truetype(default_font_path, 28)
            else:
                # Fallback to default font
                self.fonts['title'] = ImageFont.load_default()
                self.fonts['subtitle'] = ImageFont.load_default()
                self.fonts['content'] = ImageFont.load_default()
                self.fonts['small'] = ImageFont.load_default()
                
        except Exception as e:
            logger.warning(f"Error loading fonts: {str(e)}")
            # Use default fonts
            self.fonts['title'] = ImageFont.load_default()
            self.fonts['subtitle'] = ImageFont.load_default()
            self.fonts['content'] = ImageFont.load_default()
            self.fonts['small'] = ImageFont.load_default()
    
    def create_slide_image(self, slide_data: Dict[str, Any], output_path: str = None) -> str:
        """
        Create a slide image from slide data
        
        Args:
            slide_data: Dictionary containing slide information
            output_path: Output path for the image
            
        Returns:
            Path to created image
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix=".png")
        
        try:
            slide_type = slide_data.get('type', 'content')
            
            if slide_type == 'title':
                image = self._create_title_slide(slide_data)
            elif slide_type == 'summary':
                image = self._create_summary_slide(slide_data)
            else:
                image = self._create_content_slide(slide_data)
            
            # Save image
            image.save(output_path, 'PNG', quality=95)
            logger.info(f"Created slide image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating slide image: {str(e)}")
            return self._create_error_slide(output_path)
    
    def _create_title_slide(self, slide_data: Dict[str, Any]) -> Image.Image:
        """Create a title slide"""
        # Create image with gradient background
        image = self._create_background(slide_data.get('background_type', 'gradient'))
        draw = ImageDraw.Draw(image)
        
        # Get color scheme
        scheme = self._get_color_scheme()
        
        # Title
        title = slide_data.get('title', 'Title')
        title_font = self.fonts['title']
        
        # Calculate title position (centered)
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (self.width - title_width) // 2
        title_y = self.height // 3
        
        # Draw title with shadow
        self._draw_text_with_shadow(draw, (title_x, title_y), title, title_font, scheme['text'])
        
        # Subtitle
        subtitle = slide_data.get('subtitle', '')
        if subtitle:
            subtitle_font = self.fonts['subtitle']
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 50
            
            self._draw_text_with_shadow(draw, (subtitle_x, subtitle_y), subtitle, subtitle_font, scheme['accent'])
        
        # Add decorative elements
        self._add_decorative_elements(draw, scheme)
        
        return image
    
    def _create_content_slide(self, slide_data: Dict[str, Any]) -> Image.Image:
        """Create a content slide"""
        # Create image with background
        image = self._create_background(slide_data.get('background_type', 'solid'))
        draw = ImageDraw.Draw(image)
        
        # Get color scheme
        scheme = self._get_color_scheme()
        
        # Title
        title = slide_data.get('title', 'Content')
        title_font = self.fonts['subtitle']
        
        # Title position
        title_x = 100
        title_y = 80
        
        self._draw_text_with_shadow(draw, (title_x, title_y), title, title_font, scheme['accent'])
        
        # Content
        content = slide_data.get('content', '')
        if content:
            content_font = self.fonts['content']
            
            # Word wrap content
            wrapped_lines = self._wrap_text(content, content_font, self.width - 200)
            
            # Draw content lines
            line_height = 50
            content_y = title_y + 100
            
            for i, line in enumerate(wrapped_lines):
                if content_y + (i * line_height) < self.height - 100:  # Don't go below bottom margin
                    self._draw_text_with_shadow(
                        draw, 
                        (title_x, content_y + (i * line_height)), 
                        line, 
                        content_font, 
                        scheme['text']
                    )
        
        # Add slide number
        slide_num = slide_data.get('slide_number', '')
        if slide_num:
            num_text = f"{slide_num}"
            num_font = self.fonts['small']
            self._draw_text_with_shadow(
                draw, 
                (self.width - 100, self.height - 60), 
                num_text, 
                num_font, 
                scheme['secondary']
            )
        
        return image
    
    def _create_summary_slide(self, slide_data: Dict[str, Any]) -> Image.Image:
        """Create a summary slide"""
        # Similar to content slide but with different styling
        image = self._create_background('gradient')
        draw = ImageDraw.Draw(image)
        
        scheme = self._get_color_scheme()
        
        # Title
        title = slide_data.get('title', 'Summary')
        title_font = self.fonts['title']
        
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        title_y = 100
        
        self._draw_text_with_shadow(draw, (title_x, title_y), title, title_font, scheme['accent'])
        
        # Content as bullet points
        content = slide_data.get('content', '')
        if content:
            sentences = content.split('. ')
            content_font = self.fonts['content']
            
            bullet_y = title_y + 150
            line_height = 80
            
            for i, sentence in enumerate(sentences):
                if sentence.strip() and bullet_y + (i * line_height) < self.height - 100:
                    bullet_text = f"• {sentence.strip()}"
                    wrapped_lines = self._wrap_text(bullet_text, content_font, self.width - 200)
                    
                    for j, line in enumerate(wrapped_lines):
                        self._draw_text_with_shadow(
                            draw,
                            (100, bullet_y + (i * line_height) + (j * 45)),
                            line,
                            content_font,
                            scheme['text']
                        )
        
        return image
    
    def _create_background(self, bg_type: str) -> Image.Image:
        """Create background image"""
        if bg_type == 'gradient':
            return self._create_gradient_background()
        else:
            return self._create_solid_background()
    
    def _create_gradient_background(self) -> Image.Image:
        """Create gradient background"""
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        scheme = self._get_color_scheme()
        
        # Create vertical gradient
        for y in range(self.height):
            # Interpolate between background and primary colors
            ratio = y / self.height
            color = self._interpolate_color(scheme['background'], scheme['primary'], ratio)
            draw.line([(0, y), (self.width, y)], fill=color)
        
        return image
    
    def _create_solid_background(self) -> Image.Image:
        """Create solid color background"""
        scheme = self._get_color_scheme()
        image = Image.new('RGB', (self.width, self.height), scheme['background'])
        return image
    
    def _get_color_scheme(self) -> Dict[str, str]:
        """Get random color scheme"""
        schemes = list(self.color_schemes.keys())
        selected = random.choice(schemes)
        return self.color_schemes[selected]
    
    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> Tuple[int, int, int]:
        """Interpolate between two hex colors"""
        # Convert hex to RGB
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        # Interpolate
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return (r, g, b)
    
    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, position: Tuple[int, int], 
                              text: str, font: ImageFont.ImageFont, color: str):
        """Draw text with shadow effect"""
        x, y = position
        
        # Draw shadow
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill='#000000')
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=color)
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, break it
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _add_decorative_elements(self, draw: ImageDraw.Draw, scheme: Dict[str, str]):
        """Add decorative elements to slide"""
        # Add corner decorations
        accent_color = scheme['accent']
        
        # Top left corner
        draw.rectangle([0, 0, 100, 20], fill=accent_color)
        draw.rectangle([0, 0, 20, 100], fill=accent_color)
        
        # Bottom right corner
        draw.rectangle([self.width-100, self.height-20, self.width, self.height], fill=accent_color)
        draw.rectangle([self.width-20, self.height-100, self.width, self.height], fill=accent_color)
    
    def _create_error_slide(self, output_path: str) -> str:
        """Create error slide when image generation fails"""
        try:
            image = Image.new('RGB', (self.width, self.height), '#800000')
            draw = ImageDraw.Draw(image)
            
            error_text = "Error generating slide"
            font = self.fonts['title']
            
            bbox = draw.textbbox((0, 0), error_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (self.width - text_width) // 2
            text_y = self.height // 2
            
            draw.text((text_x, text_y), error_text, font=font, fill='#FFFFFF')
            
            image.save(output_path, 'PNG')
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating error slide: {str(e)}")
            return output_path
    
    def create_thumbnail(self, image_path: str, thumbnail_path: str = None) -> str:
        """Create thumbnail from image"""
        if not thumbnail_path:
            thumbnail_path = image_path.replace('.png', '_thumb.png')
        
        try:
            with Image.open(image_path) as img:
                img.thumbnail((320, 180))
                img.save(thumbnail_path, 'PNG')
            return thumbnail_path
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return image_path