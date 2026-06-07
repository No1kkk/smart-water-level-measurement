import cv2
import numpy as np
import time

# --- CÁC BIẾN TOÀN CỤC CHUẨN HÓA KHÔNG DẤU ---
ve_khung_roi = False
roi_x, roi_y, roi_w, roi_h = -1, -1, -1, -1
click_y = -1

# Khởi tạo giá trị mặc định cho các biến lưu trữ báo cáo cuối cùng
cuoi_muc_nuoc_pct = 0
cuoi_chieu_cao_nuoc = 0.0
cuoi_the_tich_tong = 0
cuoi_the_tich_thuc = 0
cuoi_trang_thai_nuoc = "Chưa xác định"

def click_event_chon_day(event, x, y, flags, param):
    """Hàm bắt sự kiện click chuột để chọn vạch đáy cốc"""
    global click_y
    if event == cv2.EVENT_LBUTTONDOWN:
        click_y = y
        print(f"-> Đã ghi nhận vạch đáy trong tại tọa độ Y: {y} pixel")

def mouse_event_quet_coc(event, x, y, flags, param):
    """Hàm tự vẽ khung chọn cốc"""
    global roi_x, roi_y, roi_w, roi_h, ve_khung_roi
    if event == cv2.EVENT_LBUTTONDOWN:
        roi_x, roi_y = x, y
        ve_khung_roi = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if ve_khung_roi:
            roi_w = x - roi_x
            roi_h = y - roi_y
    elif event == cv2.EVENT_LBUTTONUP:
        ve_khung_roi = False
        roi_w = x - roi_x
        roi_h = y - roi_y

def lay_thong_tin_cau_hinh():
    """Hàm hỏi thông số cốc và vật thể bên trong để trừ hao"""
    print("="*10 + " CẤU HÌNH THÔNG SỐ CỐC NƯỚC " + "="*10)
    try:
        chieu_cao_long_trong = float(input("Nhập CHIỀU CAO LÒNG TRONG chứa nước (cm): "))
        chieu_rong_long_trong = float(input("Nhập CHIỀU RỘNG / ĐƯỜNG KÍNH lòng trong cốc (cm): "))
        chieu_rong_ngoai = float(input("Nhập CHIỀU RỘNG / ĐƯỜNG KÍNH toàn bộ vỏ ngoài cốc (cm): "))
        
        print("\n" + "-"*5 + " TÍNH NĂNG TRỪ HAO VẬT THỂ CHIẾM CHỖ " + "-"*5)
        co_vat_the = input("Có vật thể nào bên trong cốc không? (y/n): ")
        
        the_tich_vat_the_ml = 0.0
        if co_vat_the.lower() == 'y':
            loai_nhap = input("Bạn muốn nhập theo (1) Thể tích vật thể (ml) hoặc (2) Khối lượng vật (g)? Chọn 1 hoặc 2: ")
            if loai_nhap == '1':
                the_tich_vat_the_ml = float(input("Nhập thể tích vật thể (ml): "))
            else:
                khoi_luong_g = float(input("Nhập khối lượng vật thể (g): "))
                the_tich_vat_the_ml = round(khoi_luong_g / 1.0, 1)
            print(f"-> Hệ thống sẽ tự động trừ đi {the_tich_vat_the_ml} ml vật thể chiếm chỗ.")
            
        return chieu_cao_long_trong, chieu_rong_long_trong, chieu_rong_ngoai, the_tich_vat_the_ml
    except ValueError:
        print("Nhập sai số! Tự động đặt mặc định.")
        return 6.7, 7.3, 7.7, 0.0

# ==================== VÒNG LẶP RESET TOÀN HỆ THỐNG ====================
while True:
    # Thiết lập lại biến chuột cho mỗi phiên chạy mới
    ve_khung_roi = False
    roi_x, roi_y, roi_w, roi_h = -1, -1, -1, -1
    click_y = -1

    # 1. Nhập thông số hình học và cấu hình trừ hao vật thể
    CHIEU_CAO_NUOC_MAX, CHIEU_RONG_TRONG, CHIEU_RONG_NGOAI, THE_TICH_VAT_THE = lay_thong_tin_cau_hinh()

    # 2. Kết nối tới Webcam
    cap = cv2.VideoCapture(0)

    print("\n" + "="*5 + " BƯỚC 1: QUÉT CHUỘT CHỌN TOÀN BỘ CỐC " + "="*5)

    window_step1 = "Buoc_1_Chon_Coc"
    cv2.namedWindow(window_step1)
    cv2.setMouseCallback(window_step1, mouse_event_quet_coc)

    while True:
        ret, init_frame = cap.read()
        if not ret:
            break
        init_frame = cv2.flip(init_frame, 1)
        img_ve = init_frame.copy()
        
        cv2.putText(img_ve, "NHAN GIU CHUOT TRAI VA KEO TOAN BO COC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(img_ve, "SAU KHI KEO XONG - NHAN PHIM ENTER DE TIEP TUC", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        if roi_x != -1 and roi_w > 0 and roi_h > 0:
            cv2.rectangle(img_ve, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (255, 191, 0), 2)
            
        cv2.imshow(window_step1, img_ve)
        key = cv2.waitKey(1) & 0xFF
        if key == 13 or key == 32: 
            break

    # Hủy cửa sổ bước 1 an toàn
    cv2.destroyWindow(window_step1)

    # Định hình khung hộp vùng chọn (ROI)
    roi_box = (roi_x, roi_y, roi_w, roi_h) if roi_x != -1 else (200, 150, 200, 260)
    x_left, y_top, cw, ch = roi_box
    x_right = x_left + cw
    y_bottom = y_top + ch

    print("\n" + "="*5 + " BƯỚC 2: CLICK CHUỘT CHỈ ĐỊNH ĐÁY TRONG " + "="*5)

    if ret:
        display_init = init_frame.copy()
        cv2.rectangle(display_init, (x_left, y_top), (x_right, y_bottom), (255, 191, 0), 2)
        cv2.putText(display_init, "CLICK VAO DAY TRONG TRONG LONG COC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(display_init, "SAU DO NHAN PHIM BAT KY DE CHAY", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        window_step2 = "Buoc_2_Chon_Day"
        cv2.namedWindow(window_step2)
        cv2.setMouseCallback(window_step2, click_event_chon_day)
        
        while click_y == -1:
            cv2.imshow(window_step2, display_init)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        # Kiểm tra tính hợp lệ của tọa độ click chuột
        if y_top < click_y < y_bottom:
            y_bottom_internal = click_y
        else:
            y_bottom_internal = int(y_bottom - (ch * 0.15))
            print(f"-> Tọa độ click không hợp lệ. Tự động ước lượng đáy trong tại Y: {y_bottom_internal}")

        cv2.line(display_init, (x_left, y_bottom_internal), (x_right, y_bottom_internal), (0, 0, 255), 2)
        cv2.imshow(window_step2, display_init)
        cv2.waitKey(0) 
        cv2.destroyWindow(window_step2)

    # Khởi tạo mặc định các biến tương tác trước vòng lặp chính
    do_cong_elip = 0.05
    kich_hoat_tu_dong_day = True
    history_cy = []
    last_alert_time = 0

    print("\n================ HỆ THỐNG ĐANG CHẠY ================")
    print("-> Nhấn phím 'q' tại cửa sổ Camera để TẮT và XUẤT BÁO CÁO CHI TIẾT.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        H_max, W_max = frame.shape[:2]  # Lấy giới hạn kích thước tuyệt đối của camera để chống văng code

        # Giới hạn tọa độ hộp chọn bám sát kích thước thực tế của webcam không cho phép tràn viền
        x_left = max(0, min(W_max - 2, x_left))
        x_right = max(x_left + 2, min(W_max, x_right))
        y_top = max(0, min(H_max - 2, y_top))
        y_bottom = max(y_top + 2, min(H_max, y_bottom))
        y_bottom_internal = max(y_top + 1, min(y_bottom, y_bottom_internal))

        # Cắt vùng ảnh chứa nước bên trong lòng cốc an toàn
        roi = frame[y_top:y_bottom_internal, x_left:x_right]
        
        if roi.size > 0 and roi.shape[0] > 5 and roi.shape[1] > 5:
            # --- [CẢI TIẾN TỰ ĐỘNG QUÉT ĐÁY]: Thu hẹp vùng quét chỉ ở 20% sát đáy, bỏ qua vùng miệng ly bị lóa sáng ---
            if kich_hoat_tu_dong_day:
                dong_bat_dau_vung_day = int(roi.shape[0] * 0.8)
                roi_day_gray = cv2.cvtColor(roi[dong_bat_dau_vung_day:, :], cv2.COLOR_BGR2GRAY)
                roi_day_blurred = cv2.GaussianBlur(roi_day_gray, (5, 5), 0)
                profile_day = np.mean(roi_day_blurred, axis=1)
                sai_phan_day = np.abs(np.diff(profile_day))
                if len(sai_phan_day) > 2:
                    vi_tri_day_thuc = np.argmax(sai_phan_day)
                    if sai_phan_day[vi_tri_day_thuc] > 4:
                        y_bottom_internal = y_top + dong_bat_dau_vung_day + vi_tri_day_thuc

            # --- THUẬT TOÁN ĐỌC PROFILE ĐỘ SÁNG MỰC NƯỚC CHỐNG NHIỄU LY THỦY TINH ---
                        # --- THUẬT TOÁN ĐỌC PROFILE ĐỘ SÁNG MỰC NƯỚC SIÊU NHẠY THỜI GIAN THỰC ---
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            roi_blurred = cv2.GaussianBlur(roi_gray, (5, 5), 0)
            
            # Cắt biên padding 8% để triệt tiêu khúc xạ của thành kính thủy tinh ly
            pad = max(1, int(roi_blurred.shape[0] * 0.08))
            profile_doc = np.mean(roi_blurred[pad:-pad, :], axis=1)
            sai_phan = np.abs(np.diff(profile_doc))
            
            if len(sai_phan) > 5:
                vi_tri_dot_bien = np.argmax(sai_phan)
                # CẢI TIẾN: Hạ ngưỡng sai phân xuống 1 để bắt biên mặt nước cực nhạy ở vùng kính trong suốt
                if sai_phan[vi_tri_dot_bien] >= 1:
                    detected_y = y_top + pad + vi_tri_dot_bien
                else:
                    detected_y = y_bottom_internal
            else:
                detected_y = y_bottom_internal

            # CẢI TIẾN: Giảm bộ nhớ đệm trượt xuống tối đa (chỉ lưu 3 khung hình) để vạch xanh biến thiên ngay lập tức
            history_cy.append(detected_y)
            if len(history_cy) > 3: 
                history_cy.pop(0)
            current_water_y = int(np.mean(history_cy))

            history_cy.append(detected_y)
            if len(history_cy) > 20: 
                history_cy.pop(0)
            current_water_y = int(np.mean(history_cy))
        else:
            current_water_y = y_bottom_internal

        # Khóa an toàn: Tọa độ mực nước không được phép vượt qua ranh giới vạch đáy cốc
        if current_water_y > y_bottom_internal:
            current_water_y = y_bottom_internal

        # Tính toán cấu hình quy đổi từ Pixel sang CM vật lý thời gian thực
        pixel_chua_nuoc = y_bottom_internal - y_top
        cm_per_pixel = CHIEU_CAO_NUOC_MAX / pixel_chua_nuoc if pixel_chua_nuoc > 0 else 0.03
        chieu_cao_tong_ngoai = round((y_bottom - y_top) * cm_per_pixel, 1)
        do_day_day_cm = round((y_bottom - y_bottom_internal) * cm_per_pixel, 1)
        do_day_vo_ben_cm = round((CHIEU_RONG_NGOAI - CHIEU_RONG_TRONG) / 2, 2)

        # 4. TÍNH TOÁN THÔNG SỐ VÀ TRỪ HAO VẬT THỂ
        total_pixel_height = y_bottom_internal - y_top
        if total_pixel_height > 0:
            water_pixel_height = y_bottom_internal - current_water_y
            water_level_pct = int((water_pixel_height / total_pixel_height) * 100)
            water_level_pct = max(0, min(100, water_level_pct))
        else:
            water_level_pct = 0
        
        chieu_cao_nuoc_cm = (water_level_pct / 100.0) * CHIEU_CAO_NUOC_MAX
        chieu_cao_nuoc_cm = max(0.0, chieu_cao_nuoc_cm)
        
        ban_kinh = CHIEU_RONG_TRONG / 2.0
        the_tich_tong_ml = np.pi * (ban_kinh ** 2) * chieu_cao_nuoc_cm
        
        the_tich_nuoc_thuc_te_ml = the_tich_tong_ml - THE_TICH_VAT_THE
        the_tich_nuoc_thuc_te_ml = max(0.0, the_tich_nuoc_thuc_te_ml)

        # 5. THUẬT TOÁN PHÂN LOẠI MỰC NƯỚC
        if water_level_pct == 100:
            status = "CANH BAO TRAN!!!"
            if time.time() - last_alert_time > 3:
                print(f"\033[91m[🚨 NGUY HIỂM]: CẢNH BÁO TRÀN! Nước đã đạt 100%!\033[0m")
                last_alert_time = time.time()
        elif water_level_pct > 70:
            status = "Muc Nuoc Nhieu"
        elif 31 <= water_level_pct <= 70:
            status = "Muc Nuoc Vua"
        else:
            status = "Muc Nuoc It"

        cuoi_muc_nuoc_pct = water_level_pct
        cuoi_chieu_cao_nuoc = round(chieu_cao_nuoc_cm, 1)
        cuoi_the_tich_tong = int(round(the_tich_tong_ml))
        cuoi_the_tich_thuc = int(round(the_tich_nuoc_thuc_te_ml))
        cuoi_trang_thai_nuoc = status

                # ==================== 6. VẼ GIAO DIỆN ĐỒ HỌA ĐỘNG LÊN KHUNG HÌNH CAMERA ====================
        cv2.rectangle(frame, (x_left, y_top), (x_right, y_bottom), (255, 191, 0), 2)
        
        # Khởi tạo riêng biệt 2 biến độ cong nếu chưa có trong phiên chạy
        if 'do_cong_nuoc' not in locals():
            do_cong_nuoc = 0.05  # Độ cong ban đầu của vạch nước xanh lá
        if 'do_cong_day' not in locals():
            do_cong_day = 0.05   # Độ cong ban đầu của vạch đáy màu đỏ
            
        ban_kinh_truc_ngang = int((x_right - x_left) / 2)
        vi_tri_tam_x = x_left + ban_kinh_truc_ngang
        
        # Tính toán bán kính trục dọc elip riêng cho từng vạch
        ban_kinh_doc_nuoc = int((y_bottom - y_top) * do_cong_nuoc)
        ban_kinh_doc_day = int((y_bottom - y_top) * do_cong_day)
        
        # Vẽ vạch đáy elip màu đỏ 3D (Sử dụng độ cong riêng ban_kinh_doc_day)
        cv2.ellipse(frame, (vi_tri_tam_x, y_bottom_internal), (ban_kinh_truc_ngang, ban_kinh_doc_day), 0, 0, 180, (0, 0, 255), 2)
        
        # Vẽ vạch nước elip màu xanh lá 3D (Sử dụng độ cong riêng ban_kinh_doc_nuoc)
        mau_vach_nuoc = (0, 0, 255) if water_level_pct == 100 else (0, 255, 0)
        cv2.ellipse(frame, (vi_tri_tam_x, current_water_y), (ban_kinh_truc_ngang, ban_kinh_doc_nuoc), 0, 0, 180, mau_vach_nuoc, 3)
        
        # Hiển thị thông tin chữ lên màn hình Camera
        cv2.putText(frame, f"Muc nuoc: {water_level_pct}% (Cao: {cuoi_chieu_cao_nuoc} cm)", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if THE_TICH_VAT_THE > 0:
            cv2.putText(frame, f"Nuoc thuc te (da tru hao): {cuoi_the_tich_thuc} ml", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
        else:
            cv2.putText(frame, f"The tich: ~ {cuoi_the_tich_thuc} ml", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        color_status = (0, 0, 255) if water_level_pct == 100 else ((0, 255, 255) if "Vua" in status else (255, 255, 255))
        cv2.putText(frame, f"Trang thai: {status}", (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_status, 2)
        
        # Menu hướng dẫn điều khiển phím bấm mới tách biệt
        che_do_day = "TU DONG" if kich_hoat_tu_dong_day else "THU CONG (i/k)"
        cv2.putText(frame, f"Cong Nuoc (w/s): {int(do_cong_nuoc*100)}% | Cong Day (a/d): {int(do_cong_day*100)}% | Day (m): {che_do_day}", (30, H_max - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        
        cv2.imshow("He_Thong_Do_Nuoc_Thong_Minh", frame)
        
        # --- BỘ LẮNG NGHE BÀN PHÍM ĐIỀU KHIỂN TÁCH BIỆT ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        # Điều chỉnh độ cong vạch nước XANH LÁ độc lập
        elif key == ord('w'):
            do_cong_nuoc = min(0.15, do_cong_nuoc + 0.01)
        elif key == ord('s'):
            do_cong_nuoc = max(0.01, do_cong_nuoc - 0.01)
            
        # Điều chỉnh độ cong vạch đáy ĐỎ độc lập
        elif key == ord('a'):  # Phím 'a' để GIẢM độ cong vạch đỏ
            do_cong_day = max(0.01, do_cong_day - 0.01)
        elif key == ord('d'):  # Phím 'd' để TĂNG độ cong vạch đỏ
            do_cong_day = min(0.15, do_cong_day + 0.01)
            
        # Chuyển đổi chế độ và tinh chỉnh tọa độ Y của vạch đáy
        elif key == ord('m'):
            kich_hoat_tu_dong_day = not kich_hoat_tu_dong_day
            print(f"-> Chuyen che do quet day sang: {'TU DONG' if kich_hoat_tu_dong_day else 'THU CONG'}")
        elif key == ord('i') and not kich_hoat_tu_dong_day:
            y_bottom_internal = max(y_top + 5, y_bottom_internal - 1)
        elif key == ord('k') and not kich_hoat_tu_dong_day:
            y_bottom_internal = min(y_bottom - 1, y_bottom_internal + 1)

    # Giải phóng tài nguyên camera sau khi kết thúc phiên chạy
    cap.release()
    cv2.destroyAllWindows()

    # --- KHU VỰC IN BÁO CÁO CHI TIẾT RA TERMINAL ---
    print("\n" + "="*20 + " BÁO CÁO CHI TIẾT HỆ THỐNG DO LƯỜNG " + "="*20)
    print(f" 1. Chiều cao tổng thể vỏ ngoài cốc:   {chieu_cao_tong_ngoai} cm")
    print(f" 2. Chiều cao lòng trong chứa nước:    {CHIEU_CAO_NUOC_MAX} cm")
    print(f" 3. Đường kính vỏ ngoài cốc:           {CHIEU_RONG_NGOAI} cm")
    print(f" 4. Đường kính lòng trong cốc:         {CHIEU_RONG_TRONG} cm")
    print(f" 5. Độ dày của thành/vỏ bên cốc:        {do_day_vo_ben_cm} cm")
    print(f" 6. Độ dày phần ĐÁY đặc của cốc:       {do_day_day_cm} cm")
    print(f" 7. Thể tích vật thể chiếm chỗ đã trừ: {THE_TICH_VAT_THE} ml (tương đương {THE_TICH_VAT_THE} g)")
    print("-" * 55)
    print(f" >> KẾT QUẢ PHẦN TRĂM MỰC NƯỚC:       {cuoi_muc_nuoc_pct} %")
    print(f" >> KẾT QUẢ DUNG TÍCH TỔNG (Có vật):   {cuoi_the_tich_tong} ml")
    print(f" >> KẾT QUẢ DUNG TÍCH THỰC (Không vật): {cuoi_the_tich_thuc} ml")
    print(f" >> ĐÁNH GIÁ TRẠNG THÁI MỰC NƯỚC CUỐI: {cuoi_trang_thai_nuoc}")
    print("="*56 + "\n")

    # --- TÍNH NĂNG ĐẶT LẠI HỆ THỐNG (RESET) ---
    hoi_reset = input("Ban co muon THAY DOI THONG SO hoac DO COC KHAC (Reset he thong) khong? (y/n): ")
    if hoi_reset.lower() != 'y':
        print(">> Da thoat chuong trinh thanh cong. Tam biet ban!")
        break
