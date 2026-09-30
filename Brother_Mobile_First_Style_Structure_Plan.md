# PLAN CHI TIẾT: RESTYLE VÀ TÁI CẤU TRÚC LANDING PAGE BROTHER

Ngày phân tích: 30/09/2026. Phạm vi: lập plan cho landing page HTML/CSS/JS một trang, ưu tiên mobile first và hoàn thiện desktop.

**Hướng chốt:** phần chọn máy, thông số, so sánh và form dùng nền sáng; hero và một số điểm nhấn dùng navy/xanh theo tinh thần brochure. Giữ 5 model trong HTML, làm card ngắn hơn, đưa ảnh thật/model/giá/CTA lên sớm; chuyển thông số sâu thành phần mở rộng. Mobile so sánh 2 model theo từng hàng; desktop có bảng cả 5 model. CSS mặc định cho màn hình nhỏ, mở rộng bằng `min-width`.

Đây là tài liệu thiết kế và triển khai. Chưa sửa HTML gốc, chưa chạy nghiệm thu giao diện mới. Các giá trị màu, kích thước, breakpoint và ngân sách hiệu năng dưới đây là rule đề xuất cho bản mới, không phải thông số nhận diện chính thức đã được Brother xác nhận.

## 1. Nguồn đã đọc và cách dùng

| Nguồn | Kết quả đọc | Vai trò trong plan |
| --- | --- | --- |
| `brother_color_laser_landing_page.html` | Đọc toàn bộ 850 dòng; khoảng 51 KB; HTML, Tailwind CDN, CSS và JS cùng file | Xác định cấu trúc hiện có, lỗi dữ liệu, điểm nghẽn mobile và các luồng phải bảo toàn |
| `Brochure-series-fcl-vn.pdf` | Đọc text và render đủ 8 trang; kiểm tra riêng bảng đa chức năng trang 7 | Lấy hướng hình ảnh, nội dung lợi ích và dữ liệu nền của 5 model |
| [Trang campaign Brother](https://www.brother.com.vn/vi-vn/contents/may-in-laser-mau) | Đọc nội dung, danh sách sản phẩm và link tài nguyên | Đối chiếu thông điệp, nhóm lợi ích và cấu trúc giới thiệu dòng máy |
| Các trang sản phẩm Brother Việt Nam | Mở trang từng model tại đường dẫn `/vi-vn/printers/all-printers/…` | Kiểm tra thông số theo model và phát hiện chênh lệch giá/bảo hành với campaign |
| Brother Online User’s Guide | Đọc hướng dẫn copy hai mặt và phần in trực tiếp USB có ghi model áp dụng | Phân biệt USB kết nối máy tính với USB flash drive, duplex print với duplex scan |

**Thứ tự giải quyết dữ liệu:** xác định chính xác model/thị trường trước; thông số lấy từ trang kỹ thuật và manual ghi đúng model; brochure làm dữ liệu đối chiếu. Giá bán, VAT, tồn kho và dịch vụ của đơn vị bán phải lấy từ cấu hình bán hàng được duyệt. Khi các nguồn mâu thuẫn, ghi vào danh sách xác minh, không âm thầm chọn một con số và gọi đó là thông tin chắc chắn.

Không suy ra tính năng của một model từ tiêu đề manual dùng chung cho nhiều model. Không coi toàn bộ text trong HTML trang tham chiếu là nội dung đang hiển thị: kết quả đọc có nhiều khối tiếng Anh/model lặp cần loại khỏi nội dung sử dụng.

## 2. Audit HTML hiện tại

### 2.1. Cấu trúc đang có

1. Header sticky: logo bằng chữ, menu desktop và nút đặt mua.
2. `#danh-sach-may`: tiêu đề, sau đó 5 article dài xếp dọc.
3. `#dac-quyen-dich-vu`: banner chính sách và 3 khối cam kết.
4. `#bang-so-sanh`: bảng mô phỏng bằng div/grid, 6 cột, `min-w-[960px]`.
5. `#dat-hang`: họ tên, điện thoại, model, địa chỉ, ghi chú.
6. Footer và `#confirmModal`.
7. JS: `selectProduct()`, `handleFormSubmit()`, `closeModal()`, listener Escape.

HTML đã có viewport và nhiều class responsive. Vấn đề chính là thứ tự thông tin, mật độ nội dung và tương tác; không nên kết luận file hoàn toàn chưa responsive.

### 2.2. Vấn đề và hướng sửa cụ thể

| Mức | Bằng chứng trong file | Tác động | Hướng sửa |
| --- | --- | --- | --- |
| P0 | `handleFormSubmit()` chỉ cập nhật text và mở modal; không có fetch/Ajax/action gửi đơn | Người dùng được báo đã ghi nhận dù dữ liệu chưa tới bộ phận bán hàng | Tách chế độ demo và live; chỉ báo thành công thật sau phản hồi hệ thống |
| P0 | `closeModal()` luôn `orderForm.reset()`; listener Escape gọi hàm này bất kể modal đang mở hay đóng | Nhấn Escape lúc đang nhập form cũng có thể mất dữ liệu | Kiểm tra trạng thái dialog; đóng không reset; reset là hành động riêng |
| P0 | HL-L3280CDW được mô tả cắm USB in trực tiếp; MFC-L8340CDW có Gigabit và Dual CIS | Có khả năng quảng bá sai tính năng | Sửa theo bảng xác minh ở mục 4 |
| P1 | 61 lần `text-xs`, 32 lần `text-[11px]`, 12 lần `text-[10px]` | Thông số và thao tác khó đọc trên điện thoại | Body 16px; thông số 14–16px; chữ 12px chỉ dùng chú thích phụ |
| P1 | 5 card đều có ảnh, 4 ô thông số, mô tả dài rồi mới CTA | Muốn xem đủ 5 máy phải cuộn nhiều; CTA tới muộn | Card tóm tắt + phần thông số mở rộng, CTA nằm trước phần sâu |
| P1 | Padding card và padding vùng ảnh lồng nhau; SVG `w-52` cố định | Giảm vùng đọc thực tế tại 320–375px; nguy cơ ảnh vượt vùng khả dụng | Giảm lớp bọc, dùng ảnh `max-width:100%`, container có `min-width:0` |
| P1 | Bảng dùng grid div, rộng tối thiểu 960px | Cuộn ngang dài trên mobile và thiếu quan hệ header/cell cho trình đọc màn hình | Mobile 2 model theo từng thuộc tính; desktop table semantic |
| P1 | Input dùng `text-sm` khoảng 14px | Có thể gây zoom khi focus trên iOS | Input/select/textarea tối thiểu 16px |
| P1 | Placeholder điện thoại `0912 345 678`, pattern chỉ nhận 9–11 chữ số liền | Nhập đúng theo ví dụ vẫn bị báo sai | Chuẩn hóa khoảng trắng/dấu phân cách trước khi validate |
| P1 | Label chưa có `for`; input chưa có `name`, autocomplete; select mặc định DCP | Khó dùng bằng hỗ trợ tiếp cận, khó submit thật, người dùng chưa chọn nhưng form đã chọn hộ | Liên kết label/control, đặt name, autocomplete và option chưa chọn |
| P1 | Modal div thiếu semantics dialog, focus trap/restore và kiểm soát scroll | Keyboard và mobile khó sử dụng | Ưu tiên `<dialog>` với quản lý focus và fallback cần thiết |
| P2 | H1 và nhiều tiêu đề/nút viết hoa, tracking rộng | Tiếng Việt nặng, model và câu dài khó quét mắt | Sentence case, tracking gần mặc định, chỉ eyebrow ngắn viết hoa |
| P2 | Có 6 SVG nhưng 0 ảnh `<img>`; 5 máy được minh họa bằng hình khối đơn giản | Khó phân biệt ngoại hình và tính năng từng model | Dùng ảnh đúng model; SVG giữ cho icon chức năng |
| P2 | Logo là chữ `brother` uppercase, không phải logo asset | Nhận diện thiếu chính xác | Dùng logo chính thức, giữ tỉ lệ và khoảng trống |
| P2 | Navigation bị ẩn dưới md | Mobile thiếu lối nhảy tới so sánh/chính sách | Menu mobile gọn; section nav có nhãn rõ |
| P2 | `scrollIntoView()` chưa có scroll margin/header offset | Tiêu đề/form có thể bị header sticky che | Token chiều cao header và `scroll-margin-top` |
| P2 | Tailwind chạy từ CDN, config và handler inline | Phụ thuộc runtime ngoài, khó quản lý style/logic khi triển khai | CSS tĩnh có scope; JS event listener; có thể đóng gói lại thành một HTML |
| P2 | `h-18` ở header, chưa thấy mở rộng spacing | Class không thuộc thang mặc định thường dùng của Tailwind CDN v3 | Dùng chiều cao token rõ ràng, không dựa vào class không được kiểm chứng |
| P2 | Ghi chú được nhập nhưng `handleFormSubmit()` không đọc | Thông tin VAT/thời gian giao không có trong xử lý hiện tại | Payload và recap phải mang đủ dữ liệu đã nhập |

Các vấn đề layout nêu trên được suy ra từ code; mức tràn/chồng cụ thể phải đo trên bản render khi triển khai, không ghi là đã kiểm thử browser.

## 3. Phân tích brochure và cách chuyển thành web

### 3.1. Đọc theo từng trang PDF

| Trang PDF | Nội dung/hình ảnh | Chuyển thành module web | Điều cần tránh |
| --- | --- | --- | --- |
| 1 | Logo, nền xanh tối có texture, máy thật, cá nhiều màu, thông điệp chính và dải icon | Hero ngắn với ảnh máy; dùng hình cá/màu như điểm nhấn; 2–3 lợi ích nổi bật | Không lấy nguyên trang PDF làm ảnh hero có chữ nhỏ |
| 2 | Màu sắc, môi trường làm việc, liên hệ giữa màn hình và bản in | Khối chứng minh chất lượng màu với ảnh và đoạn giải thích ngắn | Không dùng nhiều lớp panel chồng nhau trên mobile |
| 3 | Văn phòng và máy; tốc độ, dung lượng mực 3.000/2.300 trang | Khối hiệu suất và vật tư; dẫn người dùng tới model phù hợp | Không áp 30 ppm cho cả 5 máy, không nhầm mực XL với mực đi kèm |
| 4 | In hai mặt, tiết kiệm giấy, ảnh người làm việc | Khối duplex với hình minh họa và điều kiện áp dụng | Không diễn đạt “giảm 50% mọi chi phí in” |
| 5 | Máy gọn, Quiet Mode, ảnh cá màu | Khối không gian làm việc; có thể gộp lợi ích gọn/yên tĩnh | Không hứa hoàn toàn không có tiếng ồn |
| 6 | Chia sẻ, mobile/cloud, bảo mật và Secure Print | Khối kết nối/bảo mật; note rõ theo model | Không gộp mọi tính năng nâng cao vào tất cả model |
| 7 | Bảng DCP-L3560CDW, MFC-L3760CDW, MFC-L8340CDW | Dữ liệu card đa chức năng và so sánh | Mô tả MFC-L8340 có scan hai mặt nhưng cần đối chiếu manual; bảng merged cell dễ đọc sai |
| 8 | Bảng HL-L3240CDW, HL-L3280CDW và thông tin liên hệ | Dữ liệu card đơn năng, nguồn tham khảo | Không dùng địa chỉ/liên hệ cũ trong brochure như thông tin đơn vị bán hiện tại |

### 3.2. Rule tiếp thu phong cách

- Giữ cảm giác thương hiệu kỹ thuật, đáng tin cậy: logo chuẩn, navy, xanh rõ, máy thật, ảnh tài liệu màu.
- Dùng hình cá/bản in để tạo điểm nhấn màu. Thông số và form cần nền sạch để đọc nhanh.
- Hero có thể tối; card và bảng nền trắng; chia vùng bằng nền xám nhạt và khoảng trắng.
- Tiêu đề, số liệu và chú thích phải là text HTML. Ảnh chỉ mang hình minh họa.
- Không bê bố cục brochure khổ dọc thành trang web dài; không giữ nhiều đường chéo/lớp chồng tại 320px.
- Không dùng cả trang so sánh PDF như ảnh: mất khả năng đọc, tìm kiếm và hỗ trợ tiếp cận.

### 3.3. Cải thiện so với trang campaign

Trang campaign có các nhóm lợi ích về màu sắc, hiệu suất, vật tư, kích thước, tiếng ồn, điện năng và danh sách model. Bản mới dùng các chủ đề đó làm nội dung chứng minh, nhưng đưa khu vực chọn máy lên sớm để giữ mục đích bán hàng của HTML gốc.

Giảm lặp nội dung, giới hạn 5 model đã có, không nhập các model khác từ khối mẫu. Dùng nút tải brochure rõ ràng. Không sao chép giá USD hoặc các mô tả tiếng Anh lặp trong kết quả đọc trang campaign.

## 4. Chuẩn hóa thông số, giá và nội dung trước khi style

### 4.1. Bảng dữ liệu nền cho 5 model

Các trường dưới đây nhất quán giữa phần lớn dữ liệu PDF và trang sản phẩm theo model; những tính năng dễ nhầm được tách ở bảng kế tiếp.

| Model | Chức năng | In A4 đơn sắc/màu | Hiển thị | Kết nối mạng chính | Kích thước R × S × C | ADF | In hai mặt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HL-L3240CDW | In | Tối đa 26 trang/phút | LCD 1 dòng, 16 ký tự | Wi-Fi 2.4/5 GHz, Gigabit Ethernet | 399 × 399 × 239 mm | Không có | Tự động |
| HL-L3280CDW | In | Tối đa 26 trang/phút | LCD màu cảm ứng 2.7 inch | Wi-Fi 2.4/5 GHz, Gigabit Ethernet | 399 × 399 × 274 mm | Không có | Tự động |
| DCP-L3560CDW | In / Scan / Copy | Tối đa 26 trang/phút | LCD màu cảm ứng 3.5 inch | Wi-Fi 2.4/5 GHz, Gigabit Ethernet | 410 × 444 × 401 mm | 50 tờ | Tự động |
| MFC-L3760CDW | In / Scan / Copy / Fax | Tối đa 26 trang/phút | LCD màu cảm ứng 3.5 inch | Wi-Fi 2.4/5 GHz, Gigabit Ethernet | 410 × 444 × 401 mm | 50 tờ | Tự động |
| MFC-L8340CDW | In / Scan / Copy / Fax | Tối đa 30 trang/phút | LCD màu cảm ứng 3.5 inch | Wi-Fi 2.4/5 GHz; bỏ claim LAN khỏi bản hiện tại | 410 × 462 × 401 mm | 50 tờ | Tự động |

USB 2.0 kết nối máy tính là trường riêng, không dùng làm bằng chứng cho tính năng in từ USB flash drive. Tốc độ Letter 27/31 trang/phút chỉ nằm trong thông số mở rộng; card ưu tiên A4.

### 4.2. Những claim phải sửa hoặc giữ trạng thái xác minh

| Claim hiện tại | Đối chiếu | Quyết định cho bản mới |
| --- | --- | --- |
| HL-L3280CDW “Cắm USB in trực tiếp không cần mở máy tính” | PDF trang 8 chỉ ghi USB 2.0; hướng dẫn USB direct dùng chung nhiều model nhưng mục thao tác cụ thể ghi HL-L8240CDW, không phải HL-L3280CDW | Bỏ claim in flash drive; giữ USB 2.0 kết nối máy tính. Chỉ bổ sung lại nếu có tài liệu đúng model VN |
| MFC-L8340CDW “Wi-Fi Dual Band & Gigabit”, “In qua mạng LAN” | PDF trang 7 và trang kỹ thuật hiện tại không liệt kê Ethernet cho model này; bảng so sánh trong HTML cũng chỉ ghi Wi-Fi | Bỏ Gigabit/LAN khỏi card, bảng và nội dung mở rộng |
| MFC-L8340CDW “Dual CIS”, quét hai mặt một lượt | Mô tả brochure nói scan hai mặt; manual ghi MFC-L8340 phải đặt bản gốc hai mặt trên mặt kính và lật thủ công; nhánh ADF hai mặt dành cho MFC-L3780/MFC-L8390 | Bỏ Dual CIS/scan hai mặt tự động. Tách “in hai mặt tự động” và “ADF 50 tờ” thành hai thuộc tính độc lập |
| DCP-L3560CDW “Bán chạy nhất” | Không có số liệu bán hàng trong các nguồn đã đọc | Đổi thành “In / Scan / Copy”; chỉ gắn nhãn bán chạy khi có dữ liệu được duyệt |
| MFC-L8340CDW “Flagship”, “doanh nghiệp lớn” | Là phân loại marketing trong HTML, chưa có căn cứ về toàn bộ danh mục hãng | Dùng “30 trang/phút” và “Có Fax”; tư vấn theo nhu cầu chức năng |
| “Hộp mực dung tích cực lớn” | Brochure phân biệt TN269 và TN269XL; không chứng minh đây là bộ mực đi kèm | Ghi rõ mã vật tư và dung lượng theo loại; không gắn nhãn XL cho mực tặng kèm |
| “Quiet Mode không gây tiếng ồn” | Tài liệu còn công bố mức ồn khi in | Viết “Giảm tiếng ồn khi sử dụng Quiet Mode”, không hứa im lặng tuyệt đối |
| “Tiết kiệm 50%” | Lợi ích in hai mặt liên quan lượng giấy trong trường hợp phù hợp | Dùng “Có thể giảm lượng giấy sử dụng khi in hai mặt”, hoặc giữ con số kèm điều kiện cụ thể |
| Độ phân giải “2.400 dpi” | Có trường chất lượng in, khác độ phân giải cơ bản 600 × 600 dpi | Giữ tên trường và đơn vị, không biến chất lượng mô phỏng thành độ phân giải vật lý |
| Bảo hành/hoá đơn/hỗ trợ lắp đặt cho mọi model | Bảo hành hiện theo model; VAT, lắp đặt và giao hàng là dịch vụ của bên bán | Tách policy theo model và điều kiện của đơn vị bán |

### 4.3. Giá và bảo hành đang chênh nhau

Ảnh chụp nội dung nguồn tại ngày 30/09/2026; đây là số để phát hiện lệch dữ liệu, không phải xác nhận giá bán của landing page.

| Model | HTML & bảng campaign | Trang sản phẩm hiện tại | Bảo hành trong điểm nổi bật trang sản phẩm hiện tại |
| --- | --- | --- | --- |
| HL-L3240CDW | 7.000.000đ | 8.000.000đ | 24 tháng tận nơi, HCM/Hà Nội/Đà Nẵng |
| HL-L3280CDW | 7.500.000đ | 8.700.000đ | 24 tháng tận nơi, HCM/Hà Nội/Đà Nẵng |
| DCP-L3560CDW | 11.500.000đ | 12.700.000đ | 12 tháng tận nơi, HCM/Hà Nội/Đà Nẵng |
| MFC-L3760CDW | 13.000.000đ | 14.000.000đ | 12 tháng tận nơi, HCM/Hà Nội/Đà Nẵng |
| MFC-L8340CDW | 14.000.000đ | 15.200.000đ | 12 tháng tận nơi, HCM/Hà Nội/Đà Nẵng |

Không tự thay giá do user cung cấp bằng giá hãng: có thể đây là giá đại lý hoặc chương trình riêng. Trong quá trình dựng, giá gốc là dữ liệu tạm có nguồn; trước bản live phải chốt `sellingPrice`, `priceLabel`, `vatLabel`, ngày cập nhật và nội dung bảo hành. Nếu chưa xác minh, dùng “Liên hệ báo giá” cho live thay vì công bố giá thiếu căn cứ. Không tự thêm “đã VAT”, giảm giá, quà tặng, tồn kho hay thời gian giao.

## 5. Kiến trúc trang mới

### 5.1. Thứ tự đề xuất

| Thứ tự | Module | Mục đích | Mức thay đổi |
| --- | --- | --- | --- |
| 1 | Header gọn | Nhận diện, tới chọn máy/so sánh/form | Dựng lại |
| 2 | Hero ngắn | Nêu giá trị và cho người xem thấy máy thật | Thêm từ nội dung brochure |
| 3 | Chọn theo nhu cầu | Nhảy tới nhóm in/đa năng/Fax | Thêm UI đơn giản |
| 4 | Danh sách 5 máy | Model, giá, lợi ích, CTA, mở thông số | Tái cấu trúc sâu |
| 5 | So sánh | Làm rõ khác biệt trước quyết định | Đưa lên trước chính sách; đổi mobile |
| 6 | Lợi ích công nghệ | Chứng minh màu sắc, hiệu suất, duplex, kết nối | Bổ sung có chọn lọc từ PDF |
| 7 | Dịch vụ và bảo hành | Nêu điều kiện theo model/bên bán | Tái biên tập và restyle |
| 8 | Tài liệu | Tải brochure/đọc trang model | Thêm link nguồn rõ ràng |
| 9 | FAQ ngắn | Giải thích LED, Fax, duplex, USB, bảo hành | Thêm tối đa 5 câu từ các điểm dễ nhầm |
| 10 | Form | Chọn máy và gửi thông tin | Giữ luồng, sửa UI và trạng thái |
| 11 | Footer | Thông tin đơn vị vận hành, liên hệ/chính sách | Xác minh danh tính trước khi dùng |

Giữ mục đích bán hàng: hero không chiếm cả viewport và đẩy sản phẩm quá xa. Không thêm carousel tự chạy, video nền, blog, tài khoản hay checkout nhiều bước.

### 5.2. Anchor và mức bảo toàn

- Giữ `danh-sach-may`, `bang-so-sanh`, `dac-quyen-dich-vu`, `dat-hang` để link hiện có vẫn chạy.
- Thêm `tong-quan`, `loi-ich`, `tai-lieu`, `cau-hoi` khi cần.
- Đặt anchor phụ theo model, ví dụ `model-hl-l3240cdw`, ID duy nhất.
- Mọi CTA chọn model dùng model ID chính xác; cấm match bằng `option.text.includes()`.
- Thứ tự DOM theo mobile; desktop chỉ thay grid/alignment, không đổi thứ tự đọc vô lý bằng CSS.
- Hero và model vẫn đọc được khi JS tắt. JS nâng cấp phần chọn model/so sánh, không quyết định việc tồn tại của nội dung chính.

## 6. Bộ rule style thống nhất

### 6.1. Palette đề xuất

| Token | Giá trị | Ứng dụng |
| --- | --- | --- |
| `--blp-primary` | `#0050B3` | CTA chính và link nổi bật |
| `--blp-primary-hover` | `#003E8C` | Hover/active CTA |
| `--blp-navy` | `#081827` | Hero, một dải nội dung thương hiệu |
| `--blp-cyan` | `#35C8ED` | Điểm nhấn trên navy; không dùng chữ nhỏ trên trắng |
| `--blp-bg` | `#FFFFFF` | Nền chính |
| `--blp-soft` | `#F4F7FB` | Section xen kẽ/vùng ảnh |
| `--blp-text` | `#152536` | Nội dung chính |
| `--blp-muted` | `#4F6072` | Nội dung phụ |
| `--blp-border` | `#D8E1EB` | Viền card/table |
| `--blp-control-border` | `#718096` | Viền control trên trắng; kiểm contrast khi render |
| `--blp-success` | `#176B3A` | Trạng thái thành công |
| `--blp-error` | `#B42318` | Lỗi nhập liệu/gửi form |

Tỉ lệ thị giác dự kiến: khoảng 70–80% diện tích đọc nền sáng, phần còn lại là navy/hình ảnh. Không đổi màu theo từng card. Không phủ gradient lên bảng/form. Xác minh độ tương phản từng cặp thực tế; viền trang trí không thay thế viền control đủ tương phản.

### 6.2. Typography

Giữ Plus Jakarta Sans để hạn chế thay đổi không cần thiết, nhưng giảm số weight về 400/600/700 và dùng fallback `system-ui, sans-serif`. Nếu triển khai font local, kiểm đủ dấu tiếng Việt; font tải lỗi vẫn phải đọc tốt.

| Thành phần | Mobile | Desktop | Rule |
| --- | --- | --- | --- |
| Body | 16px / 1.6 | 16px / 1.6 | Nội dung chính không nhỏ hơn 16px |
| H1 | 30–34px / 1.15 | 44–52px / 1.12 | Tối đa khoảng 3 dòng mobile; không ép line-break toàn thiết bị |
| H2 section | 24–28px / 1.25 | 32–36px / 1.2 | Sentence case, khoảng cách nhất quán |
| Model | 20–22px / 1.3 | 22–24px / 1.25 | Không tách model giữa chừng ở độ rộng thông thường |
| Giá | 24–28px / 1.2 | 28–30px / 1.2 | Có đơn vị; không truncate |
| Thông số | 14–16px / 1.5 | 14–16px / 1.5 | Nội dung quyết định mua cần dễ đọc |
| Label form | 14–16px / 1.4 | 14–16px / 1.4 | Label luôn hiện, không chỉ placeholder |
| Input/select | 16px / 1.5 | 16px / 1.5 | Tránh zoom input iOS |
| CTA | 16px / 1.25 | 15–16px / 1.25 | Weight 600/700; không letter-spacing rộng |
| Eyebrow/chú thích | 12–14px / 1.5 | 12–14px / 1.5 | Không chứa duy nhất giá/điều kiện quan trọng ở 12px |

Dùng `clamp()` cho heading; đoạn dài giới hạn khoảng 60–70 ký tự/dòng. Không dùng tất cả chữ in hoa cho H1/H2. Không dùng màu xám quá nhạt để “làm sang”.

### 6.3. Spacing, bo góc và chiều rộng

- Scale spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 80px.
- Gutter: 16px tại 320–767px; 24px tại 768–1023px; 32px từ 1024px.
- Container tối đa 1200px, căn giữa; không kéo card toàn chiều rộng màn 1920px.
- Section padding dọc 36–40px mobile, 48–56px tablet, 64–72px desktop.
- Card padding 16px mobile, 20–24px desktop; vùng ảnh padding 8–12px.
- Radius card 12–16px; button/input 8px; pill chỉ cho chip/badge ngắn.
- Shadow rất nhẹ cho card; không shadow xanh đậm liên tục.
- Khoảng cách title–description 8–12px; description–content 20–24px; các card 16–24px.
- Hover card: thay border/shadow nhẹ; nếu dịch chuyển tối đa 2px và chỉ tại thiết bị hỗ trợ hover. Không hover là cách duy nhất để lộ CTA.
- Focus-visible: outline rõ 2–3px, offset 3px; không chỉ thay màu.
- Transition 150–200ms; bỏ chuyển động/scroll smooth khi `prefers-reduced-motion: reduce`.

## 7. Rule responsive và từng module

### 7.1. Breakpoint có mục đích

| Viewport | Header/hero | Sản phẩm | So sánh | Form |
| --- | --- | --- | --- | --- |
| 320–479px | Header 60–64px; hero 1 cột | 1 card/cột; không cuộn ngang toàn trang | 2 model, label chung phía trên 2 giá trị | 1 cột; control full width |
| 480–767px | Hero vẫn 1 cột; media rộng hơn | 1 cột để đủ vùng đọc | 2 model như mobile | 1 cột |
| 768–1023px | Header 72px; hero có thể 2 cột | 2 cột; gap 20–24px | Giữ chế độ 2 model; có link mở cả 5 | Form rộng hơn; nhóm tên/điện thoại có thể 2 cột |
| 1024–1279px | Menu desktop; hero 2 cột | 3 cột, 5 card thành 3 + 2 | Table 5 model; scroll bên trong khi không đủ | Summary + form 2 cột |
| ≥1280px | Container tối đa 1200px | 3 cột; hàng cuối giữ cùng width | Table 5 model đủ rộng trong container | Summary khoảng 35%, form 65% |

Không ép 2 card ở 375px hoặc 4–5 card ở desktop. Tại 768px nếu ảnh/text chưa đủ, giữ 1 cột tới breakpoint phù hợp; phải kiểm chiều rộng nội dung thay vì chỉ tên thiết bị.

### 7.2. Header

- Logo asset chính thức có kích thước khai báo; mobile rộng khoảng 96–110px.
- Mobile: logo trái; nút “Chọn máy” gọn; nút menu có accessible name và `aria-expanded`.
- Menu mở 3–4 anchor: Máy in / So sánh / Dịch vụ / Liên hệ. Tap item đóng menu, cuộn đúng offset.
- Header sticky duy nhất phía trên; không thêm một thanh sticky nhu cầu bên dưới.
- Desktop: logo, anchor nav và CTA; tagline không tracking quá rộng.
- Nếu nhúng vào theme đã có header sticky, tắt header riêng hoặc chuyển non-sticky; tránh hai header.
- Tổng chiều rộng logo + gap + CTA + menu tại 320px phải nằm trong viewport trừ 32px gutter.

### 7.3. Hero ngắn

- Eyebrow: “Máy in màu Brother”.
- H1 đề xuất: “Bản in màu sắc nét cho công việc mỗi ngày”. Đây là copy đề xuất, không trích nguyên văn brochure.
- Mô tả tối đa 2–3 dòng: nêu lựa chọn đơn năng/đa năng, kết nối và in hai mặt theo từng model.
- CTA chính: “Chọn máy phù hợp”; CTA phụ dạng link: “So sánh 5 model”.
- Dải lợi ích tối đa 3 mục ngắn, ví dụ “In hai mặt tự động”, “Kết nối không dây”, “Tối đa 30 trang/phút*”. Footnote chỉ model áp dụng phải gần claim.
- Mobile: text rồi CTA rồi ảnh; ảnh cao khoảng 180–240px tùy viewport. Không dùng `height:100vh`; không để hero kéo quá dài trên máy nhỏ.
- Desktop: khoảng 52% text / 48% ảnh, chiều cao nội dung khoảng 420–480px; không đặt chữ đè lên ảnh phức tạp.
- Ảnh máy không bị crop; texture/cá có thể là lớp trang trí. Không dùng ảnh model khác và gắn tên 5 model như ảnh đại diện đúng của tất cả.

### 7.4. Chọn theo nhu cầu

- 3 lựa chọn: “Chỉ cần in”, “In / Scan / Copy”, “Cần thêm Fax”.
- Bản mặc định dùng anchor tới model đầu phù hợp; tất cả 5 card vẫn hiện để người xem không mất lựa chọn.
- Nếu nâng cấp thành lọc, phải có “Tất cả”, đếm kết quả, reset và trạng thái focus rõ; lọc không làm mất model đã chọn trong form.
- Nhóm chỉ cần in: HL-L3240, HL-L3280. Nhóm ba chức năng: DCP-L3560. Nhóm có Fax: MFC-L3760, MFC-L8340.
- Mobile cho chip wrap 2 dòng; không yêu cầu vuốt ngang mới thấy lựa chọn cuối.
- Không phân loại theo “3–5 người” hoặc “doanh nghiệp lớn” khi chưa có dữ liệu khối lượng in khuyến nghị.

### 7.5. Card sản phẩm

Thứ tự DOM và hiển thị mặc định:

1. Badge chức năng có dữ liệu xác minh.
2. Ảnh đúng model, vùng ảnh nền trắng/xám nhạt.
3. H3 model và một dòng mô tả nhu cầu.
4. Giá + nhãn VAT/giá tham khảo khi có căn cứ.
5. Tối đa 3 bullet nổi bật: A4 ppm, màn hình/ADF, kết nối hoặc Fax.
6. CTA chính “Chọn máy này”.
7. Link/nút “Thông số chi tiết” và link thêm so sánh nếu triển khai.
8. Phần `<details>` chứa thông số sâu.

Rule mobile:

- Ảnh khoảng 150–180px chiều cao; `object-fit:contain`, không dựng thumbnail vuông quá lớn.
- Body card 16px padding; không thêm một panel viền trong cho từng thông số tóm tắt.
- Bullet label/value đọc được, không dùng đoạn phụ 10px dưới mọi bullet.
- CTA full width, cao tối thiểu 48px; bấm được bằng ngón tay.
- Chiều cao card đóng kỳ vọng khoảng 460–560px tùy nội dung, không khóa height cứng; ở 320px hoặc text lớn có thể cao hơn.
- Giá và tên model không bị line-clamp. Mô tả nên viết ngắn thay vì cắt phần thông tin cần mua.

Rule desktop:

- 3 card/cột ở vùng rộng; ảnh cao khoảng 180–200px; card cùng cấu trúc.
- Grid card stretch theo hàng; CTA có thể `margin-top:auto` để thẳng hàng khi đóng.
- Hai card cuối cùng giữ width bằng card hàng đầu; không phóng to gấp rưỡi.
- Details mở phải đẩy nội dung tự nhiên; không overlay hoặc crop thông số. Có thể chấp nhận hàng cao hơn khi mở.

Phần thông số sâu dùng `<dl>`: chức năng, A4/Letter, duplex print, ADF, display, Wi-Fi/LAN/USB PC, khay giấy, kích thước, vật tư, bảo hành đã xác minh. Thuộc tính không áp dụng ghi “Không có” hoặc “Không áp dụng”; chưa xác minh ghi rõ, không biến thành “Có”.

### 7.6. So sánh

**Mobile/tablet:** mặc định so sánh 2 máy, ví dụ HL-L3240CDW và DCP-L3560CDW để thấy khác biệt đơn/đa năng. Đây là cặp minh họa so sánh, không chọn hộ máy mua.

- Hai select có label “Máy 1”, “Máy 2”, font 16px. Model trùng không được xem là so sánh hợp lệ.
- Mỗi thuộc tính có nhãn chung trên một hàng, bên dưới là hai ô giá trị bằng width và cùng hàng.
- Mỗi ô có tên model qua label/accessibility; chiều rộng giá trị dùng `minmax(0,1fr)`, cho wrap.
- 8–10 thuộc tính quyết định mua trước: giá, chức năng, A4 ppm, in hai mặt, ADF, màn hình, mạng, kích thước, bảo hành.
- Nhóm vật tư/thông số sâu có disclosure riêng để tránh quá dài.
- Giá trị khác nhau có nền xanh nhạt kèm text rõ; màu không phải dấu hiệu duy nhất.
- Mỗi model có CTA “Chọn [model]” dùng chung logic chọn sản phẩm.
- Link “Xem bảng đủ 5 model” mở vùng table cuộn ngang như lựa chọn bổ sung; không bắt người dùng mobile dùng bảng 6 cột ngay từ đầu.

**Desktop:** `<table>` với caption, thead, tbody, th `scope=col/row`; đủ 5 model.

- Cột nhãn khoảng 180–190px; cột model khoảng 180–190px. Table khoảng 1100–1140px khi đủ 5 máy.
- Tại container nhỏ hơn, scroll ngang chỉ ở wrapper có hướng dẫn “Cuộn ngang để xem thêm”.
- Không cho width table làm body tràn; wrapper cần `max-width:100%`, card/container có `min-width:0`.
- Có thể sticky cột nhãn trong wrapper; tránh sticky toàn bảng với chiều cao cố định gây thêm một vùng cuộn dọc.
- Header model và CTA không xuống dòng quá nhiều; giá không cắt.
- Khác biệt mạng của MFC-L8340 phải nhất quán với card/form recap.

Nguồn dữ liệu so sánh và card là một object/catalog duy nhất. Nếu có hai markup responsive, IDs phải khác nhau; bản ẩn dùng `display:none` để không tạo tab stop và đọc lặp. Không dùng hai cấu trúc có dữ liệu gõ tay độc lập.

### 7.7. Khối lợi ích từ brochure

Chọn 4 chủ đề chính để giữ trang gọn: màu sắc; tốc độ/vật tư; in hai mặt/giấy; kết nối/bảo mật. “Nhỏ gọn & yên tĩnh” là dải ngắn hoặc bullet trong chủ đề liên quan.

- Mobile: ảnh rồi heading rồi nội dung, cùng một thứ tự trong mọi module; text tối đa 2–4 dòng trước disclosure.
- Desktop: 2 cột ảnh/text, có thể thay vị trí bằng grid khi thứ tự đọc vẫn hợp lý; không quá nhiều lớp trang trí.
- Icon 24–32px, một bộ thống nhất; SVG không thay ảnh sản phẩm.
- Chú thích model áp dụng nằm ngay dưới số liệu, không giấu cuối trang.
- Mực XL có thể nêu 3.000 trang đen/2.300 trang mỗi màu theo loại và điều kiện ISO/IEC 19798 trong PDF; không gắn cho bộ mực đi kèm.
- Không tạo công cụ tính chi phí/trang nếu thiếu giá vật tư, độ phủ và dữ liệu vận hành.

### 7.8. Dịch vụ, tài liệu và FAQ

- Dịch vụ dùng 3 khối: bảo hành theo model, hỗ trợ cài đặt theo phạm vi bên bán, hoá đơn theo điều kiện đã duyệt.
- Bỏ đoạn “tất cả đi kèm gói dịch vụ toàn diện” nếu không có chính sách chứng minh.
- Link bảo hành Brother có nhãn rõ; thông tin hotline bên bán và hotline hãng không trộn.
- FAQ tối đa 5 câu: laser/LED là gì; in hai mặt khác scan hai mặt; chọn đơn/đa năng/Fax; USB PC khác flash drive; bảo hành và giá cần xác nhận thế nào.
- FAQ dùng `<details><summary>`; đáp án dựa nguồn, không chứa hứa hẹn thời gian phản hồi/giao hàng chưa duyệt.
- Tài liệu có tên brochure, số trang, dung lượng thực tế và nút tải. Không iframe PDF tự mở.
- PDF gốc 303.605.961 bytes, khoảng 303,6 MB (289,5 MiB): rất lớn cho mobile. Lập bước xuất bản web tối ưu từ bản gốc, mục tiêu 5–15 MB nếu vẫn giữ chữ/ảnh đọc tốt. Dung lượng này là mục tiêu, phải đo lại sau tối ưu.
- Không ghi “PDF 5 MB” trước khi có file thật; không sửa/xoá bản PDF nguồn khi tạo bản web.

### 7.9. Form chọn máy và gửi thông tin

Giữ các trường đã có: model, tên, điện thoại, địa chỉ, ghi chú. Đưa model và recap lên đầu để người xem biết mình đang hỏi mua máy nào.

- Mobile: 1 cột; recap ảnh nhỏ + model + giá; không để panel recap chiếm cả màn hình.
- Desktop: recap trái và form phải; có thể sticky recap trong section nếu không gây chồng header.
- Model mặc định “Chọn model máy in”; chưa chọn thì không hiển thị giá của DCP như đã quyết định.
- Tất cả control có `id`, `name`, `label for`, autocomplete phù hợp; tel dùng `inputmode=tel`.
- Normalize điện thoại: trim, loại khoảng trắng/dấu `-`/`.` được cho phép, xử lý `+84` theo quy tắc được chốt. Không chấp nhận chuỗi bất kỳ chỉ vì đủ độ dài.
- Trường text phải reject chuỗi toàn khoảng trắng; email chỉ bổ sung nếu scope thu thập thực sự cần.
- Địa chỉ vẫn giữ theo yêu cầu đặt mua hiện có; nếu đổi sang form tư vấn lead thì label và trạng thái gửi phải đổi nhất quán. Không tự bỏ trường.
- VAT/ghi chú được mang vào payload; không thêm quy trình xuất hóa đơn mới nếu chưa cần.
- Lỗi đặt dưới trường, có `aria-describedby`, focus vào lỗi đầu; dữ liệu không mất khi sửa lỗi.
- Model đổi từ card/table/select cập nhật cùng recap; giá luôn từ catalog được duyệt.

Hai chế độ rõ ràng trong implementation:

| Chế độ | Nút gửi | Kết quả | Reset |
| --- | --- | --- | --- |
| Demo giao diện | “Xem thông tin yêu cầu” | Hiển thị bản tóm tắt và trạng thái demo; không nói bộ phận bán hàng đã nhận | Không tự reset khi đóng |
| Live đã tích hợp | “Gửi yêu cầu đặt mua” | Loading → phản hồi thành công/error từ endpoint thật | Chỉ reset theo hành động rõ hoặc sau success và giữ recap cần thiết |

Không đặt “Xác nhận đặt hàng” như đơn thương mại đã tạo nếu chỉ gửi lead. Điểm nối backend là hạng mục riêng cần endpoint/chính sách dữ liệu; frontend vẫn có thể triển khai đầy đủ cấu trúc và trạng thái demo trước.

### 7.10. Dialog và CTA mobile dưới màn hình

- Dialog dùng `<dialog>` khi môi trường hỗ trợ; có title, nút đóng, focus đầu, Escape và khôi phục focus về nút mở.
- Chỉ xử lý Escape khi dialog/menu thực sự mở. Đóng dialog không xoá form.
- Có `max-height` theo `dvh`, nội dung cuộn được, nút đóng luôn tiếp cận được; dự phòng `vh` cho môi trường cần.
- Nếu chặn body scroll, giữ/restoration vị trí scroll; thử trên Safari/in-app.
- Sticky bottom chỉ xuất hiện sau khi người dùng chọn model và form chưa trong viewport: model + giá/nhãn + “Tiếp tục”.
- Chưa chọn máy thì không hiện bottom CTA gán sẵn DCP.
- Ẩn bottom CTA khi dialog mở, focus vào input hoặc form đã hiển thị; cân nhắc `visualViewport` khi có để tránh bàn phím.
- Safe area: `env(safe-area-inset-bottom)`; body có padding bù đúng chiều cao bar khi nó hiện.
- Không dựng đồng thời bottom mua + bottom so sánh + floating chat trên một vùng. Desktop không dùng bar này.
- Có thể bỏ sticky bottom nếu QA cho thấy chiếm quá nhiều chiều cao; CTA trong card vẫn là hành động chính đầy đủ.

## 8. Tổ chức HTML/CSS/JS khi triển khai

### 8.1. Cấu trúc code đề xuất

- Bản phát triển: `index.html`, `assets/brother-landing.css`, `assets/brother-landing.js`, `assets/images/`, dữ liệu catalog trong một nơi.
- Nếu yêu cầu giao một index độc lập, đóng gói CSS/JS vào HTML sau QA; asset ảnh/PDF vẫn phải có đường dẫn hợp lệ và được giao kèm hoặc host đúng.
- Không dùng base64 ảnh lớn/PDF trong index; không phát sinh project framework nặng cho trang này.
- Root `.brother-landing`, prefix `blp-`; không style toàn cục `header`, `button`, `input`, `table` nếu nhúng theme.
- Scope token trên root để tránh đè biến theme. Box sizing/reset có scope và kiểm ảnh hưởng.
- HTML chính có sẵn 5 model; dùng build-time catalog hoặc renderer tĩnh để card/table/form không lệch. Không chờ fetch mới có toàn bộ nội dung.

### 8.2. CSS mobile first tối thiểu

```css
.brother-landing {
  --blp-primary: #0050b3;
  --blp-header-height: 64px;
  color: #152536;
  background: #fff;
  font-size: 16px;
  line-height: 1.6;
}
.brother-landing,
.brother-landing *,
.brother-landing *::before,
.brother-landing *::after { box-sizing: border-box; }
.blp-container {
  width: min(100%, 1200px);
  margin-inline: auto;
  padding-inline: 16px;
}
.blp-products { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; }
.blp-products > * { min-width: 0; }
.blp-anchor { scroll-margin-top: calc(var(--blp-header-height) + 16px); }
.blp-control { width: 100%; min-height: 48px; font-size: 16px; }
.blp-product-image { display: block; max-width: 100%; object-fit: contain; }
@media (min-width: 768px) {
  .brother-landing { --blp-header-height: 72px; }
  .blp-container { padding-inline: 24px; }
  .blp-products { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
}
@media (min-width: 1024px) {
  .blp-container { padding-inline: 32px; }
  .blp-products { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) {
  .brother-landing * { scroll-behavior: auto; transition: none; }
}
```

Đây là skeleton rule, chưa phải CSS hoàn chỉnh. Khi container 1200px có padding thì content width thực nhỏ hơn 1200px; table phải tính theo content width và cho overflow nội bộ khi cần. Không chữa lỗi bằng `body{overflow-x:hidden}` để giấu phần bị tràn.

### 8.3. Catalog và JS

Catalog mỗi model cần: `id`, `name`, `functions`, `price`, `priceStatus`, `priceSource`, `vatLabel`, `a4Ppm`, `display`, `wifiBands`, `ethernet`, `usbPc`, `usbDirectStatus`, `duplexPrint`, `duplexScanStatus`, `adfSheets`, `dimensions`, `image`, `alt`, `productUrl`, `warranty`, `verifiedAt`.

Không dùng boolean `false` cho dữ liệu chưa biết: `verified/unsupported/pending` hoặc null phù hợp. Không suy ra scan hai mặt từ `duplexPrint`.

JS chia trách nhiệm:

1. `selectModel(id)`: xác minh ID tồn tại → cập nhật select/state/recap → cuộn tới form; không đổi model bằng text gần giống.
2. `updateOrderSummary()`: dùng catalog; render text bằng `textContent`.
3. `updateCompare(a,b)`: kiểm model khác nhau → cập nhật cùng hàng thuộc tính → thông báo thay đổi ngắn, không đọc toàn bảng bằng aria-live.
4. `validateOrder()`: normalize rồi validate; không lưu PII ở localStorage hoặc đưa lên URL.
5. `submitOrder()`: theo chế độ demo/live; lỗi/timeout giữ dữ liệu, ngăn gửi lặp lúc loading.
6. `openConfirmation()`/`closeConfirmation()`: focus và scroll; close không reset.
7. `initNavigation()`/`initMobileBar()`: active section và visibility; ưu tiên IntersectionObserver hơn listener scroll liên tục.

Handler dùng `addEventListener`, event delegation qua `data-model-id`, không 11 onclick inline lặp. Button chọn máy/menu/details có `type=button`; chỉ nút submit gửi form.

## 9. Asset, hiệu năng và metadata

### 9.1. Asset inventory bắt buộc

| Asset | Số lượng | Yêu cầu |
| --- | --- | --- |
| Logo Brother | 1 bộ nền sáng/tối | SVG/PNG chính thức, không dựng chữ giả |
| Ảnh 5 model | Tối thiểu 5 | Đúng tên model, nền trong hoặc trắng, góc nhất quán |
| Hero campaign | 1 | Crop phù hợp mobile/desktop, chữ nằm ngoài ảnh |
| Hình lợi ích | Khoảng 3–4 | Màu bản in, văn phòng, duplex, kết nối; không lặp một ảnh ở mọi khối |
| Icon | 1 bộ | Cùng stroke/kích thước; icon trang trí aria-hidden |
| Brochure web | 1 bản tối ưu | Giữ nguồn, link và dung lượng thật; kiểm đọc rõ |

Ưu tiên asset nguồn của hãng/được bên triển khai cung cấp. Nếu trích ảnh từ PDF, kiểm chất lượng và model trước khi dùng. Không tạo hình máy bằng AI vì cần đúng cấu tạo thực tế. Không hotlink mù ảnh có query crop không hiểu; chuẩn bị file được phép sử dụng và đường dẫn ổn định.

### 9.2. Ngân sách đề xuất

- Hero mobile khoảng 120–220 KB; desktop khoảng 200–350 KB nếu chất lượng đạt.
- Ảnh card khoảng 40–100 KB/model ở kích thước sử dụng; thumbnail responsive 320/640px khi phù hợp.
- CSS khoảng dưới 40 KB gzip; JS tương tác khoảng dưới 25 KB gzip; đây là mục tiêu theo scope trang tĩnh.
- Font chỉ weight cần, `font-display:swap`; hạn chế preload thừa.
- Khai báo width/height hoặc aspect-ratio cho ảnh; hero/LCP không lazy-load; ảnh dưới fold lazy-load.
- Chỉ ưu tiên một ảnh LCP; không tải hai bản mobile/desktop hero rồi ẩn một bản bằng CSS.
- Không nhúng PDF trong initial load; không kéo thư viện slider/modal lớn cho tương tác có thể làm native.
- Theo dõi LCP ≤2,5s, CLS ≤0,1, INP ≤200ms khi có điều kiện đo phù hợp. Đây là mục tiêu nghiệm thu, không phải kết quả đã đạt.
- Lighthouse lab dùng để chẩn đoán; field INP/CWV cần dữ liệu thật. Không hứa điểm PSI 100 hoặc kết quả field từ một lượt đo local.

### 9.3. SEO và semantics

- 1 H1; H2 theo section; H3 model/FAQ phù hợp; không dùng heading chỉ để làm chữ to.
- Title và description mô tả dòng máy/chọn model, tránh “bảng giá chính hãng” nếu chưa chốt giá/đơn vị bán.
- Canonical/OG dùng URL live sau khi biết URL; không đặt canonical giả vào bản demo.
- Alt ảnh đúng model; hình texture trang trí alt rỗng.
- FAQ vẫn có text HTML. Chỉ thêm structured data nếu nội dung thực và scope cần; không thêm fake review/aggregateRating/Offer.
- Nếu xuất Product/Offer sau này, giá/tồn kho/đơn vị bán phải đồng bộ catalog đã xác minh.
- Không đưa họ tên/số điện thoại/địa chỉ vào analytics, querystring hoặc event label.

## 10. Plan triển khai 10 phase

### Phase 1 — Khóa phạm vi và dữ liệu nguồn

**Đầu vào:** HTML, PDF, campaign, trang model, manual.

**Việc làm:**

1. Lưu bản gốc và checksum, không chỉnh trực tiếp bản nguồn khi chưa có working copy.
2. Lập inventory 4 anchor cũ, 5 model, field form, handler, nguồn ảnh/PDF.
3. Chuẩn hóa catalog theo mục 4, đánh dấu giá/VAT/bảo hành cần chốt.
4. Loại claim USB flash của HL-L3280, LAN/Dual CIS của MFC-L8340, bán chạy/flagship chưa chứng minh.
5. Xác định demo form hay endpoint thật; bản mặc định hiện chưa có tích hợp.
6. Xác định trang đứng riêng hay nhúng theme; giữ một bộ content và scope đúng.

**Đầu ra:** catalog kiểm chứng, danh sách pending, mapping cũ–mới. **Gate:** không còn thông số mâu thuẫn trong card/table/form; phần chưa duyệt có trạng thái rõ.

### Phase 2 — Wireframe mobile trước

1. Vẽ wireframe 375px cho thứ tự module mục 5, đối chiếu lại tại 320px.
2. Thiết kế riêng card đóng/mở, so sánh 2 model, form có/không chọn model, menu và dialog.
3. Chốt vùng hero ngắn; sản phẩm xuất hiện sớm, CTA không nằm sau toàn bộ bảng spec.
4. Chốt một header sticky và cơ chế bottom CTA có điều kiện.
5. Xác định nội dung nào luôn hiện, nội dung nào trong details; mọi thông số quyết định vẫn truy cập được.
6. Lập wireframe desktop tương ứng 1200px content: hero 2 cột, card 3 cột, table 5 model, form 2 cột.

**Đầu ra:** wireframe và thứ tự DOM. **Gate:** mobile không cần zoom để đọc/không cần cuộn ngang trang; desktop có bố cục tận dụng không gian.

### Phase 3 — Chốt token và component

1. Áp palette, font, spacing, radius, button, input, badge, accordion, table.
2. Thiết kế states default/hover/focus/disabled/loading/error/success.
3. Đo contrast cho text, CTA, control border và focus ring.
4. Kiểm tiếng Việt có dấu, model dài, giá 8 chữ số, chú thích 2–3 dòng.
5. Chốt hero/card/table/form sử dụng cùng token, không thêm màu tùy module.

**Đầu ra:** style rules và component sheet. **Gate:** không còn body 10–12px, input ≥16px, touch target ≥44px.

### Phase 4 — Chuẩn bị ảnh và brochure web

1. Thu thập ảnh thật đúng 5 model và logo chuẩn.
2. Crop/cân vùng ảnh đồng đều, vẫn giữ toàn bộ máy.
3. Tạo srcset phù hợp; kiểm nền alpha viền trắng trên surface.
4. Chuẩn bị hero mobile/desktop qua `<picture>` nếu cần crop khác.
5. Tối ưu bản PDF web riêng; đo bytes thực và kiểm text/hình của đủ 8 trang.
6. Ghi tên, kích thước, alt, source của mỗi asset vào manifest nội bộ.

**Đầu ra:** asset sẵn dùng. **Gate:** không ảnh model sai, không ảnh/PDF nặng tải sớm, không chữ bắt buộc nằm trong raster.

### Phase 5 — Dựng HTML semantic

1. Dựng root scope và landmarks header/nav/main/footer.
2. Hero, nhu cầu, sản phẩm, so sánh, lợi ích, dịch vụ, tài liệu, FAQ, form.
3. Giữ 4 anchor cũ, thêm ID model duy nhất.
4. Card dùng article/heading/figure/list/dl/details đúng vai trò.
5. Table desktop dùng scope/caption; mobile dùng từng nhóm thuộc tính có nhãn cho hai giá trị.
6. Form có label/name/autocomplete; dialog có title và nút đóng.
7. Kiểm khi JS tắt vẫn có 5 sản phẩm, nội dung và link tài liệu.

**Đầu ra:** skeleton đầy đủ. **Gate:** không duplicate ID; heading/label/table đọc được bằng công cụ hỗ trợ.

### Phase 6 — CSS mobile first và desktop

1. Viết base CSS cho 320px và 375px, không bắt đầu bằng desktop rồi scale xuống.
2. Chốt typography, gutter, card, comparison, form một cột.
3. Mở rộng tại 768 và 1024px; kiểm boundary trước/sau breakpoint.
4. Hero 2 cột, card 2/3 cột, desktop table, form recap.
5. Thử nội dung dài, text 200%, landscape; bỏ mọi height cứng gây cắt chữ.
6. Thiết lập scroll offset, safe area, reduced motion, hover theo pointer.

**Đầu ra:** style đầy đủ responsive. **Gate:** page không tràn ngang; chỉ wrapper table bổ sung được phép cuộn ngang.

### Phase 7 — Tương tác JS và trạng thái

1. Chuyển chọn model sang ID/state dùng chung.
2. Cập nhật recap, chọn hai model so sánh, chống model trùng.
3. Menu mobile, anchor, details; không phụ thuộc hover.
4. Sửa normalize/validate form và đọc đủ note/address/model.
5. Sửa Escape/reset; dialog focus/close/backdrop theo rule thống nhất.
6. Demo summary trung thực; live gửi thật chỉ khi đã có endpoint, xử lý loading/error/timeout/retry.
7. Sticky bottom theo chọn model và visibility form, không chồng keyboard/modal.

**Đầu ra:** tất cả luồng hoạt động. **Gate:** không mất dữ liệu do Escape/đóng; không báo đã nhận khi chưa gửi.

### Phase 8 — Metadata và tối ưu

1. Loại Tailwind runtime CDN nếu chuyển sang CSS tĩnh; xoá class/config không dùng.
2. Kiểm ảnh eager/lazy, width/height, srcset/sizes, font fallback.
3. Kiểm UTF-8, title/description, alt và semantic content.
4. Chốt URL nguồn/sản phẩm/PDF; không href rỗng hoặc canonical demo giả.
5. Đo initial transfer và performance trong môi trường triển khai; sửa vấn đề có bằng chứng.
6. Kiểm CSS scope nếu nhúng theme, kiểm CSP nếu môi trường có chính sách.

**Đầu ra:** bản nhẹ và metadata hợp lệ. **Gate:** không PDF tải tự động, không asset hỏng, không class cũ ảnh hưởng style.

### Phase 9 — QA 20 nhóm và sửa lỗi

1. Chạy ma trận mục 11, ghi PASS/FAIL/BLOCKED kèm bằng chứng.
2. Sửa P0/P1 trước, sau đó P2.
3. Retest nhóm liên quan khi sửa; không chạy lại 20 vòng giống nhau chỉ để đủ số.
4. Chụp trạng thái quan trọng ở mobile/tablet/desktop khi đã có bản implementation.
5. Đối chiếu dữ liệu lần cuối giữa 5 card, compare, form và source.

**Đầu ra:** QA report thật. **Gate:** 0 P0/P1 còn mở; dữ liệu chưa xác minh không quảng bá như đã xác nhận.

### Phase 10 — Bàn giao và nghiệm thu

1. Đóng gói index/CSS/JS/ảnh/PDF web theo hình thức đã chốt.
2. Ghi rule chỉnh dữ liệu giá/bảo hành và vị trí catalog.
3. Ghi rõ mode form và trạng thái backend; có hướng dẫn cấu hình endpoint nếu thuộc scope.
4. Cung cấp ảnh kiểm chứng và QA report, danh sách giới hạn còn lại.
5. Nếu đưa vào Haravan/theme khác, thực hiện integration pass riêng cho scope/header/form và asset path.

**Đầu ra:** mã nguồn dùng được + tài liệu thay đổi + QA. **Gate:** không nhầm bản demo là bản nhận đơn live, không mất asset khi bàn giao.

## 11. Ma trận QA 20 nhóm

Đây là checklist cần chạy khi có bản mới. Chưa có nhóm nào được đánh dấu PASS cho giao diện mới trong lần lập plan này.

| Nhóm | Kiểm tra | Tiêu chí đạt | Bằng chứng cần giữ |
| --- | --- | --- | --- |
| 01 | Catalog và model | Đủ 5 model đúng ID; function/ppm/display/dimensions nhất quán | Bảng đối chiếu nguồn–catalog |
| 02 | Claim kỹ thuật | Không USB flash chưa xác minh, LAN/Dual CIS sai; print/scan duplex tách riêng | Tìm kiếm code + manual liên quan |
| 03 | Giá/VAT/bảo hành | Card/table/form cùng giá; nhãn nguồn/điều kiện đúng; không blanket 24 tháng | Chốt dữ liệu và ảnh 5 model |
| 04 | UTF-8 và HTML | Không lỗi dấu, U+FFFD/mojibake, ID trùng, tag sai | Validator/kiểm nội dung |
| 05 | 320px | Header, model, giá, CTA không tràn; card/controls đủ rộng | Ảnh viewport và đo scrollWidth |
| 06 | 360/375/390/430px | Gutter/spacing nhất quán; thông số đọc được; input không zoom bất thường | Ảnh và kiểm trên thiết bị phù hợp |
| 07 | Tablet 768/820/1024px | Không card quá hẹp; 2 cột hợp lý; compare/form không cắt | Ảnh portrait/landscape |
| 08 | Desktop 1280/1440/1920px | Container đúng, hero/card/table/form cân; hàng 3+2 không giãn sai | Ảnh desktop |
| 09 | Boundary responsive | Kiểm 767/768, 1023/1024 và container hẹp; không nhảy/chồng | Kiểm resize, ảnh lỗi nếu có |
| 10 | Header/nav/anchor | Menu mở/đóng/focus đúng; tiêu đề không bị sticky che | Luồng keyboard/touch |
| 11 | Card/details/ảnh | Ảnh đúng model, không crop máy, mở thông số không che CTA khác | Ảnh đóng/mở của card |
| 12 | So sánh | Đổi A/B đúng dữ liệu, không model trùng, khác biệt rõ, table semantic | Các cặp đơn/đa năng/Fax/8340 |
| 13 | Chọn model xuyên trang | Mọi nút chọn card/table/bottom cập nhật select và recap đúng | Kiểm cả 5 model từ mỗi vị trí |
| 14 | Form nhập liệu | Tên rỗng/space, phone format, address, note; lỗi rõ, data còn nguyên | Ca valid/invalid đã ghi |
| 15 | Demo/live submit | Demo không báo nhận thật; live success chỉ sau response; lỗi giữ dữ liệu | Network/response trong môi trường test |
| 16 | Dialog/Escape/reset | Escape ở form không reset; dialog close/restore focus đúng; không tab thoát | Keyboard + kiểm DOM/state |
| 17 | Safari/in-app/safe area | Input ≥16px, keyboard không che hành động, scroll/modal không kẹt | Test trên iPhone Safari và in-app nếu có |
| 18 | Accessibility | Contrast text/control/focus đạt mục tiêu; zoom 200%, target ≥44px, table/label đọc được | Kiểm công cụ + keyboard/manual |
| 19 | Performance/asset lỗi | Không layout shift do ảnh/font; ảnh responsive; PDF không tải trước; fallback hợp lý | Lighthouse/network/asset inventory |
| 20 | Regression/tích hợp | Scope CSS, anchors, footer, all model, form, no-JS; không console error do code mới | Smoke checklist + log issue |

### 11.1. Các ca kiểm bắt buộc, tránh bỏ sót

- Chưa chọn model → form vẫn ở trạng thái chưa chọn, không tự mua DCP.
- Bấm HL-L3280 từ card → form/recap đúng HL-L3280, không nhầm với HL-L3240.
- Bấm chọn MFC-L8340 ở bảng → không hiện Gigabit/scan hai mặt tự động trong recap.
- Đổi model trong form → summary và bottom CTA đồng bộ; thông tin tên/phone không mất.
- Nhập tên/phone rồi nhấn Escape khi dialog đóng → dữ liệu còn nguyên.
- Mở summary rồi đóng → tên/phone/address/note còn nguyên.
- Nhập điện thoại có khoảng trắng như placeholder → normalize trước khi validate.
- Chọn hai model trùng trong compare → có xử lý rõ, không tạo cặp giả.
- Mở details tại card rồi đổi breakpoint → không bị cắt nội dung hoặc duplicate ID/focus.
- Network chậm/lỗi submit → nút có trạng thái, retry rõ, không báo thành công.
- Ảnh tải lỗi/font không về → tên model, giá và CTA vẫn đọc/dùng được.
- PDF lớn → chỉ bắt đầu tải khi click, dung lượng được báo đúng.

## 12. Điều kiện nghiệm thu và thứ tự ưu tiên

### P0 — Bắt buộc trước khi coi là dùng được

- Sửa claim kỹ thuật mâu thuẫn và chốt nguồn giá/bảo hành.
- Sửa Escape làm reset form; đóng modal không mất dữ liệu.
- Không hiển thị nhận đơn thật khi form chưa có backend.
- Mỗi CTA chọn đúng model và recap đồng bộ.

### P1 — Bắt buộc cho mobile first

- Typography dễ đọc, input 16px, target đủ lớn, header/menu không tràn 320px.
- Card gọn, CTA trước thông số sâu, ảnh thật đúng model.
- Comparison 2 model đọc theo từng hàng; không bắt cuộn bảng rộng mặc định.
- Không có cuộn ngang toàn trang, overlay che nội dung hoặc sticky bar che bàn phím.
- Desktop hero/card/table/form có bố cục riêng đúng độ rộng.

### P2 — Hoàn thiện chất lượng

- Màu/token/font/spacing thống nhất, ảnh lợi ích và brochure web tối ưu.
- Metadata và asset inventory hoàn chỉnh.
- QA có bằng chứng ở các viewport và trạng thái chính.

**Definition of Done:** đủ module đã chốt; đủ 5 model; thông số không mâu thuẫn; dữ liệu bán hàng có nguồn; 0 lỗi P0/P1; mobile và desktop được kiểm thực tế; UTF-8 đúng; form mode trung thực; file bàn giao có đầy đủ asset và hướng dẫn cập nhật.

Không dùng “100% không lỗi” hoặc “QA đủ 20 vòng” thay bằng chứng. Các mục bị chặn bởi thiếu dữ liệu/endpoint/thiết bị phải ghi BLOCKED và ảnh hưởng cụ thể.

## 13. Trạng thái của lần phân tích này

| Công việc | Trạng thái |
| --- | --- |
| Đọc toàn bộ HTML và JS | Đã thực hiện |
| Trích text PDF, render đủ 8 trang, xem tổng thể và bảng trang 7 | Đã thực hiện |
| Đọc campaign và trang model Brother | Đã thực hiện |
| Kiểm manual cho duplex/USB model áp dụng | Đã thực hiện |
| Lập rule style, cấu trúc, 10 phase và QA20 | Đã thực hiện |
| Sửa HTML/CSS/JS gốc | Chưa thực hiện; đầu ra hiện tại là plan |
| Render/browser QA giao diện mới | Chưa thực hiện; chưa có bản mới |
| Chốt giá đại lý, VAT, bảo hành bán hàng và endpoint | Cần dữ liệu của đơn vị triển khai trước bản live |

## 14. Danh mục nguồn để triển khai đối chiếu

Đã truy cập tại thời điểm phân tích 30/09/2026; cần kiểm lại giá/policy khi triển khai live.

1. HTML đính kèm: `brother_color_laser_landing_page.html`.
2. PDF đính kèm: `Brochure-series-fcl-vn.pdf`, 8 trang; metadata tạo tháng 12/2023.
3. Campaign: https://www.brother.com.vn/vi-vn/contents/may-in-laser-mau
4. HL-L3240CDW: https://www.brother.com.vn/vi-vn/printers/all-printers/hl-l3240cdw
5. HL-L3280CDW: https://www.brother.com.vn/vi-vn/printers/all-printers/hl-l3280cdw
6. DCP-L3560CDW: https://www.brother.com.vn/vi-vn/printers/all-printers/dcp-l3560cdw
7. MFC-L3760CDW: https://www.brother.com.vn/vi-vn/printers/all-printers/mfc-l3760cdw
8. MFC-L8340CDW: https://www.brother.com.vn/vi-vn/printers/all-printers/mfc-l8340cdw
9. Manual hai mặt, ghi riêng các model phải lật bản gốc thủ công: https://support.brother.com/g/s/id/htmldoc/mfc/cv_dcpl3520cdw/asoce/html/GUID-D22B31B3-1169-4414-B9BB-02E108DD4DB0_1.html
10. Manual USB direct, phải đọc `Related Models` thay vì tiêu đề nhóm model: https://support.brother.com/g/s/id/htmldoc/printer/cv_hll3220cw/sfgle/html/GUID-A48243F6-422F-42CE-9254-20C31996D131_1.html

Các kết luận về hiện trạng HTML/PDF lấy từ file đính kèm; các giá trị current trong mục 4.3 lấy từ trang sản phẩm ở mục 4–8; quyết định sửa scan/USB dựa thêm mục 9–10. Các rule thiết kế còn lại là đề xuất triển khai của tài liệu này.
