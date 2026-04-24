import streamlit as st
import os
import requests
import json
import pandas as pd
from pathlib import Path
import time

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data_raw"
RESULTS_DIR = BASE_DIR / "ocr_diagnostics"
SEARCH_API_URL = "http://localhost:8003/search"
REFRESH_API_URL = "http://localhost:8003/refresh"

st.set_page_config(page_title="TLU Smart Tutor - Chandra OCR Edition", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    .admin-card { padding: 20px; border-radius: 10px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🎓 TLU Smart Tutor - Hệ thống Tra cứu Nội quy thông minh")
    
    # Sidebar navigation (Admin vs User)
    role = st.sidebar.radio("Vai trò người dùng:", ["👤 Sinh viên (User)", "🛡️ Quản trị viên (Admin)"])
    
    if role == "🛡️ Quản trị viên (Admin)":
        show_admin_page()
    else:
        show_user_page()

def show_admin_page():
    st.header("🛡️ Trung tâm Điều phối Dữ liệu (Admin)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Kho hồ sơ PDF (data_raw_v2)")
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
        
        file_data = []
        for f in files:
            safe_name = f.replace(" ", "_") # Tương ứng logic bot
            # Kiểm tra xem đã có kết quả OCR chưa
            ocr_exists = any(safe_name.replace(".pdf", "") in rf for rf in os.listdir(RESULTS_DIR)) if RESULTS_DIR.exists() else False
            status = "✅ Đã OCR" if ocr_exists else "⏳ Chờ xử lý"
            file_data.append({"Tên File": f, "Trạng thái": status})
        
        df = pd.DataFrame(file_data)
        st.table(df)
        
    with col2:
        st.subheader("⚡ Lệnh điều khiển")
        target_file = st.selectbox("Chọn file cần OCR:", files)
        
        if st.button("🚀 Kích hoạt Chandra OCR (Kaggle GPU)"):
            with st.status(f"Đang xử lý {target_file}...", expanded=True) as status:
                st.write("1. Đang tải file lên Cloud...")
                # Giả lập lệnh gọi bot (Trong thực tế sẽ dùng subprocess hoặc API)
                time.sleep(2)
                st.write("2. Đang khởi động GPU T4 x2...")
                time.sleep(2)
                st.write("3. Đang bóc tách chữ bằng Chandra-2...")
                status.update(label="OCR Hoàn tất! Vui lòng làm mới bộ chỉ mục.", state="complete")
        
        st.divider()
        if st.button("🔄 Làm mới Bộ chỉ mục Tìm kiếm (Refresh Index)"):
            try:
                resp = requests.post(REFRESH_API_URL)
                if resp.status_code == 200:
                    st.success(f"Đã cập nhật {resp.json().get('count')} mảnh dữ liệu vào Hybrid Search!")
                else:
                    st.error("Không thể kết nối Search API.")
            except:
                st.error("Search API chưa khởi động (Port 8003).")

def show_user_page():
    st.header("👤 Tra cứu Nội quy Sinh viên")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "results" in message:
                with st.expander("🔍 Trích dẫn nguồn & Độ tin cậy"):
                    for res in message["results"]:
                        st.write(f"- **{res['title']}** (Trang {res['metadata'].get('page')})")
                        st.write(f"  *Score: {res['score']:.4f} (Hybrid)*")

    # User input
    if prompt := st.chat_input("Hỏi tôi về nội quy nội trú, học phí, học bổng..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                resp = requests.post(SEARCH_API_URL, json={"query": prompt, "top_k": 3})
                if resp.status_code == 200:
                    results = resp.json()
                    if results:
                        best_match = results[0]
                        # Mô phỏng AI tổng hợp câu trả lời từ kết quả search
                        answer = f"Dựa trên {best_match['title']}, tôi tìm thấy thông tin sau:\n\n{best_match['content'][:500]}..."
                        st.markdown(answer)
                        
                        with st.expander("🔍 Trích dẫn nguồn & Độ tin cậy"):
                            for res in results:
                                st.write(f"- **{res['title']}** (Trang {res['metadata'].get('page')})")
                                st.write(f"  *Score: {res['score']:.4f} (Hybrid)*")
                        
                        st.session_state.messages.append({"role": "assistant", "content": answer, "results": results})
                    else:
                        st.warning("Xin lỗi, tôi không tìm thấy thông tin này trong quy định.")
                else:
                    st.error("Lỗi kết nối với bộ máy tìm kiếm.")
            except Exception as e:
                st.error(f"Vui lòng bật Search API tại cổng 8003. (Lỗi: {e})")

if __name__ == "__main__":
    main()
