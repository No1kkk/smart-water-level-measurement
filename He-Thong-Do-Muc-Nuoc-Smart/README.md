# HỆ THỐNG ĐO MỰC NƯỚC & THỂ TÍCH THỜI GIAN THỰC
Smart Water Level & Volume Measurement System

## GIỚI THIỆU
Hệ thống sử dụng Webcam + Thị giác máy tính (OpenCV) để:
- Đo chiều cao mực nước (cm)
- Tính phần trăm mực nước (%)
- Tính thể tích chất lỏng thực tế (ml)
- Cảnh báo khi nước sắp tràn (≥ 98%)

Tất cả hoạt động thời gian thực, không cần GPU, chạy mượt trên laptop thông thường.

## TÍNH NĂNG CHÍNH
- Phát hiện mặt nước tự động: Dùng thuật toán sai phân Profile độ sáng, không cần cảm biến vật lý.
- Hiển thị 3D trực quan: Vạch nước và đáy cốc dạng Ellipse, đồng bộ góc nghiêng camera.
- Trừ hao vật thể: Tự động trừ thể tích vật thể chiếm chỗ trong cốc.
- Chống lỗi an toàn: Tự động kẹp biên, không lo văng code khi thao tác sai.
- Nhẹ & Nhanh: Chạy realtime (< 0.05s/frame), chỉ cần CPU.

## CÀI ĐẶT
### Yêu cầu:
- Python 3.7+
- Webcam (tích hợp hoặc USB)

### Cài thư viện:
```bash
pip install opencv-python numpy
```

## HƯỚNG DẪN SỬ DỤNG
1. Chạy chương trình: `python main.py`
2. Nhập thông số cốc (nhập theo yêu cầu trong Terminal):
   - Chiều cao lòng trong (cm): Đo từ đáy trong đến miệng cốc (Ví dụ: 10.0)
   - Đường kính lòng trong (cm): Đo ngang bên trong cốc (Ví dụ: 7.0)
   - Đường kính vỏ ngoài (cm): Đo ngang mép ngoài cùng (Ví dụ: 7.6)
   - Có vật thể trong cốc? (y/n): Nếu có đá, ống hút, thìa... chọn `y` và nhập thể tích (ml) hoặc khối lượng (g). Nếu không có, chọn `n`.
3. Bước 1: Chọn vùng cốc (ROI):
   - Nhấn giữ chuột trái kéo khung bao toàn bộ cốc (từ miệng đến đáy ngoài).
   - Nhấn `ENTER` để xác nhận.
4. Bước 2: Chọn đáy trong:
   - Click chuột trái vào đáy trong của cốc (nơi nước chạm đáy).
   - Nhấn `ENTER` để xác nhận (xuất hiện vạch đỏ ngang).
5. Hệ thống bắt đầu đo: Cửa sổ hiện ra hiển thị khung vàng (vùng chọn), vạch đỏ (đáy cốc), vạch xanh (mặt nước), các thông số đo và FPS ở góc trái.

## ĐIỀU KHIỂN BẰNG BÀN PHÍM
- `w` / `s`: Tăng / Giảm độ cong vạch nước xanh (Mẹo: Nếu vạch xanh thấp hơn mặt nước thật -> Bấm `w` vài lần để nâng lên).
- `a` / `d`: Giảm / Tăng độ cong vạch đáy đỏ.
- `m`: Bật/tắt chế độ chỉnh tay vạch đáy.
- `i` / `k`: Nâng / Hạ vạch đáy lên xuống (chỉ khi tắt tự động bằng phím `m`).
- `r`: Reset bộ lọc làm mượt.
- `q`: Thoát và xuất báo cáo.

## KẾT QUẢ & BÁO CÁO (Khi bấm 'q')
```text
==================== BÁO CÁO CHI TIẾT ====================
 1. Chiều cao tổng vỏ ngoài:      10.5 cm
 2. Chiều cao lòng trong:         10.0 cm
 3. Đường kính vỏ ngoài:          7.6 cm
 4. Đường kính lòng trong:        7.0 cm
 5. Độ dày thành cốc:             0.3 cm
 6. Độ dày đáy cốc:               0.5 cm
 7. Thể tích vật thể đã trừ:      15.0 ml
----------------------------------------------------------
 >> KẾT QUẢ MỰC NƯỚC:             65 %
 >> DUNG TÍCH TỔNG:               250 ml
 >> DUNG TÍCH THỰC:               235 ml
 >> TRẠNG THÁI:                   Mực Nước Vừa
==========================================================
```

## NGUYÊN LÝ HOẠT ĐỘNG
1. Chuyển ảnh xám: Giảm dữ liệu, tăng tốc.
2. Gaussian Blur: Xóa nhiễu hạt.
3. Cắt biên 5%: Loại bỏ lòa sáng thành ly.
4. Profile dọc: Đo cường độ sáng từng hàng.
5. Sai phân: Tìm bước nhảy sáng -> Phát hiện mặt nước.
6. Trung bình trượt: Làm mượt, chống rung.

## KẾT QUẢ THỰC NGHIỆM & YÊU CẦU
- Độ chính xác: > 99% | Sai số thể tích: ± 2 ml.
- Thời gian xử lý: < 0.05 giây/frame (20 - 30 FPS).
- Cấu hình tối thiểu**: CPU Core i3, RAM 4GB, Webcam 720p.

## GHI CHÚ
- Ánh sáng: Đặt cốc trước nền tối, tránh ánh sáng chiếu trực tiếp vào thành ly.
- Khoảng cách: Khuyến nghị từ 10-15 cm từ camera đến cốc.
- Nước trong: Thêm vài giọt màu thực phẩm nếu nước quá trong để hệ thống dễ nhận biết.

## TÁC GIẢ
Phạm Thiên Vũ