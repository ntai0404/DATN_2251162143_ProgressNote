import win32com.client
import os
from pathlib import Path

class WordHandler:
    def __init__(self):
        self.word_app = None

    def _ensure_word(self):
        if self.word_app is None:
            # Initialize Word in background
            self.word_app = win32com.client.Dispatch("Word.Application")
            self.word_app.Visible = False

    def extract_text_from_doc(self, file_path: str) -> str:
        """
        Extracts text from .doc or .docx using MS Word.
        """
        abs_path = str(Path(file_path).absolute())
        print(f"[Word] Extracting text from {abs_path}...")
        
        self._ensure_word()
        doc = None
        try:
            doc = self.word_app.Documents.Open(abs_path)
            content = doc.Content.Text
            # Replace common Word special characters
            content = content.replace('\r', '\n')
            return content
        except Exception as e:
            print(f"[Word ERROR] Failed to extract: {e}")
            return ""
        finally:
            if doc:
                doc.Close(False)

    def close(self):
        if self.word_app:
            self.word_app.Quit()
            self.word_app = None
