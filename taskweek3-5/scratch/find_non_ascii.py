path = r"C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskweek3-5\kaggle_chandra_engine\kaggle_chandra_runner.py"
with open(path, "rb") as f:
    content = f.read()

for i, byte in enumerate(content):
    if byte > 127:
        print(f"Non-ASCII byte {hex(byte)} at position {i}")
