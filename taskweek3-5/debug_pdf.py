import fitz
doc = fitz.open(r'C:\SINHVIEN\DATN\DATN_2251162143_Progress_Note\taskWeek1-2\data_raw\quydinh-daotao-dh.pdf')
print(doc[0].get_text()[:2000])
