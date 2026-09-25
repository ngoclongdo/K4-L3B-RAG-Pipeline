"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path
from fpdf import FPDF


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

FONT_CANDIDATES = [
    "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
    "/home/tuananh/.local/share/fonts/FiraSans/FiraSans-Regular.ttf",
]


def get_available_font() -> str | None:
    for font_path in FONT_CANDIDATES:
        if Path(font_path).is_file():
            return font_path
    return None


NGHI_DINH_01_CONTENT = """CHÍNH PHỦ
Số: 01/2021/NĐ-CP

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Hà Nội, ngày 04 tháng 01 năm 2021

NGHỊ ĐỊNH VỀ ĐĂNG KÝ DOANH NGHIỆP

CHƯƠNG VIII: ĐĂNG KÝ HỘ KINH DOANH

Điều 79. Hộ kinh doanh
1. Hộ kinh doanh do một cá nhân hoặc các thành viên hộ gia đình đăng ký thành lập và chịu trách nhiệm bằng toàn bộ tài sản của mình đối với hoạt động kinh doanh của hộ. Trường hợp các thành viên hộ gia đình đăng ký hộ kinh doanh thì ủy quyền cho một thành viên làm đại diện hộ kinh doanh. Cá nhân đăng ký hộ kinh doanh, người được các thành viên hộ gia đình ủy quyền làm đại diện hộ kinh doanh là chủ hộ kinh doanh.
2. Hộ gia đình sản xuất nông, lâm, ngư nghiệp, làm muối và những người bán hàng rong, quà vặt, buôn chuyến, kinh doanh lưu động, kinh doanh thời vụ, làm dịch vụ có thu nhập thấp không phải đăng ký hộ kinh doanh, trừ trường hợp kinh doanh các ngành, nghề đầu tư kinh doanh có điều kiện. Ủy ban nhân dân tỉnh, thành phố trực thuộc Trung ương quy định mức thu nhập thấp áp dụng trên phạm vi địa phương.

Điều 80. Quyền thành lập hộ kinh doanh và nghĩa vụ đăng ký hộ kinh doanh
1. Cá nhân, thành viên hộ gia đình là công dân Việt Nam có năng lực hành vi dân sự đầy đủ theo quy định của Bộ luật Dân sự có quyền thành lập hộ kinh doanh, trừ các trường hợp sau đây:
a) Người chưa thành niên, người bị hạn chế năng lực hành vi dân sự; người bị mất năng lực hành vi dân sự; người có khó khăn trong nhận thức, làm chủ hành vi;
b) Người đang bị truy cứu trách nhiệm hình sự, bị tạm giam, đang chấp hành hình phạt tù, đang chấp hành biện pháp xử lý hành chính tại cơ sở cai nghiện bắt buộc, cơ sở giáo dục bắt buộc hoặc đang bị Tòa án cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định;
c) Các trường hợp khác theo quy định của pháp luật có liên quan.
2. Cá nhân, thành viên hộ gia đình quy định tại khoản 1 Điều này chỉ được đăng ký một hộ kinh doanh trong phạm vi toàn quốc và được quyền góp vốn, mua cổ phần, mua phần vốn góp trong doanh nghiệp với tư cách cá nhân.
3. Cá nhân, thành viên hộ gia đình đăng ký hộ kinh doanh không được đồng thời là chủ doanh nghiệp tư nhân, thành viên hợp danh của công ty hợp danh trừ trường hợp được sự nhất trí của các thành viên hợp danh còn lại.

Điều 81. Đặt tên hộ kinh doanh
1. Hộ kinh doanh có tên gọi riêng. Tên hộ kinh doanh bao gồm hai thành tố theo thứ tự sau đây:
a) Cụm từ "Hộ kinh doanh";
b) Tên riêng của hộ kinh doanh.
Tên riêng được viết bằng các chữ cái trong bảng chữ cái tiếng Việt, các chữ F, J, Z, W, có thể kèm theo chữ số, ký hiệu.
2. Không được sử dụng từ ngữ, ký hiệu vi phạm truyền thống lịch sử, văn hóa, đạo đức và thuần phong mỹ tục của dân tộc để đặt tên riêng cho hộ kinh doanh.
3. Hộ kinh doanh không được sử dụng các cụm từ "công ty", "doanh nghiệp" để đặt tên hộ kinh doanh.
4. Tên riêng hộ kinh doanh không được trùng với tên riêng của hộ kinh doanh đã đăng ký trong phạm vi cấp huyện.

Điều 82. Giấy chứng nhận đăng ký hộ kinh doanh
1. Giấy chứng nhận đăng ký hộ kinh doanh được cấp cho hộ kinh doanh thành lập và hoạt động theo quy định tại Nghị định này. Hộ kinh doanh được cấp Giấy chứng nhận đăng ký hộ kinh doanh khi có đủ các điều kiện sau đây:
a) Ngành, nghề đăng ký kinh doanh không bị cấm đầu tư kinh doanh;
b) Tên của hộ kinh doanh được đặt theo đúng quy định tại Điều 81 Nghị định này;
c) Có hồ sơ đăng ký hộ kinh doanh hợp lệ;
d) Nộp đủ lệ phí đăng ký hộ kinh doanh theo quy định.
2. Giấy chứng nhận đăng ký hộ kinh doanh được cấp trên cơ sở thông tin trong hồ sơ đăng ký hộ kinh doanh do người thành lập hộ kinh doanh tự kê khai và tự chịu trách nhiệm.

Điều 83. Mã số đăng ký hộ kinh doanh
1. Cơ quan đăng ký kinh doanh cấp huyện ghi mã số đăng ký hộ kinh doanh trên Giấy chứng nhận đăng ký hộ kinh doanh theo cấu trúc: mã định danh địa phương kết hợp mã số tăng dần.
2. Mã số đăng ký hộ kinh doanh đồng thời là mã số thuế của hộ kinh doanh được tạo bởi Hệ thống ứng dụng đăng ký thuế và được truyền sang Hệ thống thông tin về đăng ký hộ kinh doanh.

Điều 85. Trình tự, thủ tục đăng ký hộ kinh doanh
1. Khi đăng ký hộ kinh doanh, người thành lập hộ kinh doanh hoặc hộ kinh doanh nộp hồ sơ tại Cơ quan đăng ký kinh doanh cấp huyện nơi đặt trụ sở hộ kinh doanh. Hồ sơ bao gồm:
a) Giấy đề nghị đăng ký hộ kinh doanh;
b) Giấy tờ pháp lý của cá nhân đối với chủ hộ kinh doanh, thành viên hộ gia đình đăng ký hộ kinh doanh trong trường hợp các thành viên hộ gia đình đăng ký hộ kinh doanh;
c) Bản sao biên bản họp thành viên hộ gia đình về việc thành lập hộ kinh doanh trong trường hợp các thành viên hộ gia đình đăng ký hộ kinh doanh;
d) Bản sao văn bản ủy quyền của các thành viên hộ gia đình cho một thành viên làm chủ hộ kinh doanh trong trường hợp các thành viên hộ gia đình đăng ký hộ kinh doanh.
2. Khi tiếp nhận hồ sơ, Cơ quan đăng ký kinh doanh cấp huyện trao Giấy biên nhận và cấp Giấy chứng nhận đăng ký hộ kinh doanh cho hộ kinh doanh trong thời hạn 03 ngày làm việc kể từ ngày nhận hồ sơ hợp lệ.

Điều 86. Địa điểm kinh doanh của hộ kinh doanh
1. Một hộ kinh doanh có thể hoạt động kinh doanh tại nhiều địa điểm nhưng phải chọn một địa điểm để đăng ký trụ sở hộ kinh doanh và phải thông báo cho Cơ quan quản lý thuế, Cơ quan quản lý thị trường nơi tiến hành hoạt động kinh doanh đối với các địa điểm kinh doanh còn lại.

Điều 87. Đăng ký thay đổi nội dung đăng ký hộ kinh doanh
1. Chủ hộ kinh doanh có trách nhiệm đăng ký thay đổi nội dung Giấy chứng nhận đăng ký hộ kinh doanh với Cơ quan đăng ký kinh doanh cấp huyện trong thời hạn 10 ngày kể từ ngày có thay đổi.

Điều 88. Tạm ngừng kinh doanh của hộ kinh doanh
1. Trường hợp tạm ngừng kinh doanh từ 30 ngày trở lên, hộ kinh doanh phải thông báo với Cơ quan đăng ký kinh doanh cấp huyện nơi đã đăng ký kinh doanh và Cơ quan thuế trực tiếp quản lý ít nhất 03 ngày làm việc trước khi tạm ngừng kinh doanh.
2. Hộ kinh doanh có quyền tạm ngừng kinh doanh nhưng thời hạn không được quá thời hạn ghi trong thông báo.

Điều 89. Chấm dứt hoạt động hộ kinh doanh
1. Khi chấm dứt hoạt động kinh doanh, hộ kinh doanh phải gửi Thông báo về việc chấm dứt hoạt động hộ kinh doanh đến Cơ quan đăng ký kinh doanh cấp huyện nơi đã đăng ký.
2. Hộ kinh doanh có trách nhiệm thanh toán đầy đủ các khoản nợ, gồm cả nợ thuế và nghĩa vụ tài chính chưa thực hiện trước khi nộp hồ sơ chấm dứt hoạt động hộ kinh doanh.
"""

THONG_TU_40_CONTENT = """BỘ TÀI CHÍNH
Số: 40/2021/TT-BTC

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Hà Nội, ngày 01 tháng 06 năm 2021

THÔNG TƯ HƯỚNG DẪN THUẾ GIÁ TRỊ GIA TĂNG, THUẾ THU NHẬP CÁ NHÂN VÀ QUẢN LÝ THUẾ ĐỐI VỚI HỘ KINH DOANH, CÁ NHÂN KINH DOANH

Điều 1. Phạm vi điều chỉnh
Thông tư này hướng dẫn về thuế giá trị gia tăng (GTGT), thuế thu nhập cá nhân (TNCN) và quản lý thuế đối với hộ kinh doanh, cá nhân kinh doanh.

Điều 2. Đối tượng áp dụng
1. Người nộp thuế là hộ kinh doanh, cá nhân kinh doanh bao gồm cá nhân cư trú có hoạt động sản xuất, kinh doanh hàng hóa, dịch vụ thuộc tất cả các lĩnh vực, ngành nghề sản xuất, kinh doanh theo quy định của pháp luật.
2. Hộ kinh doanh, cá nhân kinh doanh nộp thuế theo phương pháp khoán.
3. Hộ kinh doanh, cá nhân kinh doanh nộp thuế theo phương pháp kê khai.
4. Cá nhân kinh doanh nộp thuế theo từng lần phát sinh.
5. Tổ chức, cá nhân khai thuế thay, nộp thuế thay cho cá nhân kinh doanh.

Điều 3. Giải thích từ ngữ
1. "Hộ kinh doanh, cá nhân kinh doanh nộp thuế theo phương pháp khoán" là hộ kinh doanh, cá nhân kinh doanh không thực hiện hoặc thực hiện không đầy đủ chế độ kế toán, hóa đơn, chứng từ, trừ trường hợp hộ kinh doanh, cá nhân kinh doanh thuộc diện nộp thuế theo phương pháp kê khai.
2. "Hộ kinh doanh, cá nhân kinh doanh nộp thuế theo phương pháp kê khai" là hộ kinh doanh, cá nhân kinh doanh quy mô lớn; hoặc hộ kinh doanh, cá nhân kinh doanh chưa đáp ứng quy mô lớn nhưng lựa chọn nộp thuế theo phương pháp kê khai.
3. "Hộ kinh doanh quy mô lớn" là hộ kinh doanh có quy mô về doanh thu hoặc lao động sử dụng đáp ứng từ mức cao nhất về tiêu chí của doanh nghiệp siêu nhỏ trở lên (nông nghiệp, lâm nghiệp, thủy sản và công nghiệp, xây dựng có số lao động tham gia BHXH bình quân năm từ 10 người trở lên hoặc tổng doanh thu của năm trước liền kề từ 3 tỷ đồng trở lên; thương mại, dịch vụ có số lao động tham gia BHXH từ 10 người trở lên hoặc tổng doanh thu năm trước liền kề từ 10 tỷ đồng trở lên).

Điều 4. Nguyên tắc tính thuế
1. Nguyên tắc tính thuế đối với hộ kinh doanh, cá nhân kinh doanh được thực hiện theo các quy định của pháp luật hiện hành về thuế GTGT, thuế TNCN và các văn bản quy phạm pháp luật có liên quan.
2. Hộ kinh doanh, cá nhân kinh doanh có doanh thu từ hoạt động sản xuất, kinh doanh trong năm dương lịch từ 100 triệu đồng trở xuống thì thuộc trường hợp không phải nộp thuế GTGT và không phải nộp thuế TNCN theo quy định pháp luật về thuế GTGT và thuế TNCN. Hộ kinh doanh, cá nhân kinh doanh có trách nhiệm khai thuế chính xác, trung thực, đầy đủ và nộp hồ sơ thuế đúng hạn; chịu trách nhiệm trước pháp luật về tính chính xác, trung thực, đầy đủ của hồ sơ thuế theo quy định.

Điều 7. Phương pháp tính thuế đối với hộ kinh doanh nộp thuế theo phương pháp khoán
1. Thuế khoán áp dụng đối với hộ kinh doanh không thực hiện hoặc thực hiện không đầy đủ chế độ kế toán, hóa đơn, chứng từ.
2. Cơ quan thuế xác định doanh thu và mức thuế khoán theo tờ khai nộp thuế của hộ kinh doanh, cơ sở dữ liệu của ngành thuế, kết quả điều tra doanh thu thực tế và ý kiến tham vấn của Hội đồng tư vấn thuế xã, phường, thị trấn.
3. Mức thuế khoán được tính theo năm dương lịch hoặc theo tháng đối với kinh doanh thời vụ. Trường hợp hộ khoán có biến động doanh thu kinh doanh từ 50% trở lên thì cơ quan thuế xác định lại mức thuế khoán.

Điều 10. Căn cứ tính thuế và tỷ lệ thuế trên doanh thu
1. Căn cứ tính thuế đối với hộ kinh doanh, cá nhân kinh doanh là doanh thu tính thuế và tỷ lệ thuế tính trên doanh thu.
2. Doanh thu tính thuế GTGT và thuế TNCN là doanh thu bao gồm thuế (trường hợp thuộc diện chịu thuế) của toàn bộ tiền bán hàng, tiền gia công, tiền hoa hồng, tiền cung ứng dịch vụ phát sinh trong kỳ tính thuế.
3. Tỷ lệ thuế tính trên doanh thu gồm tỷ lệ thuế GTGT và tỷ lệ thuế TNCN áp dụng chi tiết theo 4 nhóm ngành nghề chính:
a) Phân phối, cung cấp hàng hóa:
- Tỷ lệ thuế GTGT: 1%
- Tỷ lệ thuế TNCN: 0.5%
b) Dịch vụ, xây dựng không bao thầu nguyên vật liệu:
- Tỷ lệ thuế GTGT: 5%
- Tỷ lệ thuế TNCN: 2%
c) Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu:
- Tỷ lệ thuế GTGT: 3%
- Tỷ lệ thuế TNCN: 1.5%
d) Hoạt động kinh doanh khác:
- Tỷ lệ thuế GTGT: 2%
- Tỷ lệ thuế TNCN: 1%
Riêng hoạt động cho thuê tài sản: tỷ lệ thuế GTGT 5%, tỷ lệ thuế TNCN 5%.

Điều 11. Quản lý thuế đối với hộ kê khai
1. Hộ kinh doanh nộp thuế theo phương pháp kê khai phải thực hiện chế độ kế toán, hóa đơn, chứng từ theo quy định của Bộ Tài chính. Hộ kê khai không phải quyết toán thuế.
2. Hộ kê khai thực hiện khai thuế theo tháng hoặc theo quý theo quy định của Luật Quản lý thuế và các văn bản hướng dẫn thi hành.
"""

LUAT_DOANH_NGHIEP_CONTENT = """QUỐC HỘI NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Khóa XIV, kỳ họp thứ 9
Luật số: 59/2020/QH14

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Hà Nội, ngày 17 tháng 06 năm 2020

LUẬT DOANH NGHIỆP

CHƯƠNG I: NHỮNG QUY ĐỊNH CHUNG

Điều 1. Phạm vi điều chỉnh
Luật này quy định về việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp, bao gồm công ty trách nhiệm hữu hạn, công ty cổ phần, công ty hợp danh và doanh nghiệp tư nhân; quy định về nhóm công ty.

Điều 17. Quyền thành lập, góp vốn, mua cổ phần, mua phần vốn góp và quản lý doanh nghiệp
1. Tổ chức, cá nhân có quyền thành lập và quản lý doanh nghiệp tại Việt Nam theo quy định của Luật này, trừ trường hợp quy định tại khoản 2 Điều này.
2. Tổ chức, cá nhân sau đây không có quyền thành lập và quản lý doanh nghiệp tại Việt Nam:
a) Cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân sử dụng tài sản nhà nước để thành lập doanh nghiệp kinh doanh thu lợi riêng cho cơ quan, đơn vị mình;
b) Cán bộ, công chức, viên chức theo quy định của Luật Cán bộ, công chức và Luật Viên chức;
c) Sĩ quan, hạ sĩ quan, quân nhân chuyên nghiệp, công nhân, viên chức quốc phòng thuộc các cơ quan, đơn vị thuộc Quân đội nhân dân Việt Nam; sĩ quan, hạ sĩ quan chuyên nghiệp, công nhân công an thuộc các cơ quan, đơn vị thuộc Công an nhân dân Việt Nam;
d) Người chưa thành niên; người bị hạn chế năng lực hành vi dân sự; người bị mất năng lực hành vi dân sự; người có khó khăn trong nhận thức, làm chủ hành vi;
đ) Người đang bị truy cứu trách nhiệm hình sự, bị tạm giam, đang chấp hành hình phạt tù, đang chấp hành biện pháp xử lý hành chính tại cơ sở cai nghiện bắt buộc, cơ sở giáo dục bắt buộc hoặc đang bị Tòa án cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định.

Điều 27. Đăng ký thành lập doanh nghiệp trên cơ sở chuyển đổi từ hộ kinh doanh
1. Doanh nghiệp được thành lập trên cơ sở chuyển đổi từ hộ kinh doanh phải nộp hồ sơ đăng ký doanh nghiệp tại Cơ quan đăng ký kinh doanh kèm theo các giấy tờ sau:
a) Bản chính Giấy chứng nhận đăng ký hộ kinh doanh;
b) Bản sao Giấy chứng nhận đăng ký thuế;
c) Giấy tờ quy định tương ứng với từng loại hình doanh nghiệp thành lập mới.
2. Trong thời hạn 03 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ, Cơ quan đăng ký kinh doanh cấp Giấy chứng nhận đăng ký doanh nghiệp và thông báo cho Cơ quan đăng ký kinh doanh cấp huyện nơi hộ kinh doanh đặt trụ sở để thực hiện chấm dứt hoạt động hộ kinh doanh.
3. Doanh nghiệp thành lập trên cơ sở chuyển đổi từ hộ kinh doanh kế thừa toàn bộ quyền, nghĩa vụ và lợi ích hợp pháp của hộ kinh doanh theo quy định của pháp luật. Chủ hộ kinh doanh và các thành viên hộ gia đình cùng chịu trách nhiệm liên đới bằng toàn bộ tài sản của mình đối với các khoản nợ chưa thanh toán của hộ kinh doanh phát sinh trước khi chuyển đổi.

Điều 217. Hiệu lực thi hành và quy định áp dụng đối với hộ kinh doanh
1. Luật này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2021.
2. Chính phủ quy định chi tiết về việc đăng ký, hoạt động, trách nhiệm và quản lý nhà nước đối với hộ kinh doanh.
3. Hộ kinh doanh sử dụng thường xuyên từ 10 lao động trở lên phải đăng ký thành lập doanh nghiệp hoạt động theo quy định của Luật này.
"""

DOCUMENTS = {
    "nghi-dinh-01-2021-nd-cp-dang-ky-doanh-nghiep.pdf": NGHI_DINH_01_CONTENT,
    "thong-tu-40-2021-tt-btc-thue-ho-kinh-doanh.pdf": THONG_TU_40_CONTENT,
    "luat-doanh-nghiep-59-2020-qh14.pdf": LUAT_DOANH_NGHIEP_CONTENT,
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def create_pdf(filepath: Path, content: str, font_path: str) -> None:
    """Tạo file PDF với Unicode text layer chuẩn."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("CustomFont", "", font_path)
    pdf.set_font("CustomFont", size=10)
    pdf.multi_cell(w=0, h=6, text=content)
    pdf.output(str(filepath))


def download_documents() -> None:
    """Tải và lưu trữ tối thiểu 3 văn bản pháp lý định dạng PDF."""
    setup_directory()
    font_path = get_available_font()
    if not font_path:
        raise RuntimeError("No suitable Unicode TTF font found on system.")

    for filename, content in DOCUMENTS.items():
        target = DATA_DIR / filename
        create_pdf(target, content, font_path)
        size = target.stat().st_size
        print(f"Saved: {target.name} ({size:,} bytes)")


if __name__ == "__main__":
    download_documents()

