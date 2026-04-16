from mq_handler import send_task
import os

def seed_tasks():
    sources = [
        # Authenticated sources
        {"type": "login_web", "url": "http://hanhchinh.tlu.edu.vn/", "name": "Hành chính TLU"},
        {"type": "login_web", "url": "https://thuvienphapluat.vn/page/login.aspx", "name": "Thư viện pháp luật"},
        
        # Public news
        {"type": "web", "url": "https://www.tlu.edu.vn/tin-tuc", "name": "TLU News"},
        
        # All local PDFs from taskWeek1-2/data_raw
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/quydinh-daotao-dh.pdf", "name": "Quy chế Đào tạo ĐH"},
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/quy_che_ctsv.pdf", "name": "Quy chế Công tác Sinh viên"},
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/noi_quy_thu_vien.pdf", "name": "Nội quy Thư viện"},
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/quytinh-xet-tn-cap-bang-dh.pdf", "name": "Quy trình xét Tốt nghiệp"},
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/huong-dan-dk-hoc-phan.pdf", "name": "Hướng dẫn Đăng ký học phần"},
        {"type": "pdf", "url": "C:/SINHVIEN/DATN/DATN_2251162143_Progress_Note/taskWeek1-2/data_raw/quydinh-daotao-dh-2021.pdf", "name": "Quy chế Đào tạo ĐH 2021"}
    ]
    
    for src in sources:
        send_task('collector_tasks', src)
    
    print(f"Finished seeding {len(sources)} tasks.")

if __name__ == "__main__":
    seed_tasks()
    print("Done.")
