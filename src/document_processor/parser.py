"""
Document parser supporting multiple formats: PDF, HTML, Markdown, and DOCX.
"""

from typing import Dict, List, Optional
from pathlib import Path
import PyPDF2
from bs4 import BeautifulSoup
import docx
import markdown

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentParser:
    """Parse documents from various formats and extract text content."""
    
    SUPPORTED_FORMATS = {'.pdf', '.html', '.htm', '.md', '.markdown', '.docx', '.txt'}
    
    def __init__(self):
        """Initialize the document parser."""
        pass
    
    def parse(self, file_path: str) -> Dict[str, any]:
        """
        Parse a document and extract text content with metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing:
                - text: Extracted text content
                - metadata: Document metadata (title, format, etc.)
                
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"Parsing document: {path.name} (format: {suffix})")
        
        # Route to appropriate parser
        if suffix == '.pdf':
            text = self._parse_pdf(path)
        elif suffix in {'.html', '.htm'}:
            text = self._parse_html(path)
        elif suffix in {'.md', '.markdown'}:
            text = self._parse_markdown(path)
        elif suffix == '.docx':
            text = self._parse_docx(path)
        elif suffix == '.txt':
            text = self._parse_txt(path)
        else:
            raise ValueError(f"Parser not implemented for: {suffix}")
        
        # Clean the text
        text = self._clean_text(text)
        
        metadata = {
            'filename': path.name,
            'format': suffix,
            'path': str(path.absolute()),
        }
        
        logger.info(f"Successfully parsed {path.name}: {len(text)} characters")
        
        return {
            'text': text,
            'metadata': metadata
        }
    
    def _parse_pdf(self, path: Path) -> str:
        """Extract text from PDF file."""
        text_parts = []
        
        try:
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"[Page {page_num + 1}]\n{text}")
        
        except Exception as e:
            logger.error(f"Error parsing PDF {path.name}: {e}")
            raise
        
        return "\n\n".join(text_parts)
    
    def _parse_html(self, path: Path) -> str:
        """Extract text from HTML file."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Remove script and style elements
                for script in soup(['script', 'style']):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                return text
        
        except Exception as e:
            logger.error(f"Error parsing HTML {path.name}: {e}")
            raise
    
    def _parse_markdown(self, path: Path) -> str:
        """Extract text from Markdown file."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                md_content = file.read()
                
                # Convert to HTML first, then extract text for better formatting
                html = markdown.markdown(md_content)
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                
                return text
        
        except Exception as e:
            logger.error(f"Error parsing Markdown {path.name}: {e}")
            raise
    
    def _parse_docx(self, path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"Error parsing DOCX {path.name}: {e}")
            raise
    
    def _parse_txt(self, path: Path) -> str:
        """Extract text from plain text file."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return file.read()
        
        except Exception as e:
            logger.error(f"Error parsing TXT {path.name}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with double newline
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        return '\n'.join(cleaned_lines)
