# News Scraper Module - Extract Content from Web Articles
# Uses Newspaper3k and BeautifulSoup for robust content extraction

import logging
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin
import re
from datetime import datetime

try:
    from newspaper import Article, Config
    import newspaper
except ImportError:
    print("Warning: newspaper3k not installed. Install with: pip install newspaper3k")

try:
    from bs4 import BeautifulSoup
    import readability
except ImportError:
    print("Warning: BeautifulSoup4 not installed. Install with: pip install beautifulsoup4 lxml")

logger = logging.getLogger(__name__)

class NewsScraper:
    """
    Extract and process content from news articles and web pages
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('request_timeout', 10)
        self.user_agent = config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Configure newspaper
        self.newspaper_config = Config()
        self.newspaper_config.browser_user_agent = self.user_agent
        self.newspaper_config.request_timeout = self.timeout
        self.newspaper_config.memoize_articles = False
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def extract_article(self, url: str) -> Dict[str, Any]:
        """
        Extract article content from URL
        
        Args:
            url: URL of the article to extract
            
        Returns:
            Dictionary containing extracted content
        """
        try:
            logger.info(f"Extracting article from: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Try newspaper3k first
            article_data = self._extract_with_newspaper(url)
            
            # If newspaper fails or returns incomplete data, try BeautifulSoup
            if not article_data.get('text') or len(article_data.get('text', '')) < 100:
                logger.info("Newspaper extraction insufficient, trying BeautifulSoup")
                soup_data = self._extract_with_beautifulsoup(url)
                
                # Merge data, preferring non-empty values
                for key, value in soup_data.items():
                    if value and (not article_data.get(key) or len(str(article_data.get(key, ''))) < len(str(value))):
                        article_data[key] = value
            
            # Clean and validate extracted data
            article_data = self._clean_article_data(article_data)
            
            logger.info(f"Successfully extracted article: {len(article_data.get('text', ''))} characters")
            return article_data
            
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {str(e)}")
            return self._create_fallback_article(url, str(e))
    
    def _extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Extract article using newspaper3k"""
        try:
            article = Article(url, config=self.newspaper_config)
            article.download()
            article.parse()
            
            # Try to extract additional metadata
            try:
                article.nlp()
            except Exception:
                pass  # NLP is optional
            
            return {
                'title': article.title or '',
                'text': article.text or '',
                'author': ', '.join(article.authors) if article.authors else '',
                'publish_date': article.publish_date.isoformat() if article.publish_date else '',
                'top_image': article.top_image or '',
                'meta_description': article.meta_description or '',
                'meta_keywords': ', '.join(article.meta_keywords) if article.meta_keywords else '',
                'summary': article.summary if hasattr(article, 'summary') else '',
                'url': url,
                'extraction_method': 'newspaper3k'
            }
            
        except Exception as e:
            logger.warning(f"Newspaper3k extraction failed: {str(e)}")
            return {}
    
    def _extract_with_beautifulsoup(self, url: str) -> Dict[str, Any]:
        """Extract article using BeautifulSoup as fallback"""
        try:
            # Fetch page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract metadata
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            description = self._extract_description(soup)
            image = self._extract_main_image(soup, url)
            
            return {
                'title': title,
                'text': content,
                'author': author,
                'publish_date': publish_date,
                'top_image': image,
                'meta_description': description,
                'url': url,
                'extraction_method': 'beautifulsoup'
            }
            
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed: {str(e)}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            'h1',
            '[property="og:title"]',
            'title',
            '.article-title',
            '.post-title',
            '.entry-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get('content') if element.has_attr('content') else element.get_text()
                if title and len(title.strip()) > 5:
                    return title.strip()
        
        return ''
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Try content selectors
        content_selectors = [
            'article',
            '.article-content',
            '.post-content', 
            '.entry-content',
            '.content',
            '.article-body',
            '.story-body',
            '[property="articleBody"]',
            'main p'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = '\n'.join([elem.get_text().strip() for elem in elements])
                if len(content) > 200:  # Ensure substantial content
                    return self._clean_text(content)
        
        # Fallback: extract all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
            return self._clean_text(content)
        
        return ''
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '[property="article:author"]',
            '[name="author"]',
            '.author',
            '.byline',
            '.article-author',
            '.post-author'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') if element.has_attr('content') else element.get_text()
                if author and len(author.strip()) > 2:
                    return author.strip()
        
        return ''
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        date_selectors = [
            '[property="article:published_time"]',
            '[property="article:published"]',
            '[name="publish_date"]',
            '.publish-date',
            '.article-date',
            '.post-date',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_str = element.get('content') or element.get('datetime') or element.get_text()
                if date_str:
                    try:
                        # Try to parse and standardize date
                        from dateutil import parser
                        parsed_date = parser.parse(date_str)
                        return parsed_date.isoformat()
                    except:
                        return date_str.strip()
        
        return ''
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        desc_selectors = [
            '[property="og:description"]',
            '[name="description"]',
            '[name="twitter:description"]'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                return element.get('content').strip()
        
        return ''
    
    def _extract_main_image(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract main article image"""
        img_selectors = [
            '[property="og:image"]',
            '[name="twitter:image"]',
            '.article-image img',
            '.featured-image img',
            'article img'
        ]
        
        for selector in img_selectors:
            element = soup.select_one(selector)
            if element:
                img_url = element.get('content') or element.get('src')
                if img_url:
                    # Make absolute URL
                    return urljoin(base_url, img_url)
        
        return ''
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'(Advertisement|Subscribe|Sign up|Follow us).*?\n', '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up punctuation
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'\s*\.\s*\.\s*\.', '...', text)
        
        return text.strip()
    
    def _clean_article_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate article data"""
        # Ensure minimum content length
        if len(data.get('text', '')) < 50:
            raise ValueError("Article content too short")
        
        # Clean title
        if data.get('title'):
            data['title'] = re.sub(r'\s+', ' ', data['title']).strip()
        
        # Clean text
        if data.get('text'):
            data['text'] = self._clean_text(data['text'])
        
        # Validate image URL
        if data.get('top_image') and not data['top_image'].startswith('http'):
            data['top_image'] = ''
        
        return data
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _create_fallback_article(self, url: str, error: str) -> Dict[str, Any]:
        """Create fallback article data when extraction fails"""
        return {
            'title': 'Extraction Failed',
            'text': f'Unable to extract content from {url}. Error: {error}',
            'author': '',
            'publish_date': '',
            'top_image': '',
            'meta_description': '',
            'url': url,
            'extraction_method': 'fallback',
            'error': error
        }
    
    def extract_multiple_articles(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Extract multiple articles"""
        articles = []
        for url in urls:
            try:
                article = self.extract_article(url)
                articles.append(article)
            except Exception as e:
                logger.error(f"Failed to extract {url}: {str(e)}")
                articles.append(self._create_fallback_article(url, str(e)))
        
        return articles
    
    def get_article_summary(self, url: str, max_length: int = 500) -> str:
        """Get a brief summary of an article"""
        try:
            article = self.extract_article(url)
            text = article.get('text', '')
            
            if len(text) <= max_length:
                return text
            
            # Extract first few sentences
            sentences = re.split(r'[.!?]+', text)
            summary = ''
            
            for sentence in sentences:
                if len(summary + sentence) <= max_length:
                    summary += sentence + '. '
                else:
                    break
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error getting article summary: {str(e)}")
            return f"Unable to extract summary from {url}"