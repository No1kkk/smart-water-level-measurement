"""
HE THONG DO MUC NUOC THONG MINH - SMART WATER LEVEL MEASUREMENT
================================================================
Mo ta: Camera giam sat khay thiet bi do luong ti le va phan loai dung tich nuoc
       trong coc thuy tinh hinh tru tron thanh 3 loai: It, Vua, Nhieu + Canh bao tran.
Nguyen ly: Toan tu sai phan tren Profile cuong do sang (6-Layer Pipeline)
Tac gia: [Pham Thien Vu]
================================================================
"""

import cv2
import numpy as np
import time
from typing import Tuple
import traceback

# ==================== CAU HINH HE THONG ====================
class SystemConfig:
    """Lop cau hinh tap trung cho he thong"""
    DO_CONG_NUOC = 0.05             # Do cong vach nuoc GREEN 5%
    DO_CONG_DAY = 0.05              # Do cong vach nuoc RED 5%
    MOVING_AVG_WINDOW = 5           # So khung hinh de tinh trung binh
    GAUSSIAN_KERNEL = (5, 5)        # Kich thuoc ma tran Gaussian Blur (lam mo)
    PADDING_RATIO = 0.05            # Cat b0o vien trai/phai cua ROI
    MIN_GRADIENT_THRESHOLD = 2      # Nguong do doc toi thieu de nhan biet day la mat nuoc
    THRESHOLD_LOW = 30              # Nguong phan loai 'muc nuoc it'
    THRESHOLD_MEDIUM = 70           # Nguong phan loai 'muc nuoc vua'
    THRESHOLD_HIGH = 98             # Nguong canh bao tran
    ALERT_COOLDOWN = 3.0            # Thoi gian giua 2 lan canh bao
    OFFSET_NUOC = 15                # Offset nang vach nuoc len (15 pixel) de bu sai so
    
    def __init__(self):
        self.chieu_cao_max, self.chieu_rong_trong, self.chieu_rong_ngoai, self.the_tich_vat_the = \
            self._nhap_thong_so_coc()
        self.ban_kinh_trong = self.chieu_rong_trong / 2.0
        self.do_day_vo = round((self.chieu_rong_ngoai - self.chieu_rong_trong) / 2, 2)
        
    def _nhap_thong_so_coc(self) -> Tuple[float, float, float, float]:
        print("\n" + "="*50)
        print(" "*10 + "CAU HINH THONG SO COC NUOC")
        print("="*50)
        
        try:
            chieu_cao = float(input("Nhap CHIEU CAO LONG TRONG chua nuoc (cm): "))
            rong_trong = float(input("Nhap CHIEU RONG / DUONG KINH long trong coc (cm): "))
            rong_ngoai = float(input("Nhap CHIEU RONG / DUONG KINH toan bo vo ngoai coc (cm): "))
            
            print("\n" + "-"*40)
            print("TINH NANG TRU HAO VAT THE CHIEM CHO")
            print("-"*40)
            
            co_vat_the = input("Co vat the nao ben trong coc khong? (y/n): ")
            the_tich_vat = 0.0
            
            if co_vat_the.lower() == 'y':
                loai_nhap = input("Nhap theo (1) The tich (ml) hoac (2) Khoi luong (g)? Chon 1 hoac 2: ")
                if loai_nhap == '1':
                    the_tich_vat = float(input("Nhap the tich vat the (ml): "))
                else:
                    khoi_luong = float(input("Nhap khoi luong vat the (g): "))
                    the_tich_vat = round(khoi_luong / 1.0, 1)
                print(f"-> He thong se tu dong tru di {the_tich_vat} ml vat the chiem cho.")
            
            return chieu_cao, rong_trong, rong_ngoai, the_tich_vat
            
        except ValueError:
            print("Loi nhap lieu! Tu dong dat mac dinh.")
            return 6.7, 7.3, 7.7, 0.0


# ==================== LOP PHAT HIEN MUC NUOC ====================
class WaterLevelDetector:
    """Pipeline 6 Layer phat hien muc nuoc"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.history_y = []
        self.last_alert_time = 0
        self.processing_time = 0
        
    def detect_water_level(self, roi: np.ndarray) -> int:
        """
        Pipeline 6 Layer:
        Layer 1: cv2.COLOR_BGR2GRAY
        Layer 2: cv2.GaussianBlur(5,5)
        Layer 3: Cat bien Padding 5%
        Layer 4: np.mean(axis=1) - Profile cuong do sang
        Layer 5: np.abs(np.diff()) - Toan tu sai phan
        Layer 6: Moving Average (Window=5)
        """
        start_time = time.time()
        
        if roi.size == 0 or roi.shape[0] < 5 or roi.shape[1] < 5:
            return 0
        
        try:
            # Layer 1: Gray-scale
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Layer 2: Gaussian Blur
            roi_blurred = cv2.GaussianBlur(roi_gray, self.config.GAUSSIAN_KERNEL, 0)
            
            # Layer 3: Cat bien padding
            h, w = roi_blurred.shape
            pad_x = max(1, int(w * self.config.PADDING_RATIO))
            if w > 2 * pad_x:
                roi_cropped = roi_blurred[:, pad_x:-pad_x]
            else:
                roi_cropped = roi_blurred
            
            # Layer 4: Profile cuong do sang doc
            profile_doc = np.mean(roi_cropped, axis=1)
            
            # Layer 5: Toan tu sai phan (dao ham bac 1)
            gradient = np.abs(np.diff(profile_doc))
            
            # Layer 6: Tim dinh + Moving Average
            if len(gradient) > 5:
                peak_idx = np.argmax(gradient)
                peak_value = gradient[peak_idx]
                
                if peak_value >= self.config.MIN_GRADIENT_THRESHOLD:
                    detected_y = peak_idx
                else:
                    detected_y = h - 1
            else:
                detected_y = h - 1
            
            # NANG VACH NUOC LEN CAO HON - OFFSET
            detected_y = detected_y - self.config.OFFSET_NUOC
            detected_y = max(0, min(h - 1, detected_y))  # Clamping
            
            # Moving Average filter
            self.history_y.append(detected_y)
            if len(self.history_y) > self.config.MOVING_AVG_WINDOW:
                self.history_y.pop(0)
            
            smoothed_y = int(np.mean(self.history_y))
            self.processing_time = time.time() - start_time
            
            return smoothed_y
            
        except Exception as e:
            print(f"Loi trong detect_water_level: {e}")
            return 0
    
    def tinh_toan_the_tich(self, water_pct: float) -> Tuple[float, float]:
        """Cong thuc: V = pi * R^2 * h"""
        chieu_cao_nuoc = (water_pct / 100.0) * self.config.chieu_cao_max
        v_tong = np.pi * (self.config.ban_kinh_trong ** 2) * chieu_cao_nuoc
        v_thuc = max(0.0, v_tong - self.config.the_tich_vat_the)
        return round(v_tong, 1), round(v_thuc, 1)
    
    def phan_loai_muc_nuoc(self, water_pct: float) -> Tuple[str, Tuple[int, int, int]]:
        """Phan loai: It (<=30%), Vua (31-70%), Nhieu (>70%), Tran (>=98%)"""
        if water_pct >= self.config.THRESHOLD_HIGH:
            status = "CANH BAO TRAN!!!"
            color = (0, 0, 255)
            if time.time() - self.last_alert_time > self.config.ALERT_COOLDOWN:
                print(f"\033[91m[!!! NGUY HIEM]: CANH BAO TRAN! Nuoc da day coc ({water_pct}%)!\033[0m")
                self.last_alert_time = time.time()
        elif water_pct > self.config.THRESHOLD_MEDIUM:
            status = "Muc Nuoc Nhieu"
            color = (0, 165, 255)
        elif water_pct > self.config.THRESHOLD_LOW:
            status = "Muc Nuoc Vua"
            color = (0, 255, 255)
        elif water_pct > 0:
            status = "Muc Nuoc It"
            color = (0, 255, 0)
        else:
            status = "Coc Rong"
            color = (128, 128, 128)
        return status, color
    
    def reset_history(self):
        self.history_y.clear()


# ==================== LOP CHINH ====================
class SmartWaterMeasurement:
    """He thong do muc nuoc thong minh"""
    
    def __init__(self):
        self.config = None
        self.detector = None
        self.cap = None
        self.roi_box = None
        self.y_bottom_internal = -1
        self.do_cong_nuoc = SystemConfig.DO_CONG_NUOC
        self.do_cong_day = SystemConfig.DO_CONG_DAY
        self.tu_dong_day = True
        
    def setup_system(self) -> bool:
        self.config = SystemConfig()
        self.detector = WaterLevelDetector(self.config)
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Khong the mo Webcam!")
            return False
        
        if not self._select_roi():
            return False
        
        if not self._select_bottom():
            return False
        
        return True
    
    def _select_roi(self) -> bool:
        print("\n" + "="*50)
        print("BUOC 1: QUET CHUOT CHON TOAN BO COC")
        print("="*50)
        print("-> Nhan giu chuot trai va keo de chon vung coc")
        print("-> Nhan ENTER hoac SPACE de xac nhan")
        
        window_name = "Buoc 1: Chon Coc"
        cv2.namedWindow(window_name)
        
        roi_data = {'x': -1, 'y': -1, 'w': -1, 'h': -1, 'drawing': False}
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                roi_data['x'], roi_data['y'] = x, y
                roi_data['drawing'] = True
            elif event == cv2.EVENT_MOUSEMOVE and roi_data['drawing']:
                roi_data['w'] = abs(x - roi_data['x'])
                roi_data['h'] = abs(y - roi_data['y'])
            elif event == cv2.EVENT_LBUTTONUP:
                roi_data['w'] = abs(x - roi_data['x'])
                roi_data['h'] = abs(y - roi_data['y'])
                roi_data['drawing'] = False
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            display = frame.copy()
            
            cv2.putText(display, "NHAN GIU CHUOT TRAI VA KEO TOAN BO COC", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(display, "SAU KHI KEO XONG - NHAN ENTER DE TIEP TUC", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if roi_data['w'] > 0 and roi_data['h'] > 0:
                cv2.rectangle(display, (roi_data['x'], roi_data['y']),
                            (roi_data['x'] + roi_data['w'], roi_data['y'] + roi_data['h']),
                            (255, 191, 0), 2)
            
            cv2.imshow(window_name, display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 13 or key == 32:
                break
        
        cv2.destroyWindow(window_name)
        cv2.waitKey(1)
        
        if roi_data['w'] > 0 and roi_data['h'] > 0:
            self.roi_box = (roi_data['x'], roi_data['y'], roi_data['w'], roi_data['h'])
        else:
            self.roi_box = (200, 150, 200, 260)
        
        return True
    
    def _select_bottom(self) -> bool:
        print("\n" + "="*50)
        print("BUOC 2: CLICK CHUOT CHI DINH DAY TRONG")
        print("="*50)
        print("-> Click vao day trong cua coc")
        print("-> Nhan ENTER de xac nhan")
        
        window_name = "Buoc 2: Chon Day Coc"
        cv2.namedWindow(window_name)
        
        x, y, w, h = self.roi_box
        x2, y2 = x + w, y + h
        
        click_data = {'y': -1}
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                click_data['y'] = y
                print(f"-> Da ghi nhan vach day trong tai Y: {y}")
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        frame = cv2.flip(frame, 1)
        
        while True:
            display = frame.copy()
            cv2.rectangle(display, (x, y), (x2, y2), (255, 191, 0), 2)
            
            cv2.putText(display, "CLICK VAO DAY TRONG TRONG LONG COC", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(display, "SAU DO NHAN ENTER DE XAC NHAN", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if click_data['y'] != -1:
                cv2.line(display, (x, click_data['y']), (x2, click_data['y']), (0, 0, 255), 2)
            
            cv2.imshow(window_name, display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 13:
                break
            elif key == ord('q') or key == 27:
                cv2.destroyWindow(window_name)
                return False
        
        cv2.destroyWindow(window_name)
        cv2.waitKey(1)
        
        if y < click_data['y'] < y2:
            self.y_bottom_internal = click_data['y']
        else:
            self.y_bottom_internal = int(y2 - (h * 0.15))
            print(f"-> Tu dong uoc luong day trong: Y={self.y_bottom_internal}")
        
        return True
    
    def run(self):
        if not self.setup_system():
            print("Khong the khoi tao he thong!")
            return
        
        print("\n" + "="*50)
        print("HE THONG DANG CHAY - NHAN 'q' DE THOAT")
        print("="*50)
        
        window_name = "He Thong Do Nuoc Thong Minh"
        cv2.namedWindow(window_name)
        
        x, y, w, h = self.roi_box
        x2, y2 = x + w, y + h
        
        # Bien luu ket qua
        water_pct = 0
        chieu_cao_nuoc = 0.0
        v_tong = 0.0
        v_thuc = 0.0
        status = "Chua xac dinh"
        status_color = (255, 255, 255)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Mat ket noi Camera!")
                break
            
            frame = cv2.flip(frame, 1)
            H, W = frame.shape[:2]
            
            # Clamping an toan
            x = max(0, min(W - 2, x))
            x2 = max(x + 2, min(W, x2))
            y = max(0, min(H - 2, y))
            y2 = max(y + 2, min(H, y2))
            self.y_bottom_internal = max(y + 1, min(y2, self.y_bottom_internal))
            
            # Cap nhat w, h
            w = x2 - x
            h = y2 - y
            
            # Trich xuat ROI
            roi = frame[y:self.y_bottom_internal, x:x2]
            
            if roi.size > 0 and roi.shape[0] > 5 and roi.shape[1] > 5:
                # Phat hien muc nuoc (da co offset trong detect_water_level)
                water_relative_y = self.detector.detect_water_level(roi)
                
                # Tinh toan muc nuoc
                pixel_chua_nuoc = self.y_bottom_internal - y
                if pixel_chua_nuoc > 0:
                    cm_per_pixel = self.config.chieu_cao_max / pixel_chua_nuoc
                    water_pixel_height = self.y_bottom_internal - (y + water_relative_y)
                    water_pct = int((water_pixel_height / pixel_chua_nuoc) * 100)
                    water_pct = max(0, min(100, water_pct))
                else:
                    water_pct = 0
                    cm_per_pixel = 0.03
                
                # Tinh chieu cao nuoc (cm)
                chieu_cao_nuoc = round((water_pct / 100.0) * self.config.chieu_cao_max, 1)
                
                # Tinh the tich (PDF: V = pi * R^2 * h)
                v_tong, v_thuc = self.detector.tinh_toan_the_tich(water_pct)
                
                # Phan loai muc nuoc
                status, status_color = self.detector.phan_loai_muc_nuoc(water_pct)
                
                # === VE DO HOA ===
                # Khung coc
                cv2.rectangle(frame, (x, y), (x2, y2), (255, 191, 0), 2)
                
                # Ellipse
                rx = max(1, (x2 - x) // 2)
                center_x = x + rx
                ry_nuoc = max(1, int((y2 - y) * self.do_cong_nuoc))
                ry_day = max(1, int((y2 - y) * self.do_cong_day))
                
                # Ellipse day
                cv2.ellipse(frame, (center_x, self.y_bottom_internal), 
                           (rx, ry_day), 0, 0, 180, (0, 0, 255), 2)
                
                # Ellipse mat nuoc
                water_abs_y = y + water_relative_y
                adjusted_water_y = water_abs_y + int(ry_nuoc * 2.0)
                adjusted_water_y = min(self.y_bottom_internal, adjusted_water_y)
                
                ellipse_color = (0, 0, 255) if water_pct >= 98 else (0, 255, 0)
                cv2.ellipse(frame, (center_x, adjusted_water_y),
                           (rx, ry_nuoc), 0, 0, -180, ellipse_color, 3)
                
                # HUD
                cv2.putText(frame, f"Muc nuoc: {water_pct}% (Cao: {chieu_cao_nuoc} cm)",
                           (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if self.config.the_tich_vat_the > 0:
                    cv2.putText(frame, f"Nuoc thuc te (da tru hao): {int(v_thuc)} ml",
                               (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 255, 50), 2)
                else:
                    cv2.putText(frame, f"The tich: ~ {int(v_thuc)} ml",
                               (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.putText(frame, f"Trang thai: {status}",
                           (30, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                
                # FPS
                if self.detector.processing_time > 0:
                    fps = 1.0 / self.detector.processing_time
                    cv2.putText(frame, f"Toc do: {self.detector.processing_time*1000:.1f}ms ({fps:.1f} FPS)",
                               (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Menu
                che_do = "TU DONG" if self.tu_dong_day else "THU CONG (i/k)"
                menu_text = (f"Cong Nuoc(w/s): {int(self.do_cong_nuoc*100)}% | "
                           f"Cong Day(a/d): {int(self.do_cong_day*100)}% | "
                           f"Quet Day(m): {che_do}")
                cv2.putText(frame, menu_text, (15, H - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            
            cv2.imshow(window_name, frame)
            
            # Xu ly phim
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('w'):
                self.do_cong_nuoc = min(0.15, self.do_cong_nuoc + 0.005)
            elif key == ord('s'):
                self.do_cong_nuoc = max(0.005, self.do_cong_nuoc - 0.005)
            elif key == ord('a'):
                self.do_cong_day = max(0.005, self.do_cong_day - 0.005)
            elif key == ord('d'):
                self.do_cong_day = min(0.15, self.do_cong_day + 0.005)
            elif key == ord('m'):
                self.tu_dong_day = not self.tu_dong_day
                print(f"-> Chuyen che do quet day: {'TU DONG' if self.tu_dong_day else 'THU CONG'}")
            elif key == ord('i') and not self.tu_dong_day:
                self.y_bottom_internal = max(y + 5, self.y_bottom_internal - 1)
            elif key == ord('k') and not self.tu_dong_day:
                self.y_bottom_internal = min(y2 - 1, self.y_bottom_internal + 1)
            elif key == ord('r'):
                self.detector.reset_history()
                print("-> Da reset bo loc truot!")
        
        # Xuat bao cao
        self._export_report(water_pct, chieu_cao_nuoc, v_tong, v_thuc, status)
        
        self.cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    
    def _export_report(self, water_pct, chieu_cao, v_tong, v_thuc, status):
        x, y, w, h = self.roi_box
        pixel_chua_nuoc = self.y_bottom_internal - y
        cm_per_pixel = self.config.chieu_cao_max / pixel_chua_nuoc if pixel_chua_nuoc > 0 else 0.03
        chieu_cao_ngoai = round(((y + h) - y) * cm_per_pixel, 1)
        do_day_day = round(((y + h) - self.y_bottom_internal) * cm_per_pixel, 1)
        
        print("\n" + "="*60)
        print(" "*15 + "BAO CAO CHI TIET HE THONG DO LUONG")
        print("="*60)
        print(f" 1. Chieu cao tong the vo ngoai coc:     {chieu_cao_ngoai} cm")
        print(f" 2. Chieu cao long trong chua nuoc:      {self.config.chieu_cao_max} cm")
        print(f" 3. Duong kinh vo ngoai coc:             {self.config.chieu_rong_ngoai} cm")
        print(f" 4. Duong kinh long trong coc:           {self.config.chieu_rong_trong} cm")
        print(f" 5. Do day cua thanh/vo ben coc:          {self.config.do_day_vo} cm")
        print(f" 6. Do day phan DAY dac cua coc:         {do_day_day} cm")
        print(f" 7. The tich vat the chiem cho da tru:   {self.config.the_tich_vat_the} ml")
        print("-" * 60)
        print(f" >> KET QUA PHAN TRAM MUC NUOC:          {water_pct} %")
        print(f" >> KET QUA DUNG TICH TONG (Co vat):     {int(v_tong)} ml")
        print(f" >> KET QUA DUNG TICH THUC (Khong vat):  {int(v_thuc)} ml")
        print(f" >> DANH GIA TRANG THAI MUC NUOC CUOI:   {status}")
        print("="*60 + "\n")


# ==================== MAIN ====================
def main():
    print("\n" + "="*60)
    print(" "*5 + "HE THONG DO MUC NUOC THONG MINH v2.2")
    print(" "*5 + "Smart Water Level Measurement System")
    print("="*60)
    
    while True:
        app = SmartWaterMeasurement()
        try:
            app.run()
        except Exception as e:
            print(f"Loi he thong: {e}")
            traceback.print_exc()
        
        print("\n" + "="*50)
        reset = input("Ban co muon DO COC KHAC (Reset he thong) khong? (y/n): ")
        if reset.lower() != 'y':
            print("\n>> Da thoat chuong trinh. Tam biet ban!")
            break
        
        cv2.destroyAllWindows()
        cv2.waitKey(1)


if __name__ == "__main__":
    main()