# DS108

# DỰ ĐOÁN GIÁ ĐIỆN THOẠI CŨ BẰNG MÔ HÌNH MÁY HỌC

## Mục lục

- [Giới thiệu](#giới-thiệu)
- [Thành viên](#thành-viên)
- [Cấu trúc](#cấu-trúc)
- [Các giai đoạn thực hiện](#các-giai-đoạn-thực-hiện)
  - [1. Thu thập dữ liệu](#1-thu-thập-dữ-liệu)
  - [2. Điền thiếu](#2-điền-thiếu)
  - [3. Tiền xử lí dữ liệu](#3-tiền-xử-lí-dữ-liệu)
  - [4. Chọn thuộc tính](#4-chọn-thuộc-tính)
  - [5. Mã hóa thuộc tính](#5-mã-hóa-thuộc-tính)
  - [6. Mô hình](#6-mô-hình)
  - [7. Triển khai](#7-triển-khai)

## Giới thiệu

Dự án xây dựng mô hình dự đoán giá điện thoại cũ dựa trên dữ liệu thực tế từ Thế Giới Di Động và CellphoneS. Dữ liệu bao gồm các đặc điểm kỹ thuật, tình trạng thiết bị và giá bán tại thời điểm giao dịch.

Bài toán đặt ra là xây dựng một hệ thống dự đoán giá điện thoại cũ dựa trên bộ dữ liệu đã thu thập được.

- Input: Dữ liệu về các thuộc tính của điện thoại cũ.
- Output: Mức giá dự đoán.

Mục tiêu là phát triển một hệ thống thông minh có khả năng phân tích và đưa ra mức giá dự đoán chính xác, hỗ trợ người dùng trong việc định giá, mua bán và trao đổi thiết bị cũ.

## Thành viên

- Trần Nhật Phương Anh - 23520078
- Văn Thị Bảo Hân - 23520439
- Nguyễn Thảo Nga - 23520993

## Cấu trúc
```
DS108/
├── crawling/                  # Scripts và dữ liệu thô từ quá trình thu thập
│   ├── tgdd/                  # Thu thập từ Thế Giới Di Động
│   └── cellphones/            # Thu thập từ CellphoneS
├── preprocessing/             # Xử lý dữ liệu trước khi huấn luyện
│   ├── fill_missing_values/   # Xử lý dữ liệu thiếu
│   ├── preprocessing/         # Làm sạch và chuẩn hóa dữ liệu
│   ├── tidy_data/             # Dữ liệu đã chuẩn hóa
│   └── updated_data/          # Dữ liệu sau điền thiếu
├── modeling/                  # Mã hóa đặc trưng, huấn luyện mô hình
│   ├── modeling/              # Notebook huấn luyện mô hình
│   ├── data/                  # Dữ liệu sau chọn và mã hóa
│   └── model/                 # Mô hình đã huấn luyện
├── web/                       # Giao diện người dùng
│   ├── templates/             # Giao diện HTML
│   └── app/                   # Mã nguồn backend
└── README.md                  # Tài liệu mô tả dự án
```
## Các giai đoạn thực hiện

### 1. Thu thập dữ liệu

Dữ liệu được thu thập từ danh mục điện thoại cũ của Thế Giới Di Động (TGDĐ) và CellphoneS – hai chuỗi bán lẻ uy tín tại Việt Nam. Chúng tôi sử dụng Selenium để tự động hóa quá trình thu thập, đảm bảo tính đầy đủ và chính xác.

- Tổng số mẫu: 13.760 (TGDĐ: 12.535, CellphoneS: 1.225)
- Số thuộc tính: 23 (bao gồm: tên, hãng, RAM, CPU, giá, tình trạng, hệ điều hành, v.v.)
- Ngày thu thập: 18/05/2025

Dữ liệu từ hai nguồn được chuẩn hóa và kết hợp theo một khuôn mẫu thống nhất để đảm bảo tính đồng nhất và tận dụng dữ liệu đầy đủ nhất cho mô hình dự đoán giá.

### 2. Điền thiếu

Đối với các thông số kỹ thuật bị thiếu, chúng tôi xử lý theo từng dòng máy (name). Các thuộc tính được chia thành:

- Thuộc tính cố định theo dòng máy: CPU, battery, screen_size, operating_system, GPU, v.v.
- Thuộc tính không cố định: RAM, capacity (có thể thay đổi theo phiên bản).

Để đảm bảo việc điền thiếu chính xác, tên dòng máy được chuẩn hóa bằng cách:

- Chuyển về chữ thường, loại bỏ khoảng trắng và ký tự thừa.
- Chỉ giữ lại tên hãng và tên thiết bị.
- Xử lý đặc biệt với các từ khóa như “5G”, “Plus” để tránh nhầm lẫn giữa tính năng và tên dòng máy.

Sau khi chuẩn hóa, các thuộc tính cố định được điền dựa trên thông tin đầy đủ từ các mẫu cùng dòng máy.

### 3. Tiền xử lí dữ liệu

Dữ liệu được xử lý để loại bỏ thông tin dư thừa, chuẩn hóa định dạng và chuyển đổi kiểu dữ liệu phù hợp:

- Trích xuất nội dung chính: giữ lại thông tin cốt lõi cho các thuộc tính như CPU, GPU, màn hình, hệ điều hành, tình trạng, màu sắc, hình ảnh...
- Chuẩn hóa tên dòng máy: xử lý thống nhất tên thiết bị để hỗ trợ điền thiếu chính xác.
- Chuyển đổi kiểu dữ liệu: chuẩn hóa đơn vị và kiểu dữ liệu cho các cột như giá, RAM, pin, kích thước, độ phân giải...
- Tách thuộc tính mới: từ các cột như size, SIM, warranty, time tạo ra các thuộc tính mới có ý nghĩa hơn cho mô hình.

### 4. Chọn thuộc tính

- Categorical: Tính entropy để đo mức độ đa dạng và Cramér's V + Kruskal-Wallis để đánh giá mối liên hệ với price_old. Loại bỏ các thuộc tính không có ý nghĩa thống kê hoặc liên hệ yếu như image, color.
- Numerical: Phân tích đa cộng tuyến bằng ma trận tương quan Pearson và chỉ số VIF. Loại bỏ các thuộc tính có VIF cao như battery, screen_size, has_nano_sim.
- Loại bỏ thêm: day_remaining_warranty bị loại do phân bố nhiễu, không có mối liên hệ rõ ràng với giá.

### 5. Mã hóa thuộc tính

Mã hóa categorical: Các thuộc tính phân loại được mã hóa bằng cách gán nhãn số theo mức độ phổ biến, hiệu năng hoặc tính cập nhật:

- name: dùng LabelEncoder.
- brand, condition: phân loại theo thị phần và độ mới.
- CPU, GPU: phân nhóm hiệu năng.
- display_technology, operating_system, bluetooth: phân loại theo công nghệ và phiên bản.

Phân khúc dữ liệu: Áp dụng K-Means để chia thành 3 nhóm điện thoại dựa trên đặc điểm kỹ thuật, hỗ trợ mô hình học được mối quan hệ tổng thể.

Chia tập dữ liệu: Dữ liệu hoàn chỉnh được chia thành train.csv, dev.csv, test.csv theo tỉ lệ 6:2:2.

![Các thuộc tính của bộ dữ liệu](https://github.com/user-attachments/assets/36fd2266-553b-4d5b-9c52-921fd2666e5d)


### 6. Mô hình

Sử dụng GridSearchCV và RandomizedCV để tối ưu cho các mô hình sau:

- XGBoost
- LightGBM
- Random Forest
- CatBoost

### 7. Triển khai

Xây dựng ứng dụng web sử dụng mô hình CatBoost để dự đoán giá điện thoại cũ:

- Input: Người dùng chọn tên thiết bị và tình trạng máy
- Xử lý: Các thuộc tính còn lại được tự động lấy từ tidy_data.csv
- Output: Hiển thị mức giá dự đoán trên giao diện web
