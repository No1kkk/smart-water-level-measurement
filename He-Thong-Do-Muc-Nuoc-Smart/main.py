import cv2  # Thu viện tích hợp thị giác máy tính: Quản lý luồng video, tiền xử lý ảnh và kết xuất đồ họa
import numpy as np  # Thư viện đại số tuyến tính: Xử lý ma trận điểm ảnh (pixel) và tính toán hình học hiệu năng cao
import time  # Thư viện kiểm soát thời gian: Đồng bộ luồng dữ liệu và thiết lập bộ đếm thời gian thực (cooldown) cho hệ thống

# --- KHỞI TẠO CÁC BIẾN TOÀN CỤC CHUẨN ĐỊNH VỊ VÀ ĐỒ HỌA ---
ve_khung_roi = False  # Cờ hiệu (Flag) trạng thái quét chuột chọn vùng quan tâm (ROI)
roi_x, roi_y, roi_w, roi_h = -1, -1, -1, -1  # Tọa độ gốc, chiều rộng và chiều cao của hộp giới hạn (Bounding Box) chiếc cốc
click_y = -1  # Tọa độ trục dọc vật lý lưu vị trí vạch đáy cốc do người dùng chỉ định

# Các tham số cấu hình hệ số phối cảnh (Perspective) giữ xuyên suốt chu kỳ chạy hệ thống
do_cong_nuoc = 0.05  # Tỉ lệ bán kính trục đứng của Ellipse mô phỏng mặt nước
do_cong_day = 0.05  # Tỉ lệ bán kính trục đứng của Ellipse mô phỏng đáy cốc

# Cấu trúc lưu trữ dữ liệu đầu ra phục vụ xuất báo cáo (Report Generation)
cuoi_muc_nuoc_pct = 0  # Giá trị phần trăm mực nước cuối cùng đạt được
cuoi_chieu_cao_nuoc = 0.0  # Chiều cao mực nước thực tế tính theo đơn vị cm
cuoi_the_tich_tong = 0  # Tổng dung tích chất lỏng bao gồm cả vật thể chiếm chỗ (ml)
cuoi_the_tich_thuc = 0  # Dung tích chất lỏng thực tế sau khi đã triệt tiêu sai số chiếm chỗ (ml)
cuoi_trang_thai_nuoc = "Chưa xác định"  # Chuỗi trạng thái phân loại mực nước phục vụ hiển thị HUD

# --- ĐỊNH NGHĨA CÁC HÀM TIỀN XỬ LÝ VÀ ĐỒNG BỘ THÔNG SỐ VẬT LÝ ---
def click_event_chon_day(event, x, y, flags, param):
    """Hàm xử lý sự kiện ngắt chuột (Mouse Callback) để định vị mốc không gian 'Vạch số 0' tại đáy cốc"""
    global click_y
    if event == cv2.EVENT_LBUTTONDOWN:  # Bắt sự kiện nhấn chuột trái
        click_y = y
        print(f"-> Đã ghi nhận vạch đáy trong tại tọa độ Y: {y} pixel")

def mouse_event_quet_coc(event, x, y, flags, param):
    """Hàm xây dựng vùng quan tâm (ROI) bằng cơ chế kéo thả chuột trái đa trạng thái"""
    global roi_x, roi_y, roi_w, roi_h, ve_khung_roi
    if event == cv2.EVENT_LBUTTONDOWN:  # Khởi tạo điểm neo (Anchor Point) gốc cho Bounding Box
        roi_x, roi_y = x, y
        ve_khung_roi = True
    elif event == cv2.EVENT_MOUSEMOVE:  # Cập nhật kích thước Preview động khi người dùng di chuyển chuột
        if ve_khung_roi:
            roi_w = abs(x - roi_x)  # Sử dụng trị tuyệt đối chống lỗi tràn mảng (IndexError) khi kéo ngược trục X
            roi_h = abs(y - roi_y)  # Sử dụng trị tuyệt đối chống lỗi tràn mảng (IndexError) khi kéo ngược trục Y
    elif event == cv2.EVENT_LBUTTONUP:  # Xác lập và chốt ma trận tọa độ cố định của chiếc cốc
        ve_khung_roi = False
        roi_w = abs(x - roi_x)
        roi_h = abs(y - roi_y)

def lay_thong_tin_cau_hinh():
    """Hàm thiết lập hằng số quy đổi vật lý và ma trận trừ hao thể tích vật thể không định hình"""
    print("\n" + "="*10 + " CẤU HÌNH THÔNG SỐ CỐC NƯỚC " + "="*10)
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
                # Áp dụng định luật vật lý quy đổi tỷ trọng chất lỏng tiêu chuẩn (d = 1g/ml)
                the_tich_vat_the_ml = round(khoi_luong_g / 1.0, 1)
            print(f"-> Hệ thống sẽ tự động trừ đi {the_tich_vat_the_ml} ml vật thể chiếm chỗ.")
            
        return chieu_cao_long_trong, chieu_rong_long_trong, chieu_rong_ngoai, the_tich_vat_the_ml
    except ValueError:  # Cơ chế bẫy lỗi ngoại lệ: Khóa an toàn chống sập code khi người dùng nhập sai định dạng số
        print("Nhập sai số! Tự động đặt mặc định.")
        return 6.7, 7.3, 7.7, 0.0

# Định danh chuỗi ký tự quản lý hệ thống phân tầng cửa sổ (Window Management) của OpenCV
window_step1 = "Buoc_1_Chon_Coc"
window_step2 = "Buoc_2_Chon_Day"
window_main = "He_Thong_Do_Nuoc_Thong_Minh"

# ==================== VÒNG LẶP TUẦN HOÀN RESET HỆ THỐNG ĐỒ ÁN ====================
while True:
    # Đồng bộ giao diện: Giải phóng luồng đồ họa cũ tránh xung đột khóa tiến trình hiển thị (Not Responding)
    cv2.destroyAllWindows()
    cv2.waitKey(1) 

    # Trả các biến trạng thái chuột nội bộ về trạng thái nguyên bản trước một phiên chạy mới
    ve_khung_roi = False
    roi_x, roi_y, roi_w, roi_h = -1, -1, -1, -1
    click_y = -1

    # Khởi chạy bước nhập liệu hằng số hình học từ luồng nhập Terminal độc lập
    CHIEU_CAO_NUOC_MAX, CHIEU_RONG_TRONG, CHIEU_RONG_NGOAI, THE_TICH_VAT_THE = lay_thong_tin_cau_hinh()

    # Kích hoạt luồng phần cứng: Tạo kết nối và mở luồng dữ liệu hình ảnh từ Webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không thể mở Webcam!")
        break

    print("\n" + "="*5 + " BƯỚC 1: QUÉT CHUỘT CHỌN TOÀN BỘ CỐC " + "="*5)
    cv2.namedWindow(window_step1)
    cv2.setMouseCallback(window_step1, mouse_event_quet_coc)  # Đăng ký hàm bắt sự kiện tương tác chuột cho bước 1

    Webcam_OK = True
    while True:
        ret, init_frame = cap.read()  # Thu thập một khung hình (Frame Capture) từ bộ đệm của camera
        if not ret:
            print("Lỗi đọc khung hình từ Webcam.")
            Webcam_OK = False
            break
        init_frame = cv2.flip(init_frame, 1)  # Lật đối xứng gương khung hình để thuận tiện tương tác trực quan
        img_ve = init_frame.copy()  # Sao chép vùng nhớ ảnh để kết xuất đồ họa tĩnh, bảo vệ dữ liệu khung hình gốc
        
        # Kết xuất các lớp văn bản hướng dẫn quy trình tương tác người dùng lên màn hình HUD
        cv2.putText(img_ve, "NHAN GIU CHUOT TRAI VA KEO TOAN BO COC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(img_ve, "SAU KHI KEO XONG - NHAN PHIM ENTER DE TIEP TUC", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Kiểm tra tính hợp lệ và dựng khung hình chữ nhật hiển thị vùng ROI đang chọn theo thời gian thực
        if roi_x != -1 and roi_w > 0 and roi_h > 0:
            cv2.rectangle(img_ve, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (255, 191, 0), 2)
            
        cv2.imshow(window_step1, img_ve)
        key = cv2.waitKey(1) & 0xFF  # Chờ ngắt từ bàn phím với chu kỳ lấy mẫu 1ms
        if key == 13 or key == 32:  # Thoát luồng tiền xử lý bước 1 khi người dùng nhấn phím Enter (13) hoặc Space (32)
            break

    # Giải phóng tài nguyên cửa sổ bước 1 đồng bộ nhằm dọn dẹp RAM đồ họa
    cv2.destroyWindow(window_step1)
    cv2.waitKey(1)

    if not Webcam_OK:
        cap.release()
        break

    # Thiết lập tọa độ không gian hộp chọn (Bounding Box) an toàn, tự động nạp vùng giả định nếu chuột lỗi
    roi_box = (roi_x, roi_y, roi_w, roi_h) if roi_x != -1 else (200, 150, 200, 260)
    x_left, y_top, cw, ch = roi_box
    x_right = x_left + cw
    y_bottom = y_top + ch
    y_bottom_internal = y_bottom  # Gán giá trị ranh giới đáy trong mặc định ban đầu

    print("\n" + "="*5 + " BƯỚC 2: CLICK CHUỘT CHỈ ĐỊNH ĐÁY TRONG " + "="*5)
    cv2.namedWindow(window_step2)
    cv2.setMouseCallback(window_step2, click_event_chon_day)  # Đăng ký hàm ngắt chuột xác định mặt phẳng đáy số 0
    
    step2_passed = True
    while True:
        img_step2_show = init_frame.copy()  # Tạo bản sao luồng tĩnh bảo toàn ma trận gốc
        cv2.rectangle(img_step2_show, (x_left, y_top), (x_right, y_bottom), (255, 191, 0), 2)  # Vẽ viền ngoài cốc
        
        # Kết xuất thông tin HUD hướng dẫn tương tác thiết lập điểm đáy vật lý
        cv2.putText(img_step2_show, "CLICK VAO DAY TRONG TRONG LONG COC", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(img_step2_show, "SAU DO NHAN PHIM ENTER DE XAC NHAN", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Hiển thị vạch đường thẳng mặt cắt ngang (Cross-section) theo tọa độ click chuột thực tế
        if click_y != -1:
            cv2.line(img_step2_show, (x_left, click_y), (x_right, click_y), (0, 0, 255), 2)
            
        cv2.imshow(window_step2, img_step2_show)
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Xác nhận lưu thông số tọa độ bằng nút Enter
            break
        elif key == ord('q') or key == 27:  # Hủy phiên làm việc nếu nhấn phím 'q' hoặc ESC (27)
            step2_passed = False
            break
            
    if not step2_passed:
        cv2.destroyWindow(window_step2)
        cap.release()
        break

    # Thuật toán kiểm định tính hợp lệ của không gian click chuột so với cấu trúc chiếc cốc
    if y_top < click_y < y_bottom:
        y_bottom_internal = click_y  # Phê duyệt tọa độ đáy trong do người dùng chỉ định
    else:
        # Cơ chế hồi quy (Fallback): Tự động ước lượng toán học độ dày đáy cốc bằng 15% tổng chiều cao hộp chọn
        y_bottom_internal = int(y_bottom - (ch * 0.15))
        print(f"-> Tọa độ click không hợp lệ. Tự động ước lượng đáy trong tại Y: {y_bottom_internal}")

    cv2.destroyWindow(window_step2)
    cv2.waitKey(1)  # Giải phóng bộ nhớ đệm luồng đồ họa bước 2

    # Khởi tạo các siêu tham số (Hyperparameters) kiểm soát bộ lọc động lực học
    kich_hoat_tu_dong_day = True  # Bật cờ thuật toán tối ưu hóa thích nghi vị trí vạch đáy
    history_cy = []  # Khởi tạo bộ nhớ mảng trượt lưu trữ biên độ mực nước qua từng chu kỳ
    last_alert_time = 0  # Biến mốc thời gian khống chế tần suất cảnh báo nguy hiểm

    print("\n================ HỆ THỐNG ĐANG CHẠY ================")
    print("-> Nhấn phím 'q' tại cửa sổ Camera để TẮT và XUẤT BÁO CÁO CHI TIẾT.")

    # ==================== VÒNG LẶP XỬ LÝ ẢNH REAL-TIME CHÍNH ====================
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Mất kết nối Camera giữa chừng.")
            break
            
        frame = cv2.flip(frame, 1)  # Đồng bộ hướng tương tác thực tế người dùng
        H_max, W_max = frame.shape[:2]  # Trích xuất chiều cao và chiều rộng tuyệt đối của ma trận ảnh đầu vào

        # Thuật toán kẹp dải biến thiên (Clamping Algorithm) ngăn lỗi tràn bộ nhớ mảng ma trận (IndexError)
        x_left = max(0, min(W_max - 2, x_left))
        x_right = max(x_left + 2, min(W_max, x_right))
        y_top = max(0, min(H_max - 2, y_top))
        y_bottom = max(y_top + 2, min(H_max, y_bottom))
        y_bottom_internal = max(y_top + 1, min(y_bottom, y_bottom_internal))

        # Khởi tạo biến đáy động để cô lập, chống hiện tượng co rút thu hẹp vùng ROI tuần hoàn
        y_bottom_dynamic = y_bottom_internal
        roi = frame[y_top:y_bottom_internal, x_left:x_right]  # Phân tách vùng không gian lòng cốc
        
        if roi.size > 0 and roi.shape[0] > 5 and roi.shape[1] > 5:
            # --- THUẬT TOÁN TINH CHỈNH ĐÁY ĐỘNG THÍCH NGHI (Adaptive Base Detection) ---
            if kich_hoat_tu_dong_day:
                dong_bat_dau_vung_day = int(roi.shape[0] * 0.8)  # Thu hẹp khu vực phân tích chỉ quét 20% biên sát đáy
                roi_day_gray = cv2.cvtColor(roi[dong_bat_dau_vung_day:, :], cv2.COLOR_BGR2GRAY)  # Ép kênh xám tối ưu tính toán
                roi_day_blurred = cv2.GaussianBlur(roi_day_gray, (5, 5), 0)  # Loại bỏ nhiễu tần số cao bằng nhân Gaussian
                profile_day = np.mean(roi_day_blurred, axis=1)  # Tích phân độ sáng trung bình theo hàng ngang trục X
                sai_phan_day = np.abs(np.diff(profile_day))  # Áp dụng toán tử đạo hàm sai phân bậc nhất tìm biên độ dốc độ sáng
                if len(sai_phan_day) > 2:
                    vi_tri_day_thuc = np.argmax(sai_phan_day)  # Trích xuất cực trị (Điểm đột biến độ sáng mạnh nhất)
                    if sai_phan_day[vi_tri_day_thuc] > 4:  # Bộ lọc ngưỡng biên độ chống lọt nhiễu lóa sáng
                        y_bottom_dynamic = y_top + dong_bat_dau_vung_day + vi_tri_day_thuc

            # --- THUẬT TOÁN PHÂN TÍCH PROFILE ĐỘ SÁNG MỰC NƯỚC (Vertical Intensity Profiling) ---
            roi_nuoc = frame[y_top:y_bottom_dynamic, x_left:x_right]  # Cắt vùng không gian chứa nước theo đáy động mới
            roi_gray = cv2.cvtColor(roi_nuoc, cv2.COLOR_BGR2GRAY)  # Chuyển đổi không gian màu BGR sang Gray-scale 1 kênh
            roi_blurred = cv2.GaussianBlur(roi_gray, (5, 5), 0)  # Triệt tiêu nhiễu hạt (Salt-and-pepper noise) của phần cứng cảm biến
            
            # Cắt biên Padding 8% chiều ngang để cô lập và loại bỏ nhiễu khúc xạ lóa sáng tại thành ly thủy tinh
            pad_x = max(1, int(roi_blurred.shape[1] * 0.08))
            profile_doc = np.mean(roi_blurred[:, pad_x:-pad_x], axis=1)  # Tính toán Profile độ sáng trung bình trên trục dọc Y
            sai_phan = np.abs(np.diff(profile_doc))  # Thực hiện đạo hàm sai phân rời rạc để tìm ranh giới phân tách pha (Mặt nước)
            
            if len(sai_phan) > 5:
                vi_tri_dot_bien = np.argmax(sai_phan)  # Định vị tọa độ hàng ngang có mức độ biến thiên quang học lớn nhất
                if sai_phan[vi_tri_dot_bien] >= 3:  # Đặt ngưỡng biên độ tối thiểu = 3 để loại bỏ nhiễu rung từ môi trường ánh sáng phòng
                    detected_y = y_top + vi_tri_dot_bien
                else:
                    detected_y = y_bottom_dynamic  # Phục hồi về vị trí đáy nếu không phát hiện bước nhảy quang học hợp lệ
            else:
                detected_y = y_bottom_dynamic

            # --- BỘ LỌC TRUNG BÌNH TRƯỢT THỜI GIAN THỰC (Moving Average Filter) ---
            history_cy.append(detected_y)  # Cập nhật tọa độ mới vào hàng đợi bộ nhớ đệm
            if len(history_cy) > 5: 
                history_cy.pop(0)  # Duy trì độ dài cửa sổ trượt (Window size = 5) nhằm triệt tiêu độ trễ hiển thị (Lag)
            current_water_y = int(np.mean(history_cy))  # Tính giá trị kỳ vọng toán học để đường đo đứng im, mịn màng
        else:
            current_water_y = y_bottom_dynamic

        # Khóa an toàn logic tuyệt đối: Tọa độ mực nước không được vượt quá giới hạn biên vật lý của đáy cốc
        if current_water_y > y_bottom_dynamic:
            current_water_y = y_bottom_dynamic
        # --- 4. THUẬT TOÁN QUY ĐỔI KHÔNG GIAN VÀ TRỪ HAO VẬT LÝ ---
        pixel_chua_nuoc = y_bottom_internal - y_top  # Chiều cao lòng trong tính bằng đơn vị điểm ảnh (pixel)
        # Thiết lập hệ số phân giải vật lý (Pixel Pitch resolution) để ánh xạ 1 pixel bằng bao nhiêu cm
        cm_per_pixel = CHIEU_CAO_NUOC_MAX / pixel_chua_nuoc if pixel_chua_nuoc > 0 else 0.03
        
        # Áp dụng hàm tuyến tính quy đổi các thông số hình học của cốc từ ma trận pixel sang cm thực tế
        chieu_cao_tong_ngoai = round((y_bottom - y_top) * cm_per_pixel, 1)
        do_day_day_cm = round((y_bottom - y_bottom_internal) * cm_per_pixel, 1)
        do_day_vo_ben_cm = round((CHIEU_RONG_NGOAI - CHIEU_RONG_TRONG) / 2, 2)

        total_pixel_height = y_bottom_internal - y_top
        if total_pixel_height > 0:
            # Tính toán tỉ lệ phần trăm dung tích dựa trên tỷ lệ phân biên trục đứng (Y-axis ratio)
            water_pixel_height = y_bottom_internal - current_water_y
            water_level_pct = int((water_pixel_height / total_pixel_height) * 100)
            water_level_pct = max(0, min(100, water_level_pct))  # Ngưỡng hóa giá trị trong dải [0 - 100]%
        else:
            water_level_pct = 0

        chieu_cao_nuoc_cm = max(0.0, (water_level_pct / 100.0) * CHIEU_CAO_NUOC_MAX)
        ban_kinh = CHIEU_RONG_TRONG / 2.0
        
        # Áp dụng công thức hình học không gian tính thể tích khối trụ tiêu chuẩn: V = pi * R^2 * h
        the_tich_tong_ml = np.pi * (ban_kinh ** 2) * chieu_cao_nuoc_cm
        # Thực hiện phép trừ toán học nhằm triệt tiêu sai số chiếm chỗ của vật thể không định hình
        the_tich_nuoc_thuc_te_ml = max(0.0, the_tich_tong_ml - THE_TICH_VAT_THE)

        # --- 5. MÔ HÌNH PHÂN LOẠI TRẠNG THÁI VÀ LOGIC KHỐNG CHẾ TẦN SUẤT CẢNH BÁO ---
        if water_level_pct >= 98:  # Ngưỡng 98% giúp bù trừ sai số quang học do hiện tượng lóa sáng viền cốc
            status = "CANH BAO TRAN!!!"
            # Thiết lập bộ đếm thời gian Cooldown (3 giây) ngăn chặn hiện tượng tràn ngập log (Terminal Flooding)
            if time.time() - last_alert_time > 3:
                print(f"\033[91m[🚨 NGUY HIỂM]: CẢNH BÁO TRÀN! Nước đã đầy cốc!\033[0m")
                last_alert_time = time.time()  # Cập nhật lại mốc thời gian phát ngắt cảnh báo gần nhất
        elif water_level_pct > 70:
            status = "Muc Nuoc Nhieu"
        elif 31 <= water_level_pct <= 70:
            status = "Muc Nuoc Vua"
        elif 0 < water_level_pct < 31:
            status = "Muc Nuoc It"
        else:
            status = "Coc Rong"

        # Đồng bộ dữ liệu ra các biến trạng thái toàn cục phục vụ kết xuất báo cáo cuối chu kỳ
        cuoi_muc_nuoc_pct = water_level_pct
        cuoi_chieu_cao_nuoc = round(chieu_cao_nuoc_cm, 1)
        cuoi_the_tich_tong = int(round(the_tich_tong_ml))
        cuoi_the_tich_thuc = int(round(the_tich_nuoc_thuc_te_ml))
        cuoi_trang_thai_nuoc = status

        # --- 6. KẾT XUẤT ĐỒ HỌA VÀ ĐỒNG BỘ PHỐI CẢNH 3D (HUD GERNERATION) ---
        cv2.rectangle(frame, (x_left, y_top), (x_right, y_bottom), (255, 191, 0), 2)  # Dựng khung định vị cốc
        ban_kinh_truc_ngang = max(1, int((x_right - x_left) / 2))
        vi_tri_tam_x = x_left + ban_kinh_truc_ngang

        # Tính toán bán kính trục đứng của Ellipse dựa trên các tham số cấu hình phối cảnh góc nhìn
        ban_kinh_doc_nuoc = max(1, int((y_bottom - y_top) * do_cong_nuoc))
        ban_kinh_doc_day = max(1, int((y_bottom - y_top) * do_cong_day))
        
        # Kết xuất đồ họa cung Ellipse mô phỏng mặt phẳng đáy (Góc vẽ 0 đến 180 độ cho nửa cung dưới)
        cv2.ellipse(frame, (vi_tri_tam_x, y_bottom_internal), (ban_kinh_truc_ngang, ban_kinh_doc_day), 0, 0, 180, (0, 0, 255), 2)

        # Thuật toán tịnh tiến dịch chuyển tâm trục Y nhằm bù trừ độ lệch quang sai hình học do góc nghiêng webcam
        vi_tri_vach_nuoc_y = current_water_y + int(ban_kinh_doc_nuoc * 1.6)
        vi_tri_vach_nuoc_y = min(y_bottom_internal, vi_tri_vach_nuoc_y)  # Khóa an toàn ngăn vạch nước vượt đáy

        # Kết xuất đồ họa cung Ellipse mô phỏng mặt nước (Góc vẽ 0 đến -180 độ uốn cong ngược lên trên)
        mau_vach_nuoc = (0, 0, 255) if water_level_pct >= 98 else (0, 255, 0)
        cv2.ellipse(frame, (vi_tri_tam_x, vi_tri_vach_nuoc_y), (ban_kinh_truc_ngang, ban_kinh_doc_nuoc), 0, 0, -180, mau_vach_nuoc, 3)

        # Chèn các lớp văn bản hiển thị thông tin đo lường thời gian thực lên màn hình camera
        cv2.putText(frame, f"Muc nuoc: {water_level_pct}% (Cao: {cuoi_chieu_cao_nuoc} cm)", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        if THE_TICH_VAT_THE > 0:
            cv2.putText(frame, f"Nuoc thuc te (da tru hao): {cuoi_the_tich_thuc} ml", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 255, 50), 2)
        else:
            cv2.putText(frame, f"The tich: ~ {cuoi_the_tich_thuc} ml", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Chuyển đổi màu sắc chuỗi ký tự trạng thái theo mức độ nguy hiểm của mực nước
        color_status = (0, 0, 255) if water_level_pct >= 98 else ((0, 255, 255) if "Vua" in status else (0, 255, 0))
        cv2.putText(frame, f"Trang thai: {status}", (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_status, 2)

        # Vẽ Menu hướng dẫn các phím ngắt tinh chỉnh thông số ở góc dưới khung hình
        che_do_day = "TU DONG" if kich_hoat_tu_dong_day else "THU CONG (i/k)"
        cv2.putText(frame, f"Cong Nuoc(w/s): {int(do_cong_nuoc * 100)}% | Cong Day(a/d): {int(do_cong_day * 100)}% | Quet Day(m): {che_do_day}", (15, H_max - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        cv2.imshow(window_main, frame)

        # --- 7. BỘ LẮNG NGHE VÀ XỬ LÝ SỰ KIỆN BÀN PHÍM (KEYBOARD INTERRUPT HANDLER) ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # Ngắt vòng lặp chính để kết thúc phiên và xuất báo cáo
            break
        elif key == ord('w'):  # Tăng biên độ cong Ellipse mặt nước
            do_cong_nuoc = min(0.15, do_cong_nuoc + 0.005)
        elif key == ord('s'):  # Giảm biên độ cong Ellipse mặt nước
            do_cong_nuoc = max(0.005, do_cong_nuoc - 0.005)
        elif key == ord('a'):  # Giảm biên độ cong Ellipse đáy cốc
            do_cong_day = max(0.005, do_cong_day - 0.005)
        elif key == ord('d'):  # Tăng biên độ cong Ellipse đáy cốc
            do_cong_day = min(0.15, do_cong_day + 0.005)
        elif key == ord('m'):  # Đảo trạng thái cơ chế quét vạch đáy (Tự động / Thủ công)
            kich_hoat_tu_dong_day = not kich_hoat_tu_dong_day
            print(f"-> Chuyen che do quet day sang: {'TU DONG' if kich_hoat_tu_dong_day else 'THU CONG'}")
        elif key == ord('i') and not kich_hoat_tu_dong_day:  # Dịch chuyển vạch đáy thủ công lên trên
            y_bottom_internal = max(y_top + 5, y_bottom_internal - 1)
        elif key == ord('k') and not kich_hoat_tu_dong_day:  # Dịch chuyển vạch đáy thủ công xuống dưới
            y_bottom_internal = min(y_bottom - 1, y_bottom_internal + 1)

    # Giải phóng luồng phần cứng của camera để dọn dẹp tài nguyên hệ thống
    cap.release()

    # Hủy toàn bộ cửa sổ hiển thị đồ họa của OpenCV
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # Ép hạt nhân OpenCV cập nhật giải phóng luồng giao diện lập tức trên hệ điều hành

    # --- 8. KHU VỰC KẾT XUẤT BÁO CÁO TỔNG HỢP RA TERMINAL (LOG GENERATOR) ---
    print("\n" + "="*20 + " BÁO CÁO CHI TIẾT HỆ THỐNG DO LƯỜNG " + "="*20)
    print(f" 1. Chiều cao tổng thể vỏ ngoài cốc:   {chieu_cao_tong_ngoai} cm")
    print(f" 2. Chiều cao lòng trong chứa nước:    {CHIEU_CAO_NUOC_MAX} cm")
    print(f" 3. Đường kính vỏ ngoài cốc:           {CHIEU_RONG_NGOAI} cm")
    print(f" 4. Đường kính lòng trong cốc:         {CHIEU_RONG_TRONG} cm")
    print(f" 5. Độ dày của thành/vỏ bên cốc:        {do_day_vo_ben_cm} cm")
    print(f" 6. Độ dày phần ĐÁY đặc của cốc:       {do_day_day_cm} cm")
    print(f" 7. Thể tích vật thể chiếm chỗ đã trừ: {THE_TICH_VAT_THE} ml")
    print("-" * 55)
    print(f" >> KẾT QUẢ PHẦN TRĂM MỰC NƯỚC:       {cuoi_muc_nuoc_pct} %")
    print(f" >> KẾT QUẢ DUNG TÍCH TỔNG (Có vật):   {cuoi_the_tich_tong} ml")
    print(f" >> KẾT QUẢ DUNG TÍCH THỰC (Không vật): {cuoi_the_tich_thuc} ml")
    print(f" >> ĐÁNH GIÁ TRẠNG THÁI MỰC NƯỚC CUỐI: {cuoi_trang_thai_nuoc}")
    print("="*56 + "\n")

    # --- 9. LOGIC RESET TUẦN HOÀN TOÀN HỆ THỐNG ---
    hoi_reset = input("Ban co muon THAY DOI THONG SO hoac DO COC KHAC (Reset he thong) khong? (y/n): ")
    if hoi_reset.lower() != 'y':
        print(">> Da thoat chuong trinh thanh cong. Tam biet ban!")
        break
