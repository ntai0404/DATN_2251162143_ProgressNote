import re

class DataCleaner:
    def __init__(self):
        # Bộ quy tắc sửa lỗi phổ biến (Common OCR mangles)
        self.rules = [
            # 1. Sửa lỗi nhận diện chữ "Trường"
            (r'(?i)[IlIn]ru[ờo]ng', 'Trường'),
            (r'(?i)Tr[uđ][ờo]ng', 'Trường'),
            
            # 2. Sửa lỗi chữ "Điều/Định/Đào"
            (r'(?i)Đ[ỉíiì]êu', 'Điều'),
            (r'(?i)Đ[ạa]i\s*h[ọo]c', 'Đại học'),
            (r'(?i)đo\s*t[ạa]o', 'đào tạo'),
            
            # 3. Sửa lỗi ký tự 'đ' bị nhận diện nhầm thành 'ẩ'
            (r'ẩ(?=[uư]ờng|ã|à|ợ)', 'đ'),
            (r'(?<=\s)ẩ', 'đ'),
            
            # 4. Sửa lỗi dính chữ
            (r'(?i)Bộmôn', 'Bộ môn'),
            (r'(?i)gọitắt', 'gọi tắt'),
            
            # 5. Sửa lỗi dấu hỏi/ngã/nặng phổ biến
            (r'kề từ', 'kể từ'),
            (r'đảm bào', 'đảm bảo'),
            (r'nghiên cúu', 'nghiên cứu'),
            (r'kiẻm tra', 'kiểm tra'),
            
            # 6. Sửa lỗi in hoa/thường nhầm lẫn (T -> I)
            (r'Nguyễn\s*Irung', 'Nguyễn Trung'),
        ]
        
    def clean_text(self, text):
        if not text: return ""
        
        # A. Xóa nhiễu con dấu/ký tự rác (Noise removal)
        # Xóa các chuỗi vô nghĩa có quá nhiều ký tự đặc biệt/lộn xộn
        text = re.sub(r'[ýỷ§{}Fwvq;.,]{2,}', '', text)
        
        # B. Áp dụng các quy tắc sửa lỗi chính tả
        cleaned = text
        for pattern, replacement in self.rules:
            cleaned = re.sub(pattern, replacement, cleaned)
            
        # C. Chuẩn hóa khoảng trắng
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()

    def filter_noise_chunks(self, chunks):
        """Loại bỏ các đoạn chunk chứa quá nhiều rác không có giá trị."""
        valid_chunks = []
        for chunk in chunks:
            content = chunk['content']
            # Nếu đoạn văn có quá nhiều ký tự rác hoặc quá ngắn sau khi clean
            if len(content) < 20: continue
            
            # Kiểm tra tỷ lệ ký tự rác/chữ
            noise_chars = len(re.findall(r'[^\w\s,.\-]', content))
            if noise_chars / (len(content) + 1) > 0.3:
                continue
                
            chunk['content'] = self.clean_text(content)
            valid_chunks.append(chunk)
            
        return valid_chunks
