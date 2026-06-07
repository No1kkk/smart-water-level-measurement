# Hệ thống Đo lường Mực nước và Thể tích Chất lỏng Thời gian thực

Đề án xây dựng hệ thống giám sát biến thiên mực nước (cm), tỷ lệ phần trăm (%) và dung tích thực tế (ml) chất lỏng trong cốc thủy tinh thời gian thực (Real-time) ứng dụng kỹ thuật thị giác máy tính truyền thống.

## Tính năng cốt lõi
* **Thuật toán Profile độ sáng dọc (Light Intensity Profile):** Tự động bám bắt biên mặt nước dựa trên giải thuật sai phân (đạo hàm bậc 1) nhạy bén, triệt tiêu tạp nhiễu lóa sáng từ thành ly thủy tinh dày.
* **Giao diện 3D hình học không gian:** Mô phỏng các vạch đo dạng hình elip cánh cung động đồng bộ theo góc nghiêng thấu kính camera.
* **Bộ trừ hao vật thể:** Tự động trừ đi không gian chiếm chỗ của dị vật bên trong lòng cốc để tính toán dung tích thực chính xác.
* **Cơ chế khóa biên an toàn:** Ngăn chặn hoàn toàn hiện tượng tràn bộ nhớ hoặc văng sập mã nguồn khi người dùng tương tác điều chỉnh hệ thống.
* **Tính thích ứng tối ưu:** Hệ thống dựa trên các đặc trưng hình học vật lý trực tiếp, chạy mượt mà trên các máy tính cấu hình phổ thông mà không cần phần cứng mạnh (GPU) để huấn luyện mô hình.

## Cài đặt môi trường & Thư viện
Hệ thống được phát triển trên ngôn ngữ **Python 3**. Để cài đặt các thư viện bổ trợ cần thiết, hãy chạy lệnh sau trong cửa sổ dòng lệnh (Terminal):

```bash
pip install opencv-python numpy
```

## Hướng dẫn Vận hành và Thao tác Demo
1. Di chuyển vào thư mục chứa mã nguồn và khởi chạy chương trình:
   ```bash
   python src/main.py
   ```
2. Nhập các thông số kích thước vật lý của chiếc cốc và khối lượng vật thể chiếm chỗ theo hướng dẫn hiển thị trên Terminal.
3. **Bước 1 (Chọn cốc):** Nhấn giữ chuột trái và kéo khung chữ nhật bao bọc toàn bộ chiếc cốc trên màn hình camera, nhấn `Enter` để xác nhận vùng xử lý (ROI).
4. **Bước 2 (Chọn đáy):** Click chuột trái vào ranh giới đáy trong của lòng cốc, nhấn một phím bất kỳ để kích hoạt luồng đo lường trực tiếp.

### ĐIỀU KHIỂN HỆ THỐNG TRỰC TIẾP QUA BÀN PHÍM:
* `w` / `s`: Tăng / Giảm độ cong Elip của vạch mực nước (Màu xanh lá).
* `d` / `a`: Tăng / Giảm độ cong Elip của vạch đáy cốc (Màu đỏ).
* `m`: Bật / Tắt chế độ hiệu chỉnh vị trí vạch đáy bằng tay (`THỦ CÔNG`).
* `i` / `k`: Dịch chuyển vạch đáy đỏ lên trên hoặc xuống dưới (Khi ở chế độ thủ công).
* `q`: Thoát luồng camera và xuất bảng báo cáo chi tiết tổng hợp dữ liệu ra Terminal.

## Kết quả Thực nghiệm
Hệ thống đạt độ ổn định cao, phản hồi biến thiên mực nước tức thời khi đổ thêm hoặc rút bớt chất lỏng. Sai số tính toán dung tích thực tế đạt mức cực thấp (< 1%), dao động trong khoảng $\pm 2$ ml so với công thức toán học trụ tròn lý thuyết.
