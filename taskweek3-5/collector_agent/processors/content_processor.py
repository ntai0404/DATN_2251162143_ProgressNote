import re
from bs4 import BeautifulSoup
from typing import List, Dict

class ContentProcessor:
    def __init__(self):
        # Regex for standard Article/Section markers in Vietnamese
        self.section_pattern = re.compile(r'(Điều\s+\d+|Chương\s+[IVXLCDM]+|Phần\s+\d+)', re.IGNORECASE)

    def parse_high_fidelity_md(self, md_content: str) -> List[Dict]:
        """
        Parses Chandra's High-Fidelity Markdown (with HTML tags) into semantic chunks.
        """
        # Split by PAGE markers
        pages = re.split(r'## PAGE \d+', md_content)
        chunks = []
        
        current_article = "Giới thiệu"
        
        for page_idx, page_content in enumerate(pages):
            if not page_content.strip(): continue
            
            # Use BeautifulSoup to find all structural blocks
            soup = BeautifulSoup(page_content, 'html.parser')
            blocks = soup.find_all('div', recursive=False)
            
            if not blocks:
                # Fallback if no divs found (plain markdown)
                self._handle_plain_text(page_content, page_idx, chunks)
                continue

            for block in blocks:
                label = block.get('data-label', 'Text')
                bbox = block.get('data-bbox', '')
                clean_text = block.get_text(separator=' ').strip()
                
                # Check if this block is a new Section/Article
                if label == 'Section-Header' or self.section_pattern.search(clean_text):
                    match = self.section_pattern.search(clean_text)
                    if match:
                        current_article = match.group(1)

                if not clean_text: continue
                
                chunks.append({
                    "text": clean_text,
                    "raw_html": str(block),
                    "metadata": {
                        "page": page_idx,
                        "article": current_article,
                        "label": label,
                        "bbox": bbox
                    }
                })
        
        return chunks

    def _handle_plain_text(self, text, page_idx, chunks):
        # Basic split by double newline
        paras = text.split('\n\n')
        for p in paras:
            if p.strip():
                chunks.append({
                    "text": p.strip(),
                    "raw_html": f"<p>{p.strip()}</p>",
                    "metadata": {"page": page_idx, "label": "Text"}
                })
                
    def clean_text_for_embedding(self, text: str) -> str:
        """Removes extra spaces and normalizing text for better vector search"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
