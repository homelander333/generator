# Content Processor Module - Text Processing and Slide Generation
# Handles content structuring, keyword extraction, and slide creation

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import nltk
from pathlib import Path

try:
    from textstat import flesch_reading_ease, syllable_count
    import spacy
    from sklearn.feature_extraction.text import TfidfVectorizer
    from wordcloud import WordCloud
except ImportError as e:
    print(f"Warning: Optional dependencies not installed: {e}")

logger = logging.getLogger(__name__)

class ContentProcessor:
    """
    Process text content into structured slides for video generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_slides = config.get('max_slides', 8)
        self.words_per_slide = config.get('words_per_slide', 50)
        self.min_slide_duration = config.get('min_slide_duration', 3.0)
        self.max_slide_duration = config.get('max_slide_duration', 8.0)
        
        # Initialize NLP tools
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP tools"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            
            # Try to load spaCy model
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
                
        except Exception as e:
            logger.error(f"Error initializing NLP tools: {str(e)}")
            self.nlp = None
    
    def create_slides(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create structured slides from content
        
        Args:
            content: Dictionary with title, text, author, etc.
            
        Returns:
            List of slide dictionaries
        """
        try:
            text = content.get('text', '')
            title = content.get('title', 'Untitled')
            
            if not text:
                return self._create_fallback_slides(title)
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(text)
            
            # Extract key information
            keywords = self._extract_keywords(cleaned_text)
            sentences = self._split_into_sentences(cleaned_text)
            
            # Create slides
            slides = []
            
            # Title slide
            slides.append({
                'type': 'title',
                'title': title,
                'subtitle': content.get('author', ''),
                'content': '',
                'keywords': keywords[:3],
                'duration': 4.0,
                'background_type': 'gradient',
                'text_size': 'large'
            })
            
            # Content slides
            content_slides = self._create_content_slides(sentences, keywords)
            slides.extend(content_slides)
            
            # Summary slide (if content is long enough)
            if len(sentences) > 5:
                summary = self._generate_summary(cleaned_text, sentences)
                slides.append({
                    'type': 'summary',
                    'title': 'Key Points',
                    'content': summary,
                    'keywords': keywords[:5],
                    'duration': 5.0,
                    'background_type': 'solid',
                    'text_size': 'medium'
                })
            
            # Limit total slides
            if len(slides) > self.max_slides:
                slides = slides[:self.max_slides]
            
            logger.info(f"Created {len(slides)} slides from content")
            return slides
            
        except Exception as e:
            logger.error(f"Error creating slides: {str(e)}")
            return self._create_fallback_slides(content.get('title', 'Error'))
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # Fix common issues
        text = text.replace('..', '.')
        text = text.replace('  ', ' ')
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        try:
            if self.nlp:
                doc = self.nlp(text)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            else:
                # Fallback to NLTK
                from nltk.tokenize import sent_tokenize
                sentences = sent_tokenize(text)
            
            # Filter out very short sentences
            sentences = [s for s in sentences if len(s.split()) >= 4]
            
            return sentences
            
        except Exception as e:
            logger.error(f"Error splitting sentences: {str(e)}")
            # Simple fallback
            return [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        try:
            if self.nlp:
                return self._extract_keywords_spacy(text, max_keywords)
            else:
                return self._extract_keywords_simple(text, max_keywords)
                
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def _extract_keywords_spacy(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using spaCy"""
        doc = self.nlp(text)
        
        # Extract named entities and important nouns
        keywords = []
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
                keywords.append(ent.text)
        
        # Important nouns and adjectives
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and
                len(token.text) > 2):
                keywords.append(token.text)
        
        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))[:max_keywords]
        
        return keywords
    
    def _extract_keywords_simple(self, text: str, max_keywords: int) -> List[str]:
        """Simple keyword extraction using frequency analysis"""
        try:
            from collections import Counter
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text.lower())
            
            # Filter words
            words = [word for word in words 
                    if word.isalpha() and 
                    len(word) > 2 and 
                    word not in stop_words]
            
            # Get most common words
            word_freq = Counter(words)
            keywords = [word for word, freq in word_freq.most_common(max_keywords)]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error in simple keyword extraction: {str(e)}")
            return []
    
    def _create_content_slides(self, sentences: List[str], keywords: List[str]) -> List[Dict[str, Any]]:
        """Create content slides from sentences"""
        slides = []
        current_slide_text = ""
        current_slide_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed word limit
            words_in_sentence = len(sentence.split())
            current_words = len(current_slide_text.split())
            
            if current_words + words_in_sentence <= self.words_per_slide:
                current_slide_text += " " + sentence if current_slide_text else sentence
                current_slide_sentences.append(sentence)
            else:
                # Create slide from current content
                if current_slide_text:
                    slide = self._create_single_content_slide(
                        current_slide_text, 
                        current_slide_sentences, 
                        keywords,
                        len(slides) + 1
                    )
                    slides.append(slide)
                
                # Start new slide
                current_slide_text = sentence
                current_slide_sentences = [sentence]
        
        # Add remaining content
        if current_slide_text:
            slide = self._create_single_content_slide(
                current_slide_text, 
                current_slide_sentences, 
                keywords,
                len(slides) + 1
            )
            slides.append(slide)
        
        return slides
    
    def _create_single_content_slide(self, text: str, sentences: List[str], 
                                   keywords: List[str], slide_num: int) -> Dict[str, Any]:
        """Create a single content slide"""
        # Extract relevant keywords for this slide
        slide_keywords = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                slide_keywords.append(keyword)
        
        # Calculate duration based on text length
        word_count = len(text.split())
        duration = max(self.min_slide_duration, min(self.max_slide_duration, word_count / 10))
        
        # Create slide title from first sentence or keywords
        title = self._create_slide_title(sentences[0] if sentences else text, slide_num)
        
        return {
            'type': 'content',
            'title': title,
            'content': text,
            'keywords': slide_keywords[:3],
            'duration': duration,
            'background_type': 'gradient' if slide_num % 2 == 0 else 'solid',
            'text_size': 'medium',
            'slide_number': slide_num
        }
    
    def _create_slide_title(self, text: str, slide_num: int) -> str:
        """Create a title for a content slide"""
        # Extract first few words
        words = text.split()[:6]
        title = ' '.join(words)
        
        # Clean up title
        title = re.sub(r'[^\w\s]', '', title)
        title = title.strip()
        
        # Ensure title isn't too long
        if len(title) > 40:
            title = title[:37] + "..."
        
        return title if title else f"Section {slide_num}"
    
    def _generate_summary(self, text: str, sentences: List[str]) -> str:
        """Generate a summary of the content"""
        try:
            # Simple extractive summarization
            if len(sentences) <= 3:
                return '. '.join(sentences)
            
            # Take first sentence, a middle sentence, and last sentence
            summary_sentences = [
                sentences[0],
                sentences[len(sentences) // 2],
                sentences[-1]
            ]
            
            return '. '.join(summary_sentences)
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def _create_fallback_slides(self, title: str) -> List[Dict[str, Any]]:
        """Create fallback slides when content processing fails"""
        return [
            {
                'type': 'title',
                'title': title,
                'subtitle': 'Content Processing Error',
                'content': 'Unable to process the provided content.',
                'keywords': [],
                'duration': 5.0,
                'background_type': 'gradient',
                'text_size': 'large'
            }
        ]
    
    def estimate_total_duration(self, slides: List[Dict[str, Any]]) -> float:
        """Estimate total video duration from slides"""
        return sum(slide.get('duration', 5.0) for slide in slides)
    
    def get_slide_statistics(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the slides"""
        total_words = sum(len(slide.get('content', '').split()) for slide in slides)
        total_duration = self.estimate_total_duration(slides)
        
        return {
            'total_slides': len(slides),
            'total_words': total_words,
            'total_duration': total_duration,
            'average_words_per_slide': total_words / len(slides) if slides else 0,
            'average_duration_per_slide': total_duration / len(slides) if slides else 0
        }