"""
Kịch bản tự động khởi tạo Slide Báo Cáo Bảo Vệ Đồ Án PowerPoint (.pptx)
Dự án: Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Bất Động Sản Việt Nam
Sinh viên thực hiện: Phạm Văn Minh
Mã sinh viên: 23010350
Email: 23010350@st.phenikaa-uni.edu.vn
Đơn vị đào tạo: Trường Công nghệ Thông tin - Trường Đại học Phenikaa

Chuẩn thiết kế:
  - Tỷ lệ màn hình rộng Widescreen 16:9 (13.333 in x 7.5 in)
  - Tông màu học thuật Phenikaa: Deep Navy (#0F2942), Cobalt Blue (#1E40AF), Phenikaa Amber (#F58220)
  - Nhúng trực tiếp 8 hình ảnh biểu đồ phân tích độ nét cao
  - Bảng đối chuẩn trước/sau, thông số mô hình và hướng dẫn vận hành
  - 100% Tiếng Việt chuẩn mực, tuyệt đối không dùng tiếng Anh mở ngoặc cạnh tiếng Việt
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Bảng màu chuẩn
COLOR_NAVY = RGBColor(15, 41, 66)      # #0F2942
COLOR_BLUE = RGBColor(30, 64, 175)     # #1E40AF
COLOR_ORANGE = RGBColor(245, 130, 32)  # #F58220
COLOR_BG_CARD = RGBColor(248, 250, 252) # #F8FAFC
COLOR_BORDER = RGBColor(226, 232, 240) # #E2E8F0
COLOR_TEXT_DARK = RGBColor(15, 23, 42) # #0F172A
COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # #64748B
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_GREEN = RGBColor(22, 163, 74)   # #16A34A

def create_slide_header(slide, title_text, category_text="TÍCH HỢP & PHÂN TÍCH DỮ LIỆU LỚN | TRƯỜNG ĐH PHENIKAA"):
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Arial"
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_ORANGE
    p_cat.space_after = Pt(2)
    
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = "Arial"
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_NAVY

def create_slide_footer(slide, current_slide, total_slides=16):
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.7), Inches(0.35))
    tf = footer_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"Sinh viên: Phạm Văn Minh - Mã sinh viên: 23010350 - Trường Đại học Phenikaa                                                     Slide {current_slide} / {total_slides}"
    p.font.name = "Arial"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED

def add_card(slide, left, top, width, height, bg_color=COLOR_BG_CARD, border_color=COLOR_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1)
    return shape

def add_bullet_point(tf, bold_prefix, normal_text, font_size=13, space_after=8):
    p = tf.add_paragraph()
    p.space_after = Pt(space_after)
    p.level = 0
    
    r1 = p.add_run()
    r1.text = "• " + bold_prefix + ": " if bold_prefix else "• "
    r1.font.name = "Arial"
    r1.font.size = Pt(font_size)
    r1.font.bold = True
    r1.font.color.rgb = COLOR_NAVY
    
    r2 = p.add_run()
    r2.text = normal_text
    r2.font.name = "Arial"
    r2.font.size = Pt(font_size)
    r2.font.bold = False
    r2.font.color.rgb = COLOR_TEXT_DARK

def generate_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # ==========================================================================
    # SLIDE 1: TRANG BÌA
    # ==========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    
    bg = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_NAVY
    bg.line.fill.background()
    
    acc = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(0.15), Inches(5.0))
    acc.fill.solid()
    acc.fill.fore_color.rgb = COLOR_ORANGE
    acc.line.fill.background()
    
    title_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.1), Inches(11.3), Inches(5.2))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.text = "TRƯỜNG ĐẠI HỌC PHENIKAA — TRƯỜNG CÔNG NGHỆ THÔNG TIN"
    p1.font.name = "Arial"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_ORANGE
    p1.space_after = Pt(8)
    
    p2 = tf1.add_paragraph()
    p2.text = "BÁO CÁO BẢO VỆ ĐỒ ÁN HỌC PHẦN: TÍCH HỢP VÀ PHÂN TÍCH DỮ LIỆU LỚN"
    p2.font.name = "Arial"
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_WHITE
    p2.space_after = Pt(16)
    
    p3 = tf1.add_paragraph()
    p3.text = "NGHIÊN CỨU XÂY DỰNG HỆ THỐNG HỒ DỮ LIỆU ĐA TẦNG MEDALLION TÍCH HỢP DỮ LIỆU LỚN VÀ ĐỊNH GIÁ BẤT ĐỘNG SẢN VIỆT NAM BẰNG MÔ HÌNH HỌC MÁY LIGHTGBM"
    p3.font.name = "Arial"
    p3.font.size = Pt(23)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_WHITE
    p3.space_after = Pt(28)
    
    p4 = tf1.add_paragraph()
    p4.text = "Sinh viên thực hiện: PHẠM VĂN MINH       |       Mã sinh viên: 23010350"
    p4.font.name = "Arial"
    p4.font.size = Pt(14)
    p4.font.bold = True
    p4.font.color.rgb = COLOR_ORANGE
    p4.space_after = Pt(6)
    
    p5 = tf1.add_paragraph()
    p5.text = "Email: 23010350@st.phenikaa-uni.edu.vn   |   Khóa: K17 — Công nghệ Thông tin"
    p5.font.name = "Arial"
    p5.font.size = Pt(12.5)
    p5.font.color.rgb = COLOR_WHITE
    p5.space_after = Pt(6)
    
    p6 = tf1.add_paragraph()
    p6.text = "Công nghệ: Apache PySpark 3.5 • Parquet Snappy • PostgreSQL/SQLite • LightGBM • Streamlit"
    p6.font.name = "Arial"
    p6.font.size = Pt(11.5)
    p6.font.color.rgb = COLOR_TEXT_MUTED
    
    # ==========================================================================
    # SLIDE 2: ĐẶT VẤN ĐỀ & THÁCH THỨC DỮ LIỆU LỚN
    # ==========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide2, "1. Tổng Quan Bài Toán & Thách Thức Dữ Liệu Lớn")
    create_slide_footer(slide2, 2)
    
    stat_data = [
        ("KHO NGUỒN HUGGING FACE", "3,500,744", "bản ghi trên 10 phân mảnh"),
        ("PHÂN MẢNH THỰC NGHIỆM", "350,075", "bản ghi thô Shard 0000 Parquet"),
        ("TẦNG VÀNG SẠCH SAU ETL", "300,295", "bản ghi phục vụ phân tích & ML (85.8%)")
    ]
    for i, (title, big_val, desc) in enumerate(stat_data):
        c_left = Inches(0.8 + i * 4.0)
        card = add_card(slide2, c_left, Inches(1.5), Inches(3.7), Inches(1.3))
        tf = card.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_MUTED
        
        p_v = tf.add_paragraph()
        p_v.text = big_val
        p_v.font.name = "Arial"
        p_v.font.size = Pt(22)
        p_v.font.bold = True
        p_v.font.color.rgb = COLOR_BLUE
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = COLOR_TEXT_DARK
        
    c_main = add_card(slide2, Inches(0.8), Inches(3.0), Inches(11.7), Inches(3.8))
    tf_m = c_main.text_frame
    tf_m.word_wrap = True
    p_init = tf_m.paragraphs[0]
    p_init.text = "4 THÁCH THỨC ĐẶC THÙ CỦA DỮ LIỆU BẤT ĐỘNG SẢN VIỆT NAM:"
    p_init.font.name = "Arial"
    p_init.font.size = Pt(13.5)
    p_init.font.bold = True
    p_init.font.color.rgb = COLOR_NAVY
    p_init.space_after = Pt(12)
    
    add_bullet_point(tf_m, "Quy mô dữ liệu lớn", "3.5 triệu tin đăng vượt quá khả năng xử lý trên bộ nhớ đơn lẻ; giải quyết bằng kiến trúc xử lý phân tán Apache PySpark.", font_size=12)
    add_bullet_point(tf_m, "Độ tin cậy và xử lý nhiễu loạn", "Môi giới đăng tải hàng loạt tin trùng lặp; tin rác báo giá ảo 881,020 tỷ đồng, diện tích 24 triệu m²; thiếu chuẩn hóa đơn vị (tỷ, triệu, đ/m², thương lượng).", font_size=12)
    add_bullet_point(tf_m, "Dữ liệu văn bản phi cấu trúc", "Yếu tố định giá quan trọng như sổ đỏ, nhà mặt tiền, ngõ ô tô ẩn giấu trong văn bản miêu tả; giải quyết bằng bộ trích xuất biểu thức chính quy tự động.", font_size=12)
    add_bullet_point(tf_m, "Truy vết nguồn gốc và kiểm toán", "Tin đăng phát sinh liên tục theo thời gian; hệ thống gắn siêu dữ liệu kiểm toán gồm thời điểm nạp, mã lô và phân mảnh nguồn.", font_size=12)
    add_bullet_point(tf_m, "Giá trị ứng dụng thực tiễn", "Xây dựng mô hình định giá tự động LightGBM và bảng điều khiển Streamlit tương tác 4 phân hệ hỗ trợ ra quyết định đầu tư.", font_size=12)

    # ==========================================================================
    # SLIDE 3: KIẾN TRÚC HỒ DỮ LIỆU MEDALLION 6 TẦNG
    # ==========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide3, "2. Kiến Trúc Hồ Dữ Liệu Medallion 6 Tầng")
    create_slide_footer(slide3, 3)
    
    img_path = BASE_DIR / "docs/images/00_architecture_flowchart.png"
    if img_path.exists():
        slide3.shapes.add_picture(str(img_path), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_arch = add_card(slide3, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_a = c_arch.text_frame
    tf_a.word_wrap = True
    
    p_at = tf_a.paragraphs[0]
    p_at.text = "ĐẶC TẢ CÔNG NGHỆ 6 TẦNG:"
    p_at.font.name = "Arial"
    p_at.font.size = Pt(13)
    p_at.font.bold = True
    p_at.font.color.rgb = COLOR_NAVY
    p_at.space_after = Pt(10)
    
    add_bullet_point(tf_a, "1. Thu nạp thô", "Nạp bất đồng bộ từ Hugging Face qua Polars và Arrow, gắn mã định danh lô và thời điểm nạp.", font_size=11, space_after=6)
    add_bullet_point(tf_a, "2. Tầng Đồng", "Lưu trữ nguyên trạng bất biến định dạng Parquet Snappy (350,075 dòng, 153.9 MB).", font_size=11, space_after=6)
    add_bullet_point(tf_a, "3. Tầng Bạc", "Làm sạch bằng PySpark, khử trùng lặp đa thuộc tính, chuẩn hóa kiểu dữ liệu số (307,457 dòng, 130.0 MB).", font_size=11, space_after=6)
    add_bullet_point(tf_a, "4. Tầng Vàng", "Lọc ngoại lệ, trích xuất đặc trưng văn bản, biến đổi chuẩn hóa logarit (300,295 dòng, 128.2 MB).", font_size=11, space_after=6)
    add_bullet_point(tf_a, "5. CSDL Phục vụ", "PostgreSQL và SQLite, đánh 4 chỉ mục B-Tree, nạp theo khối 10,000 dòng, dung lượng chỉ 17.4 MB.", font_size=11, space_after=6)
    add_bullet_point(tf_a, "6. Giao diện & ML", "Mô hình LightGBM định giá trực tuyến và Bảng điều khiển Streamlit 4 Tab tương tác.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 4: THUẬT TOÁN KHỬ TRÙNG LẶP & PHỄU LƯU LƯỢNG
    # ==========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide4, "3. Thuật Toán Khử Trùng Lặp & Phễu Lưu Lượng Dữ Liệu")
    create_slide_footer(slide4, 4)
    
    img_funnel = BASE_DIR / "docs/images/01_pipeline_funnel_retention.png"
    if img_funnel.exists():
        slide4.shapes.add_picture(str(img_funnel), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_fn = add_card(slide4, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_fn = c_fn.text_frame
    tf_fn.word_wrap = True
    
    p_fnt = tf_fn.paragraphs[0]
    p_fnt.text = "CƠ CHẾ KHỬ TRÙNG & PHỄU LƯU LƯỢNG:"
    p_fnt.font.name = "Arial"
    p_fnt.font.size = Pt(13)
    p_fnt.font.bold = True
    p_fnt.font.color.rgb = COLOR_NAVY
    p_fnt.space_after = Pt(10)
    
    add_bullet_point(tf_fn, "Khóa băm tổ hợp đa thuộc tính", "K_khử_trùng = Băm(chữ_thường(tiêu_đề) || tỉnh || huyện || xã || chuỗi_giá || diện_tích)", font_size=11, space_after=6)
    add_bullet_point(tf_fn, "Khử chính xác 29,686 trùng lặp", "Chiếm 8.48% dữ liệu thô, giải quyết triệt để tình trạng một căn nhà được nhiều môi giới spam.", font_size=11, space_after=6)
    add_bullet_point(tf_fn, "Lọc 12,932 tin thiếu giá / diện tích", "Loại bỏ các tin thỏa thuận, thương lượng, giá âm hoặc diện tích rỗng không thể khôi phục.", font_size=11, space_after=6)
    add_bullet_point(tf_fn, "Tỷ lệ giữ lại Tầng Bạc", "307,457 bản ghi sạch (đạt 87.83% so với Tầng Đồng ban đầu).", font_size=11, space_after=6)
    add_bullet_point(tf_fn, "Tỷ lệ toàn trình", "Toàn bộ pipeline giữ lại 85.78% dữ liệu chuẩn mực, vượt xa tiêu chuẩn nghiệm thu 80%.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 5: KIỂM TOÁN CHẤT LƯỢNG & GIÁ TRỊ KHUYẾT THIẾU
    # ==========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide5, "4. Kiểm Toán Chất Lượng & Xử Lý Giá Trị Khuyết Thiếu")
    create_slide_footer(slide5, 5)
    
    img_miss = BASE_DIR / "docs/images/02_data_quality_missing_analysis.png"
    if img_miss.exists():
        slide5.shapes.add_picture(str(img_miss), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_ms = add_card(slide5, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_ms = c_ms.text_frame
    tf_ms.word_wrap = True
    
    p_mst = tf_ms.paragraphs[0]
    p_mst.text = "CHIẾN LƯỢC XỬ LÝ 3 NHÓM THUỘC TÍNH:"
    p_mst.font.name = "Arial"
    p_mst.font.size = Pt(13)
    p_mst.font.bold = True
    p_mst.font.color.rgb = COLOR_NAVY
    p_mst.space_after = Pt(10)
    
    add_bullet_point(tf_ms, "Nhóm sạch (< 5% khuyết)", "Tiêu đề (0%), mô tả (0%), tỉnh thành (0%), quận huyện (1.75%), giá bán (0%), diện tích (0%). Giữ nguyên vẹn, điền 'Không rõ' cho quận huyện thiếu.", font_size=11, space_after=6)
    add_bullet_point(tf_ms, "Nhóm khuyết vừa (5% - 50%)", "Phường xã (14.4%), tên đường (40.4%), số phòng ngủ (24.8%), hướng nhà (46.8%). Điền 'Không rõ' cho phân loại và giá trị trung vị theo quận cho số phòng ngủ.", font_size=11, space_after=6)
    add_bullet_point(tf_ms, "Nhóm khuyết cao (> 50%)", "Tên dự án (86.1%), mặt tiền (64.2%), độ rộng đường (61.5%).", font_size=11, space_after=6)
    add_bullet_point(tf_ms, "Nguyên tắc nghiệp vụ", "TUYỆT ĐỐI KHÔNG XÓA CỘT khuyết cao vì khi có dữ liệu (ví dụ nhà mặt phố), giá trị kinh tế tăng vọt. Áp dụng kỹ thuật điền khuyết riêng biệt và nhị phân hóa cờ đặc trưng.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 6: THUẬT TOÁN LỌC NGOẠI LỆ & ĐỐI CHIẾU TRƯỚC / SAU
    # ==========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide6, "5. Thuật Toán Lọc Ngoại Lệ Thống Kê Kháng Nhiễu")
    create_slide_footer(slide6, 6)
    
    img_dist = BASE_DIR / "docs/images/03_distribution_outlier_analysis.png"
    if img_dist.exists():
        slide6.shapes.add_picture(str(img_dist), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_dst = add_card(slide6, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_dst = c_dst.text_frame
    tf_dst.word_wrap = True
    
    p_dst = tf_dst.paragraphs[0]
    p_dst.text = "ĐỐI CHIẾU SỐ LIỆU TRƯỚC (BẠC) VS SAU (VÀNG):"
    p_dst.font.name = "Arial"
    p_dst.font.size = Pt(12.5)
    p_dst.font.bold = True
    p_dst.font.color.rgb = COLOR_NAVY
    p_dst.space_after = Pt(8)
    
    add_bullet_point(tf_dst, "Loại bỏ 7,162 ngoại lệ (2.33%)", "Kết hợp biên nghiệp vụ [0.1 - 500 tỷ, 10 - 5000 m²] với phân vị khoảng liên tứ phân vị trên thang logarit.", font_size=10.5, space_after=5)
    add_bullet_point(tf_dst, "Độ lệch chuẩn Giá bán", "Từ 2,006.6 Tỷ GIẢM 77 LẦN còn 25.98 Tỷ VNĐ (Triệt tiêu tin ảo 881,020 tỷ).", font_size=10.5, space_after=5)
    add_bullet_point(tf_dst, "TRUNG VỊ GIÁ BẢO TOÀN", "7.2 Tỷ ở Tầng Bạc -> 7.3 Tỷ ở Tầng Vàng. Không làm méo mó bản chất thị trường!", font_size=10.5, space_after=5)
    add_bullet_point(tf_dst, "Độ lệch chuẩn Diện tích", "Từ 51,332 m² GIẢM 208 LẦN còn 246.5 m² (Triệt tiêu diện tích ảo 24 triệu m²).", font_size=10.5, space_after=5)
    add_bullet_point(tf_dst, "TRUNG VỊ DIỆN TÍCH", "Giữ nguyên vẹn 100% tại 80.0 m².", font_size=10.5, space_after=5)
    add_bullet_point(tf_dst, "Độ lệch chuẩn Đơn giá", "Từ 48,836 Tr/m² GIẢM 385 LẦN còn 126.8 Tr/m².", font_size=10.5, space_after=5)

    # ==========================================================================
    # SLIDE 7: PHÂN TÍCH TOÀN CẢNH THỊ TRƯỜNG BẤT ĐỘNG SẢN
    # ==========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide7, "6. Toàn Cảnh Thị Trường Bất Động Sản")
    create_slide_footer(slide7, 7)
    
    img_mkt = BASE_DIR / "docs/images/04_market_distribution.png"
    if img_mkt.exists():
        slide7.shapes.add_picture(str(img_mkt), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_mkt = add_card(slide7, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_mkt = c_mkt.text_frame
    tf_mkt.word_wrap = True
    
    p_mktt = tf_mkt.paragraphs[0]
    p_mktt.text = "PHÂN TÍCH KHÁM PHÁ THỊ TRƯỜNG:"
    p_mktt.font.name = "Arial"
    p_mktt.font.size = Pt(13)
    p_mktt.font.bold = True
    p_mktt.font.color.rgb = COLOR_NAVY
    p_mktt.space_after = Pt(10)
    
    add_bullet_point(tf_mkt, "Hà Nội dẫn đầu giá trung vị", "8.90 Tỷ VNĐ (104.8k tin), đơn giá trung vị 148.5 Tr/m², giao dịch sôi động nhà ngõ & mặt phố.", font_size=11, space_after=6)
    add_bullet_point(tf_mkt, "TP. Hồ Chí Minh bám sát", "8.50 Tỷ VNĐ (105.7k tin), đơn giá trung vị 135.2 Tr/m², biên độ phân hóa lớn giữa trung tâm và vùng ven.", font_size=11, space_after=6)
    add_bullet_point(tf_mkt, "Đà Nẵng & Bình Dương", "Đà Nẵng trung vị 7.57 Tỷ (thị trường ven biển); Bình Dương trung vị 2.91 Tỷ (nhà ở công nghiệp/chuyên gia).", font_size=11, space_after=6)
    add_bullet_point(tf_mkt, "Cơ cấu theo loại hình", "Nhà mặt phố & Biệt thự liền kề có giá trị trung vị cao nhất, tiếp theo là Nhà riêng và Căn hộ chung cư.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 8: NLP TRÍCH XUẤT ĐẶC TRƯNG & BIẾN ĐỔI LOGARIT
    # ==========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide8, "7. Kỹ Thuật Đặc Trưng Văn Bản & Chuẩn Hóa Logarit")
    create_slide_footer(slide8, 8)
    
    img_eda_p = BASE_DIR / "docs/images/eda_price_distribution.png"
    if img_eda_p.exists():
        slide8.shapes.add_picture(str(img_eda_p), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_nlp = add_card(slide8, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_nlp = c_nlp.text_frame
    tf_nlp.word_wrap = True
    
    p_nlpt = tf_nlp.paragraphs[0]
    p_nlpt.text = "TRÍCH XUẤT ĐẶC TRƯNG & CHUẨN HÓA:"
    p_nlpt.font.name = "Arial"
    p_nlpt.font.size = Pt(13)
    p_nlpt.font.bold = True
    p_nlpt.font.color.rgb = COLOR_NAVY
    p_nlpt.space_after = Pt(10)
    
    add_bullet_point(tf_nlp, "Cờ pháp lý sổ đỏ/hồng", "Nhận diện từ khóa 'sổ đỏ', 'sổ hồng', 'chính chủ', 'pháp lý chuẩn'. Đẩy thanh khoản và giá nhà tăng rõ rệt.", font_size=11, space_after=6)
    add_bullet_point(tf_nlp, "Cờ vị trí mặt phố và ngõ hẻm", "Nhận diện 'mặt phố', 'kinh doanh' so với 'ngõ hẻm', 'ba gác'. Mặt phố có đơn giá gấp 2-3 lần nhà ngõ.", font_size=11, space_after=6)
    add_bullet_point(tf_nlp, "Cờ tiện nghi nội thất và ô tô", "Nhận diện 'full nội thất', 'ô tô đỗ cửa', 'gara ô tô'.", font_size=11, space_after=6)
    add_bullet_point(tf_nlp, "Biến đổi logarit tự nhiên", "Kéo hệ số bất đối xứng từ 6.70 xuống 0.24 (gần chuẩn đối xứng), giúp hàm mục tiêu hội tụ tối ưu.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 9: GIAO THỨC CHIA 3 TẬP CHỐNG RÒ RỈ DỮ LIỆU
    # ==========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide9, "8. Giao Thức Phân Chia Ba Tập Dữ Liệu Chống Rò Rỉ")
    create_slide_footer(slide9, 9)
    
    splits_info = [
        ("TẬP HUẤN LUYỆN", "70%", "210,206 mẫu", "Toàn bộ tiền xử lý phân loại, điền khuyết, chuẩn hóa CHỈ ĐƯỢC HỌC trên tập dữ liệu này. Tuyệt đối không nhìn trước dữ liệu kiểm thử."),
        ("TẬP KIỂM ĐỊNH", "15%", "45,044 mẫu", "Sử dụng độc quyền để điều chỉnh siêu tham số và kích hoạt cơ chế dừng sớm chống quá khớp."),
        ("TẬP KIỂM THỬ ĐỘC LẬP", "15%", "45,045 mẫu", "Được giữ bí mật tuyệt đối trong quá trình huấn luyện; CHỈ ĐƯỢC CHẤM ĐIỂM ĐÚNG 1 LẦN DUY NHẤT để đánh giá năng lực tổng quát hóa.")
    ]
    for i, (title, pct, count, desc) in enumerate(splits_info):
        c_left = Inches(0.8 + i * 4.0)
        card = add_card(slide9, c_left, Inches(1.5), Inches(3.7), Inches(5.2))
        tf = card.text_frame
        tf.word_wrap = True
        
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_NAVY
        p_t.space_after = Pt(10)
        
        p_p = tf.add_paragraph()
        p_p.text = pct
        p_p.font.name = "Arial"
        p_p.font.size = Pt(36)
        p_p.font.bold = True
        p_p.font.color.rgb = COLOR_BLUE
        
        p_c = tf.add_paragraph()
        p_c.text = count
        p_c.font.name = "Arial"
        p_c.font.size = Pt(14)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_ORANGE
        p_c.space_after = Pt(16)
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(11.5)
        p_d.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 10: SO SÁNH THUẬT TOÁN: RIDGE VS LIGHTGBM
    # ==========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide10, "9. Thuật Toán Học Máy: Hồi Quy Ridge Cơ Sở vs LightGBM")
    create_slide_footer(slide10, 10)
    
    rows = 7
    cols = 4
    left = Inches(0.8)
    top = Inches(1.5)
    width = Inches(11.7)
    height = Inches(5.0)
    
    table_shape = slide10.shapes.add_table(rows, cols, left, top, width, height)
    tbl = table_shape.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(2.6)
    tbl.columns[2].width = Inches(2.6)
    tbl.columns[3].width = Inches(3.3)
    
    headers = ["Chỉ Số Đánh Giá", "Hồi Quy Ridge Cơ Sở", "Mô Hình LightGBM", "Mức Độ Cải Thiện Vượt Trội"]
    data = [
        ["Hệ số xác định R² trên thang logarit", "0.6266 (62.7%)", "0.8537 (85.4%)", "TĂNG +36.2% (Giải thích 85.4% phương sai)"],
        ["Sai số căn quân phương RMSE trên thang logarit", "0.6556", "0.4104", "GIẢM -37.4% sai số toàn phương"],
        ["Sai số tuyệt đối trung bình MAE trên thang logarit", "0.4918", "0.2907", "GIẢM -40.9% sai số tuyệt đối"],
        ["MAE trên thang tiền tệ thực tế", "10.18 Tỷ VNĐ", "4.64 Tỷ VNĐ", "GIẢM -54.4% (Sai số giảm hơn một nửa!)"],
        ["Sai số tuyệt đối trung vị MedAE", "2.62 Tỷ VNĐ", "1.36 Tỷ VNĐ", "GIẢM -48.2% (50% nhà lệch dưới 1.36 tỷ)"],
        ["Sai số phần trăm tuyệt đối trung vị MdAPE", "37.28%", "20.47%", "CẢI THIỆN -45.1% (Sai số thực tế chỉ ~20%)"]
    ]
    
    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.name = "Arial"
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER
        
    for r_idx, row_vals in enumerate(data):
        for c_idx, val in enumerate(row_vals):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            if r_idx % 2 == 0:
                cell.fill.fore_color.rgb = COLOR_WHITE
            else:
                cell.fill.fore_color.rgb = COLOR_BG_CARD
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_TEXT_DARK
            if c_idx in [1, 2]:
                p.alignment = PP_ALIGN.RIGHT
            elif c_idx == 3:
                p.font.bold = True
                p.font.color.rgb = COLOR_BLUE

    # ==========================================================================
    # SLIDE 11: TẦM QUAN TRỌNG ĐẶC TRƯNG & CHẨN ĐOÁN PHẦN DƯ
    # ==========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide11, "10. Tầm Quan Trọng Đặc Trưng & Chẩn Đoán Sai Số Mô Hình")
    create_slide_footer(slide11, 11)
    
    img_fi = BASE_DIR / "docs/images/05_feature_importance.png"
    img_res = BASE_DIR / "docs/images/06_residual_analysis.png"
    
    if img_fi.exists():
        slide11.shapes.add_picture(str(img_fi), Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    if img_res.exists():
        slide11.shapes.add_picture(str(img_res), Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))

    # ==========================================================================
    # SLIDE 12: HIỆU NĂNG XỬ LÝ & TỐI ƯU HÓA LƯU TRỮ
    # ==========================================================================
    slide12 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide12, "11. Hiệu Năng Tính Toán Song Song & Tối Ưu Hóa Lưu Trữ")
    create_slide_footer(slide12, 12)
    
    img_perf = BASE_DIR / "docs/images/07_pipeline_performance_storage.png"
    if img_perf.exists():
        slide12.shapes.add_picture(str(img_perf), Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.2))
        
    c_prf = add_card(slide12, Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.2))
    tf_prf = c_prf.text_frame
    tf_prf.word_wrap = True
    
    p_prft = tf_prf.paragraphs[0]
    p_prft.text = "THÔNG SỐ HIỆU NĂNG & DUNG LƯỢNG:"
    p_prft.font.name = "Arial"
    p_prft.font.size = Pt(13)
    p_prft.font.bold = True
    p_prft.font.color.rgb = COLOR_NAVY
    p_prft.space_after = Pt(10)
    
    add_bullet_point(tf_prf, "Tổng thời gian pipeline", "451.4 giây (~7.52 phút) cho 350,075 dòng thô.", font_size=11, space_after=6)
    add_bullet_point(tf_prf, "Thông lượng xử lý PySpark", "Ingestion: 10,002 dòng/s | Silver: 6,956 dòng/s | Gold: 4,010 dòng/s | Loading: 1,038 dòng/s.", font_size=11, space_after=6)
    add_bullet_point(tf_prf, "Nén Parquet Snappy", "Giảm từ 217 MB tệp thô chưa nén xuống 153.9 MB Tầng Đồng và 128.2 MB Tầng Vàng - Tiết kiệm 29.1% dung lượng.", font_size=11, space_after=6)
    add_bullet_point(tf_prf, "CSDL Phục Vụ SQLite", "Tối ưu hóa chỉ còn 17.4 MB, tích hợp 4 chỉ mục B-Tree, tốc độ truy vấn phục vụ Web dưới 50ms.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 13: KIỂM THỬ TỰ ĐỘNG & HƯỚNG DẪN CHẠY DỄ DÀNG
    # ==========================================================================
    slide13 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide13, "12. Tự Động Hóa Kiểm Thử & Hướng Dẫn Vận Hành Dễ Dàng")
    create_slide_footer(slide13, 13)
    
    c_tst = add_card(slide13, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tf_tst = c_tst.text_frame
    tf_tst.word_wrap = True
    p_tt = tf_tst.paragraphs[0]
    p_tt.text = "BỘ KIỂM THỬ TỰ ĐỘNG (10/10 BÀI KIỂM THỬ ĐẠT YÊU CẦU):"
    p_tt.font.name = "Arial"
    p_tt.font.size = Pt(12)
    p_tt.font.bold = True
    p_tt.font.color.rgb = COLOR_GREEN
    p_tt.space_after = Pt(10)
    
    tests = [
        "1. test_directories_exist (Kiểm tra cấu trúc thư mục chuẩn)",
        "2. test_bronze_parquet (350,075 dòng, 3 cột kiểm toán)",
        "3. test_silver_parquet (307,457 dòng, sạch null và âm)",
        "4. test_gold_parquet (300,295 dòng, cờ đặc trưng và log)",
        "5. test_data_quality_report (Kiểm toán báo cáo chất lượng)",
        "6. test_storage_database (Khớp 100%, 4 chỉ mục B-Tree)",
        "7. test_three_way_split_protocol (Tỷ lệ 70/15/15, R² >= 0.80)",
        "8. test_train_serving_consistency (Đồng nhất quy trình)",
        "9. test_evaluation_diagnostics (Biểu đồ chẩn đoán mô hình)",
        "10. test_pipeline_summary_metrics (7 mục số liệu và 7 biểu đồ)"
    ]
    for t in tests:
        p = tf_tst.add_paragraph()
        p.text = f"✔ {t}"
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(4)
        
    c_exe = add_card(slide13, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    tf_exe = c_exe.text_frame
    tf_exe.word_wrap = True
    p_exet = tf_exe.paragraphs[0]
    p_exet.text = "CÁC BƯỚC VẬN HÀNH DỰ ÁN DỄ DÀNG:"
    p_exet.font.name = "Arial"
    p_exet.font.size = Pt(12.5)
    p_exet.font.bold = True
    p_exet.font.color.rgb = COLOR_NAVY
    p_exet.space_after = Pt(10)
    
    add_bullet_point(tf_exe, "Menu tương tác trung tâm (run.bat)", "Nhấp đúp run.bat trên Windows, chọn phím số từ [1] đến [9] để chạy ứng dụng hoặc pipeline.", font_size=11, space_after=6)
    add_bullet_point(tf_exe, "Chạy toàn bộ pipeline (chay_pipeline.bat)", "python run_pipeline.py all (hoặc make all): Tự động nạp, ETL, nạp DB và huấn luyện mô hình.", font_size=11, space_after=6)
    add_bullet_point(tf_exe, "Khởi chạy Web Streamlit (chay_app.bat)", "streamlit run src/serving/app.py: Mở ngay giao diện trực quan tại http://localhost:8501.", font_size=11, space_after=6)
    add_bullet_point(tf_exe, "Chạy bộ kiểm thử tự động", "pytest tests/test_pipelines.py -v (10/10 ca kiểm thử pass trong 4.73 giây).", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 14: DEMO GIAO DIỆN STREAMLIT 4 PHÂN HỆ
    # ==========================================================================
    slide14 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide14, "13. Giao Diện Ứng Dụng Web Streamlit 4 Phân Hệ")
    create_slide_footer(slide14, 14)
    
    tabs = [
        ("TAB 1: KIẾN TRÚC HỒ DỮ LIỆU", "Trực quan hóa sơ đồ 6 tầng, quy mô 3.5 triệu dòng trên 10 phân mảnh, lưu lượng và các thuộc tính qua từng tầng."),
        ("TAB 2: CHẤT LƯỢNG & BIẾN ĐỔI", "Biểu đồ phễu lưu lượng 2 panel, tỷ lệ khuyết thiếu phân 3 nhóm màu, bảng 5 số thống kê TRƯỚC và SAU khi lọc ngoại lệ."),
        ("TAB 3: PHÂN TÍCH THỊ TRƯỜNG", "Bản đồ giá trung vị theo tỉnh thành, phân tích loại hình bất động sản, đơn giá theo phòng ngủ và ma trận tương quan."),
        ("TAB 4: HIỆU NĂNG & ĐỊNH GIÁ", "Bảng điều khiển giám sát quy trình, hiệu quả nén Parquet Snappy, biểu mẫu định giá nhà tự động bằng LightGBM theo thời gian thực.")
    ]
    for i, (tab_title, tab_desc) in enumerate(tabs):
        r_i = i // 2
        c_i = i % 2
        t_left = Inches(0.8 + c_i * 6.0)
        t_top = Inches(1.5 + r_i * 2.6)
        card = add_card(slide14, t_left, t_top, Inches(5.7), Inches(2.3))
        tf = card.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = tab_title
        p.font.name = "Arial"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_NAVY
        p.space_after = Pt(8)
        
        p_d = tf.add_paragraph()
        p_d.text = tab_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(11.5)
        p_d.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 15: KẾT LUẬN, GIỚI HẠN & HƯỚNG MỞ RỘNG
    # ==========================================================================
    slide15 = prs.slides.add_slide(blank_layout)
    create_slide_header(slide15, "14. Kết Luận, Giới Hạn Khách Quan & Hướng Phát Triển")
    create_slide_footer(slide15, 15)
    
    c_concl = add_card(slide15, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    tf_c = c_concl.text_frame
    tf_c.word_wrap = True
    p_ct = tf_c.paragraphs[0]
    p_ct.text = "KẾT QUẢ ĐẠT ĐƯỢC:"
    p_ct.font.name = "Arial"
    p_ct.font.size = Pt(13)
    p_ct.font.bold = True
    p_ct.font.color.rgb = COLOR_GREEN
    p_ct.space_after = Pt(10)
    
    add_bullet_point(tf_c, "Hoàn thiện quy trình 6 tầng", "Tuân thủ chuẩn mực Hồ dữ liệu Medallion, xử lý phân tán PySpark.", font_size=11, space_after=6)
    add_bullet_point(tf_c, "Kiểm soát chất lượng khoa học", "Khử 29.7k trùng lặp, lọc 7.1k ngoại lệ, giảm phương sai giá 77 lần mà bảo toàn trung vị.", font_size=11, space_after=6)
    add_bullet_point(tf_c, "Mô hình LightGBM tối ưu", "R² = 0.8537, MdAPE = 20.47%, vượt trội hoàn toàn so với mô hình cơ sở Ridge.", font_size=11, space_after=6)
    add_bullet_point(tf_c, "Độ tin cậy & tự động hóa cao", "10/10 ca kiểm thử đạt yêu cầu, đóng gói kịch bản tự động trên Windows và ứng dụng Web Streamlit.", font_size=11, space_after=6)
    
    c_lim = add_card(slide15, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    tf_l = c_lim.text_frame
    tf_l.word_wrap = True
    p_lt = tf_l.paragraphs[0]
    p_lt.text = "GIỚI HẠN KHÁCH QUAN & HƯỚNG MỞ RỘNG:"
    p_lt.font.name = "Arial"
    p_lt.font.size = Pt(13)
    p_lt.font.bold = True
    p_lt.font.color.rgb = COLOR_ORANGE
    p_lt.space_after = Pt(10)
    
    add_bullet_point(tf_l, "Giới hạn 1 - Phân mảnh thực nghiệm", "Thực nghiệm trên 1 phân mảnh (350k dòng) do giới hạn máy trạm cá nhân; mở rộng 3.5 triệu dòng cần cụm máy chủ Spark phân tán.", font_size=11, space_after=6)
    add_bullet_point(tf_l, "Giới hạn 2 - Bản chất giá rao bán", "Giá rao bán phản ánh kỳ vọng người bán, thường cao hơn 5-15% so với giá giao dịch thực tế tại phòng công chứng.", font_size=11, space_after=6)
    add_bullet_point(tf_l, "Giới hạn 3 - Tọa độ không gian", "Dữ liệu thiếu tọa độ GPS chính xác từng số nhà để tính khoảng cách đến trường học/bệnh viện.", font_size=11, space_after=6)
    add_bullet_point(tf_l, "Lộ trình tương lai", "Mở rộng cụm phân tán Spark trên Cloud, tích hợp dịch vụ Geocoding API và mô hình đồ thị tri thức GNN.", font_size=11, space_after=6)

    # ==========================================================================
    # SLIDE 16: TRANG KẾT THÚC / Q&A
    # ==========================================================================
    slide16 = prs.slides.add_slide(blank_layout)
    bg16 = slide16.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg16.fill.solid()
    bg16.fill.fore_color.rgb = COLOR_NAVY
    bg16.line.fill.background()
    
    q_box = slide16.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.3), Inches(4.0))
    tf16 = q_box.text_frame
    tf16.word_wrap = True
    
    pq1 = tf16.paragraphs[0]
    pq1.text = "TRÂN TRỌNG CẢM ƠN QUÝ THẦY CÔ VÀ HỘI ĐỒNG!"
    pq1.font.name = "Arial"
    pq1.font.size = Pt(28)
    pq1.font.bold = True
    pq1.font.color.rgb = COLOR_ORANGE
    pq1.alignment = PP_ALIGN.CENTER
    pq1.space_after = Pt(24)
    
    pq2 = tf16.add_paragraph()
    pq2.text = "KÍNH MỜI QUÝ THẦY CÔ ĐẶT CÂU HỎI VÀ ĐÓNG GÓP Ý KIẾN"
    pq2.font.name = "Arial"
    pq2.font.size = Pt(18)
    pq2.font.bold = True
    pq2.font.color.rgb = COLOR_WHITE
    pq2.alignment = PP_ALIGN.CENTER
    pq2.space_after = Pt(36)
    
    pq3 = tf16.add_paragraph()
    pq3.text = "Sinh viên thực hiện: Phạm Văn Minh  —  Mã sinh viên: 23010350"
    pq3.font.name = "Arial"
    pq3.font.size = Pt(14)
    pq3.font.bold = True
    pq3.font.color.rgb = COLOR_WHITE
    pq3.alignment = PP_ALIGN.CENTER
    pq3.space_after = Pt(6)
    
    pq4 = tf16.add_paragraph()
    pq4.text = "Email: 23010350@st.phenikaa-uni.edu.vn  —  Trường Công nghệ Thông tin, Đại học Phenikaa"
    pq4.font.name = "Arial"
    pq4.font.size = Pt(13)
    pq4.font.color.rgb = COLOR_TEXT_MUTED
    pq4.alignment = PP_ALIGN.CENTER

    output_pptx = BASE_DIR / "docs/Slide_Bao_Ve_Du_An_House_Prediction.pptx"
    prs.save(str(output_pptx))
    print(f"[SUCCESS] Slide PowerPoint da duoc tao thanh cong tai: {output_pptx}")
    print(f"[METRIC] Dung luong file: {output_pptx.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    generate_presentation()
