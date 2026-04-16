import sys
import os
import json
import pika
sys.path.append(r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\shared")
from mq_handler import send_task

def run_test():
    task = {
        "type": "pdf",
        "url": r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskWeek1-2\data_raw\quydinh-daotao-dh.pdf",
        "name": "Test PDF"
    }
    send_task('collector_tasks', task)
    print("Test task sent.")

if __name__ == "__main__":
    run_test()
