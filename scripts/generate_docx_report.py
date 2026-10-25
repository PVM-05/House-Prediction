"""
Kịch bản tự động khởi tạo Báo cáo Toàn diện Đồ án / Luận văn Microsoft Word (.docx)
Dự án: Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Bất Động Sản Việt Nam
Chuẩn định dạng:
  - Font: 100% Times New Roman
  - Màu chữ: Màu đen tuyệt đối (RGB: 0, 0, 0)
  - Căn lề: Trái 3cm (1.18 in), Phải 2cm (0.79 in), Trên 2cm (0.79 in), Dưới 2cm (0.79 in)
  - Đầy đủ 13 hình ảnh phân giải cao, 8 chương chuyên sâu, bảng đối chiếu trước/sau, công thức toán học và hướng dẫn chạy.
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def configure_document_styles(doc):
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    rPr = normal_style._element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rFonts.set(qn('w:cs'), 'Times New Roman')
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    rPr.append(rFonts)

def set_run_font(run, font_name="Times New Roman", font_size=12, bold=False, italic=False, color=(0, 0, 0)):
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color)
    rPr = run._r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rFonts.set(qn('w:eastAsia'), font_name)
    rPr.append(rFonts)

def add_styled_p(doc, text="", font_size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=6, line_spacing=1.25):
    p = doc.add_paragraph()
    p.alignment = align
    pPr = p._p.get_or_add_pPr()
    spPr = OxmlElement('w:spacing')
    spPr.set(qn('w:before'), str(int(space_before * 20)))
    spPr.set(qn('w:after'), str(int(space_after * 20)))
    spPr.set(qn('w:line'), str(int(line_spacing * 240)))
    spPr.set(qn('w:lineRule'), 'auto')
    pPr.append(spPr)
    if text:
        run = p.add_run(text)
        set_run_font(run, font_size=font_size, bold=bold, italic=italic)
    return p

def add_h1(doc, text):
    return add_styled_p(doc, text=text, font_size=15, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=14, space_after=6)

def add_h2(doc, text):
    return add_styled_p(doc, text=text, font_size=13.5, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=10, space_after=4)

def add_h3(doc, text):
    return add_styled_p(doc, text=text, font_size=12.5, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=6, space_after=2)

def add_bullet(doc, bold_prefix, normal_text):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pPr = p._p.get_or_add_pPr()
    spPr = OxmlElement('w:spacing')
    spPr.set(qn('w:before'), '0')
    spPr.set(qn('w:after'), '80')
    spPr.set(qn('w:line'), '280')
    spPr.set(qn('w:lineRule'), 'auto')
    pPr.append(spPr)
    
    r1 = p.add_run(bold_prefix)
    set_run_font(r1, font_size=12, bold=True)
    r2 = p.add_run(normal_text)
    set_run_font(r2, font_size=12, bold=False)
    return p

def add_image(doc, image_path, caption_text, width_inches=6.0):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = p_img._p.get_or_add_pPr()
    spPr = OxmlElement('w:spacing')
    spPr.set(qn('w:before'), '120')
    spPr.set(qn('w:after'), '60')
    pPr.append(spPr)
    
    run_img = p_img.add_run()
    set_run_font(run_img, font_size=10)
    run_img.add_picture(str(image_path), width=Inches(width_inches))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr_c = p_cap._p.get_or_add_pPr()
    spPr_c = OxmlElement('w:spacing')
    spPr_c.set(qn('w:before'), '0')
    spPr_c.set(qn('w:after'), '140')
    pPr_c.append(spPr_c)
    
    run_cap = p_cap.add_run(caption_text)
    set_run_font(run_cap, font_size=10.5, bold=False, italic=True)

def style_table(table, col_widths, headers, data_rows, col_alignments=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)
    
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    
    for i, title in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.width = Inches(col_widths[i])
        tcPr = cell._tc.get_or_add_tcPr()
        tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="F3F4F6"/>'))
        tcPr.append(parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="140" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar>'))
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        set_run_font(run, font_size=10.5, bold=True)
        
    for r_idx, row_data in enumerate(data_rows):
        row = table.rows[r_idx + 1]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = Inches(col_widths[c_idx])
            tcPr = cell._tc.get_or_add_tcPr()
            tcPr.append(parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:left w:w="140" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar>'))
            p = cell.paragraphs[0]
            if col_alignments and c_idx < len(col_alignments):
                p.alignment = col_alignments[c_idx]
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            set_run_font(run, font_size=10.5, bold=False)

def add_callout(doc, title, text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.3)
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="F9FAFB"/>'))
    tcPr.append(parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:color="000000"/>'
        f'</w:tcBorders>'
    ))
    tcPr.append(parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="180" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tcMar>'))
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r1 = p.add_run(f"★ {title}: ")
    set_run_font(r1, font_size=11, bold=True)
    r2 = p.add_run(text)
    set_run_font(r2, font_size=11, bold=False)
    
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)

def setup_page_margins_and_footer(doc):
    for section in doc.sections:
        section.top_margin = Inches(0.79)     # 2.0 cm
        section.bottom_margin = Inches(0.79)  # 2.0 cm
        section.left_margin = Inches(1.18)    # 3.0 cm (chuẩn đóng gáy)
        section.right_margin = Inches(0.79)   # 2.0 cm
        
        footer = section.footer
        p_ft = footer.paragraphs[0]
        p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_txt = p_ft.add_run("Báo Cáo Đồ Án - SV: Phạm Văn Minh (MSV: 23010350) - ĐH Phenikaa | ")
        set_run_font(r_txt, font_size=9.5, italic=True)
        r_page = p_ft.add_run("Trang ")
        set_run_font(r_page, font_size=9.5, italic=True)
        
        fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
        instr = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls('w'))
        fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
        fld3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
        r_page._r.append(fld1)
        r_page._r.append(instr)
        r_page._r.append(fld2)
        r_page._r.append(fld3)

def generate_report():
    doc = docx.Document()
    configure_document_styles(doc)
    setup_page_margins_and_footer(doc)
    
    # ==========================================================================
    # TRANG BÌA (COVER PAGE)
    # ==========================================================================
    add_styled_p(doc, "BỘ GIÁO DỤC VÀ ĐÀO TẠO", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=2)
    add_styled_p(doc, "TRƯỜNG ĐẠI HỌC PHENIKAA", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_styled_p(doc, "TRƯỜNG CÔNG NGHỆ THÔNG TIN", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=20)
    
    add_styled_p(doc, "--------------------------------------------------", font_size=12, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=25)
    
    add_styled_p(doc, "BÁO CÁO KHOA HỌC & KỸ THUẬT DỰ ÁN", font_size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=10)
    add_styled_p(doc, "HỌC PHẦN: TÍCH HỢP VÀ PHÂN TÍCH DỮ LIỆU LỚN (BIG DATA ANALYTICS)", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=25)
    
    add_styled_p(doc, "ĐỀ TÀI:", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=6)
    add_styled_p(
        doc,
        "NGHIÊN CỨU XÂY DỰNG HỆ THỐNG LAKEHOUSE ĐA TẦNG (MEDALLION ARCHITECTURE) TÍCH HỢP DỮ LIỆU LỚN VÀ ĐỊNH GIÁ BẤT ĐỘNG SẢN VIỆT NAM BẰNG MÔ HÌNH HỌC MÁY LIGHTGBM",
        font_size=17, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=30
    )
    
    add_styled_p(doc, "--------------------------------------------------", font_size=12, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=30)
    
    meta_rows = [
        ["Học phần / Môn học:", "Tích Hợp và Phân Tích Dữ Liệu Lớn"],
        ["Sinh viên thực hiện:", "Phạm Văn Minh"],
        ["Mã sinh viên (MSV):", "23010350"],
        ["Email sinh viên:", "23010350@st.phenikaa-uni.edu.vn"],
        ["Đơn vị đào tạo:", "Trường Công nghệ Thông tin - Trường Đại học Phenikaa"],
        ["Công nghệ chủ đạo:", "Apache PySpark, Parquet Snappy, PostgreSQL/SQLite, LightGBM, Streamlit"],
        ["Quy mô dữ liệu thực nghiệm:", "350,075 bản ghi thô (Shard 0000), kho nguồn 3,500,744 bản ghi (10 Shards)"],
        ["Thời gian thực hiện:", "Sprint 2 Tuần (Năm 2026)"]
    ]
    meta_table = doc.add_table(rows=len(meta_rows), cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_i, (k, v) in enumerate(meta_rows):
        c0 = meta_table.cell(r_i, 0)
        c1 = meta_table.cell(r_i, 1)
        c0.width = Inches(2.5)
        c1.width = Inches(3.8)
        p0 = c0.paragraphs[0]
        p1 = c1.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r0 = p0.add_run(k)
        set_run_font(r0, font_size=11, bold=True)
        r1 = p1.add_run(v)
        set_run_font(r1, font_size=11, bold=False)
        
    add_styled_p(doc, "", font_size=12, space_before=0, space_after=40)
    add_styled_p(doc, "Hà Nội, Năm 2026", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=0)
    
    doc.add_page_break()
    
    # ==========================================================================
    # TÓM TẮT DỰ ÁN & MỤC LỤC
    # ==========================================================================
    add_h1(doc, "TÓM TẮT DỰ ÁN (EXECUTIVE SUMMARY)")
    add_styled_p(
        doc,
        "Dự án tập trung giải quyết bài toán cốt lõi trong kỹ thuật dữ liệu lớn: Tiếp nhận, chuẩn hóa, làm sạch và khai thác kho dữ liệu bất động sản Việt Nam quy mô lớn từ nguồn Hugging Face Hub (tinixai/vietnam-real-estates) gồm 10 phân mảnh (shards) với 3,500,744 bản ghi thô. Trong khuôn khổ sprint 2 tuần, hệ thống đã triển khai thực nghiệm hoàn chỉnh trên phân mảnh Shard 0000 gồm 350,075 dòng thô, thiết kế kiến trúc Medallion Lakehouse 6 tầng (Ingestion -> Bronze -> Silver -> Gold -> Database Serving -> Streamlit/ML Serving)."
    )
    add_styled_p(
        doc,
        "Các thành tựu định lượng nổi bật đạt được trong dự án bao gồm:"
    )
    add_bullet(doc, "Xử lý và kiểm soát chất lượng dữ liệu: ", "Khử chính xác 29,686 tin đăng trùng lặp; loại bỏ 12,932 tin thiếu giá/diện tích; lọc 7,162 bản ghi ngoại lệ cực đoan (giá ảo lên tới 881,020 tỷ đồng và diện tích 24 triệu m²). Giữ lại 300,295 bản ghi sạch tại Tầng Vàng (Gold Layer) với tỷ lệ toàn vẹn 85.78%.")
    add_bullet(doc, "Triệt tiêu nhiễu và bảo toàn trung vị: ", "Giảm độ lệch chuẩn của giá 77 lần (từ 2,006.6 tỷ xuống 25.98 tỷ) và diện tích 208 lần (từ 51,332 m² xuống 246.5 m²). Giá trị trung vị được bảo toàn nguyên vẹn tuyệt đối (7.2 tỷ tại Silver và 7.3 tỷ tại Gold, diện tích 80.0 m²), chứng minh thuật toán lọc kháng nhiễu chuẩn mực.")
    add_bullet(doc, "Mô hình học máy tối ưu không rò rỉ: ", "Tuân thủ giao thức phân chia 3 tập nghiêm ngặt (Train 70% / Val 15% / Test 15%). Mô hình LightGBM Regressor đạt hệ số xác định R² = 0.8537, sai số tỷ lệ trung vị MdAPE = 20.47%, vượt trội hoàn toàn mô hình cơ sở Ridge Regression (R² = 0.6266, MdAPE = 37.28%).")
    add_bullet(doc, "Hiệu năng xử lý và nén lưu trữ cao: ", "Xử lý phân tán bằng PySpark đạt thông lượng trung bình 775.5 dòng/giây; định dạng cột Parquet Snappy tiết kiệm 29.09% dung lượng so với CSV thô; CSDL Serving SQLite được tối ưu hóa chỉ còn 17.4 MB với 4 chỉ mục B-Tree.")
    add_bullet(doc, "Độ tin cậy và tự động hóa toàn diện: ", "10/10 ca kiểm thử tự động Pytest vượt qua 100% trong 4.73 giây. Hệ thống được đóng gói tự động hóa 1-click qua các tệp Makefile, run_pipeline.py và batch scripts trên Windows.")
    
    add_styled_p(doc, "", font_size=12, space_before=10, space_after=10)
    add_h2(doc, "MỤC LỤC BÁO CÁO")
    add_styled_p(doc, "CHƯƠNG 1: TỔNG QUAN VÀ BỐI CẢNH DỰ ÁN", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG VÀ LUỒNG DỮ LIỆU ĐA TẦNG (MEDALLION ARCHITECTURE)", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 3: CHI TIẾT CÁC THUẬT TOÁN TIỀN XỬ LÝ, LÀM SẠCH VÀ BIẾN ĐỔI DỮ LIỆU", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 4: PHÂN TÍCH KHÁM PHÁ THỊ TRƯỜNG DỮ LIỆU LỚN (BIG DATA EDA)", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 5: THUẬT TOÁN HỌC MÁY (MACHINE LEARNING) & ĐÁNH GIÁ CHẨN ĐOÁN MÔ HÌNH", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 6: HIỆU NĂNG HỆ THỐNG, TỐI ƯU HÓA LƯU TRỮ VÀ KIỂM THỬ TỰ ĐỘNG", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 7: HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ CÁC BƯỚC CHẠY TOÀN BỘ DỰ ÁN", font_size=11, bold=True)
    add_styled_p(doc, "CHƯƠNG 8: KẾT LUẬN, GIỚI HẠN CỦA HỆ THỐNG VÀ LỘ TRÌNH PHÁT TRIỂN", font_size=11, bold=True)
    add_styled_p(doc, "TÀI LIỆU THAM KHẢO", font_size=11, bold=True)
    
    doc.add_page_break()
    
    # ==========================================================================
    # CHƯƠNG 1: TỔNG QUAN & BỐI CẢNH DỰ ÁN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 1: TỔNG QUAN VÀ BỐI CẢNH DỰ ÁN")
    
    add_h2(doc, "1.1. Bối cảnh thị trường và thách thức dữ liệu lớn bất động sản")
    add_styled_p(
        doc,
        "Thị trường bất động sản Việt Nam là một trong những thị trường sôi động và có giá trị vốn hóa lớn nhất nền kinh tế. Tuy nhiên, tính minh bạch thông tin thị trường còn nhiều hạn chế. Dữ liệu tin rao bán chủ yếu tồn tại ở dạng phi cấu trúc hoặc bán cấu trúc trên hàng trăm cổng thông tin rao vặt, mạng xã hội và diễn đàn môi giới."
    )
    add_styled_p(
        doc,
        "Khi thu thập và tích hợp dữ liệu bất động sản quy mô hàng triệu bản ghi, hệ thống kỹ thuật phải đối mặt với 4 thách thức dữ liệu lớn đặc thù:"
    )
    add_bullet(doc, "Dữ liệu trùng lặp cực lớn (Duplicate Listings): ", "Một căn nhà thường được nhiều môi giới khác nhau cùng đăng tải lên mạng với tiêu đề biến tấu, tạo ra hiện tượng trùng lặp ảo làm sai lệch nghiêm trọng các phân tích thống kê.")
    add_bullet(doc, "Nhiễu loạn giá trị và đơn vị phi chuẩn: ", "Giá rao được ghi bằng nhiều định dạng phức tạp: '3.5 tỷ', '850 triệu', '45 triệu/m²', 'thương lượng', 'thỏa thuận', sử dụng lẫn lộn dấu chấm và phẩy ngăn cách hàng thập phân theo thói quen địa phương.")
    add_bullet(doc, "Ngoại lệ cực đoan và tin rác (Extreme Outliers & Spam): ", "Tồn tại các tin đăng sai sót bàn phím hoặc cố tình thổi giá với mức giá vô lý lên tới 881,020 tỷ đồng hoặc diện tích đất ảo 24 triệu m², làm sai lệch toàn bộ hàm phân phối chuẩn.")
    add_bullet(doc, "Tỷ lệ khuyết thiếu thông tin cao (High Missingness): ", "Các thuộc tính quan trọng như tên đường, tên dự án, kích thước mặt tiền, hướng nhà có tỷ lệ khuyết thiếu từ 14% đến hơn 86%.")

    add_h2(doc, "1.2. Mục tiêu nghiên cứu và phạm vi triển khai")
    add_styled_p(
        doc,
        "Mục tiêu cốt lõi của dự án là xây dựng một hệ thống tích hợp và phân tích dữ liệu lớn end-to-end tuân thủ các chuẩn mực công nghiệp hiện đại, bao gồm:"
    )
    add_bullet(doc, "Thiết kế kiến trúc Hồ dữ liệu Medallion Lakehouse 6 tầng: ", "Tách biệt rõ ràng các tầng dữ liệu từ Thô (Bronze), Làm sạch (Silver), Trích xuất đặc trưng (Gold) đến Cơ sở dữ liệu phục vụ (PostgreSQL/SQLite) và Giao diện tương tác.")
    add_bullet(doc, "Xử lý phân tán với Apache PySpark: ", "Ứng dụng động cơ tính toán phân tán PySpark để thực hiện các thao tác biến đổi dữ liệu lớn, khử trùng lặp và tính toán đặc trưng song song.")
    add_bullet(doc, "Mô hình hóa định giá thông minh: ", "Huấn luyện mô hình Gradient Boosting (LightGBM) dự báo log(giá), so sánh đối chuẩn với mô hình cơ sở Ridge Regression, cam kết không rò rỉ dữ liệu (No Data Leakage).")
    add_bullet(doc, "Trực quan hóa và phục vụ người dùng: ", "Xây dựng bảng điều khiển Streamlit tương tác 4 phân hệ và hệ thống kiểm thử tự động Pytest bảo đảm chất lượng phần mềm.")

    add_h2(doc, "1.3. Quy mô kho dữ liệu thực nghiệm")
    add_styled_p(
        doc,
        "Nguồn dữ liệu sử dụng trong đề tài là tập dữ liệu mở 'tinixai/vietnam-real-estates' lưu trữ trên nền tảng Hugging Face Hub. Toàn bộ kho nguồn bao gồm 10 phân mảnh (shards) với tổng quy mô 3,500,744 bản ghi. Trong giới hạn tài nguyên tính toán của máy trạm cá nhân thuộc sprint 2 tuần, dự án triển khai quy trình xử lý đầy đủ trên phân mảnh Shard 0000 gồm 350,075 bản ghi thô với 22 thuộc tính nguyên bản."
    )
    
    # ==========================================================================
    # CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG VÀ LUỒNG DỮ LIỆU ĐA TẦNG
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG VÀ LUỒNG DỮ LIỆU ĐA TẦNG (MEDALLION ARCHITECTURE)")
    
    add_h2(doc, "2.1. Tổng quan kiến trúc Medallion Lakehouse 6 tầng")
    add_styled_p(
        doc,
        "Hệ thống được thiết kế theo kiến trúc Medallion Lakehouse chuẩn công nghiệp. Kiến trúc này phân chia dữ liệu thành các tầng kế tiếp nhau với chất lượng tăng dần, kết hợp tính linh hoạt lưu trữ của Data Lake và độ tin cậy giao dịch ACID của Data Warehouse. Toàn bộ hệ thống vận hành qua 6 tầng mạch lạc:"
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/00_architecture_flowchart.png",
        "Hình 2.1: Sơ đồ kiến trúc và luồng dữ liệu 6 tầng Medallion Lakehouse (Hugging Face -> Bronze -> Silver -> Gold -> Database -> Streamlit/ML)",
        width_inches=6.2
    )
    
    add_h2(doc, "2.2. Phân tích chi tiết các tầng trong luồng dữ liệu")
    add_bullet(doc, "Tầng 1: Nguồn Dữ Liệu & Thu Nạp Thô (Data Ingestion): ", "Dữ liệu được nạp bất đồng bộ từ Hugging Face Hub (tinixai/vietnam-real-estates) thông qua thư viện Polars/Arrow tốc độ cao. Tại tầng này, hệ thống gắn kèm các trường siêu dữ liệu kiểm toán (Lineage Metadata) gồm ingested_at, batch_id, source_file nhằm bảo đảm khả năng truy vết nguồn gốc 100%.")
    add_bullet(doc, "Tầng 2: Tầng Đồng (Bronze Layer - Parquet Raw): ", "Lưu trữ dữ liệu thô nguyên vẹn (Immutable Raw Data) ở định dạng Apache Parquet nén Snappy. Quy mô: 350,075 dòng, 22 cột, dung lượng 153.89 MB. Tầng này bảo đảm nguyên tắc 'không bao giờ mất dữ liệu gốc'.")
    add_bullet(doc, "Tầng 3: Tầng Bạc (Silver Layer - Cleaned Data): ", "Dữ liệu sau khi đi qua pipeline Apache PySpark làm sạch, khử trùng lặp đa thuộc tính, chuẩn hóa kiểu dữ liệu số, phân tích chuỗi giá và diện tích. Quy mô: 307,457 dòng, 23 cột, dung lượng 130.04 MB.")
    add_bullet(doc, "Tầng 4: Tầng Vàng (Gold Layer - Curated Features): ", "Dữ liệu sẵn sàng cho phân tích nghiệp vụ và học máy. PySpark thực hiện lọc ngoại lệ thống kê kháng nhiễu (Domain + IQR), trích xuất đặc trưng NLP (sổ đỏ, mặt tiền, nội thất) và biến đổi chuẩn hóa logarit. Quy mô: 300,295 dòng, 33 cột, dung lượng 128.20 MB.")
    add_bullet(doc, "Tầng 5: Tầng Phục Vụ Cơ Sở Dữ Liệu (Serving Storage): ", "Dữ liệu Gold được nạp phân khối (chunk size 10,000) vào PostgreSQL (hỗ trợ SQLite dự phòng), tự động đánh 4 chỉ mục B-Tree (province_clean, district_clean, price_billion, area). Quy mô lưu trữ SQLite chỉ 17.4 MB phục vụ truy vấn dưới 50ms.")
    add_bullet(doc, "Tầng 6: Tầng Phục Vụ Ứng Dụng & Mô Hình Học Máy (Serving Layer): ", "Triển khai mô hình LightGBM Regressor định giá trực tuyến và giao diện Dashboard Streamlit 4 phân hệ tương tác phục vụ người dùng cuối.")

    add_h2(doc, "2.3. Bảng tổng hợp thông số kỹ thuật 6 tầng kiến trúc")
    table_arch_headers = ["Tầng Kiến Trúc", "Công Nghệ / Định Dạng", "Số Bản Ghi", "Số Cột", "Dung Lượng", "Mục Tiêu & Vai Trò"]
    table_arch_data = [
        ["1. Raw Ingestion", "Hugging Face / Polars", "350,075", "19", "N/A", "Thu nạp thô, gán Lineage Metadata"],
        ["2. Tầng Đồng (Bronze)", "Parquet (Snappy)", "350,075", "22", "153.89 MB", "Lưu trữ nguyên trạng bất biến"],
        ["3. Tầng Bạc (Silver)", "Apache PySpark / Parquet", "307,457", "23", "130.04 MB", "Làm sạch, khử trùng, chuẩn hóa số liệu"],
        ["4. Tầng Vàng (Gold)", "Apache PySpark / Parquet", "300,295", "33", "128.20 MB", "Lọc ngoại lệ, trích xuất đặc trưng NLP"],
        ["5. Serving Database", "PostgreSQL / SQLite Indexing", "300,295", "33", "17.40 MB", "Lưu trữ quan hệ, truy vấn dưới 50ms"],
        ["6. ML & Serving UI", "LightGBM & Streamlit", "45,045 (Test)", "33", "N/A", "Định giá trực tuyến & Dashboard 4 Tab"]
    ]
    t_arch = doc.add_table(rows=len(table_arch_data) + 1, cols=6)
    style_table(t_arch, [1.1, 1.2, 0.8, 0.5, 0.9, 1.8], table_arch_headers, table_arch_data, 
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)
    
    # ==========================================================================
    # CHƯƠNG 3: THUẬT TOÁN TIỀN XỬ LÝ, LÀM SẠCH, LỌC NGOẠI LỆ & NLP
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 3: CHI TIẾT CÁC THUẬT TOÁN TIỀN XỬ LÝ, LÀM SẠCH VÀ BIẾN ĐỔI DỮ LIỆU")
    
    add_h2(doc, "3.1. Thuật toán phát hiện và khử trùng lặp (Deduplication Algorithm)")
    add_styled_p(
        doc,
        "Hiện tượng trùng lặp trong dữ liệu tin rao bất động sản xảy ra khi một bất động sản được nhiều người môi giới cùng đăng bán, hoặc một môi giới đăng lặp lại nhiều lần trong tuần. Nếu không khử trùng triệt để, mô hình học máy sẽ bị hiện tượng ghi nhớ mẫu (memorization bias) và rò rỉ dữ liệu giữa tập Train và Test."
    )
    add_styled_p(
        doc,
        "Thuật toán phát hiện trùng lặp được triển khai trên PySpark dựa trên tổ hợp khóa logic đa thuộc tính (Composite Deduplication Key):"
    )
    add_styled_p(
        doc,
        "K_{dedup} = Hash(lower(name) || province_clean || district_clean || ward_clean || price_string || round(area, 1))",
        font_size=11, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER
    )
    add_styled_p(
        doc,
        "Kết quả thực thi thuật toán đã phát hiện và loại bỏ chính xác 29,686 bản ghi trùng lặp (chiếm 8.48% tổng dữ liệu thô)."
    )

    add_h2(doc, "3.2. Thuật toán phân tích cú pháp chuẩn hóa giá và diện tích")
    add_styled_p(
        doc,
        "Cột giá và diện tích trong tin rao gốc tồn tại dưới dạng văn bản tự do với nhiều quy chuẩn không đồng nhất. Thuật toán phân tích cú pháp (Parser) thực hiện nhận diện từ khóa quy đổi về đơn vị chuẩn:"
    )
    add_bullet(doc, "Quy đổi Giá về VNĐ: ", "Nếu chuỗi chứa từ khóa 'tỷ', nhân giá trị số với 1,000,000,000; nếu chứa 'triệu', nhân với 1,000,000; nếu chứa 'triệu/m²', nhân giá trị số với diện tích tương ứng.")
    add_bullet(doc, "Lọc bỏ tin không hợp lệ: ", "Các tin có giá ghi 'thỏa thuận', 'thương lượng', giá trị bằng 0 hoặc âm được đánh dấu không hợp lệ và loại bỏ. Tổng cộng có 12,932 bản ghi thiếu giá hoặc diện tích không thể khôi phục đã được loại bỏ an toàn.")

    add_h2(doc, "3.3. Phễu lưu lượng và tỷ lệ giữ lại qua các tầng (Pipeline Funnel & Retention)")
    add_styled_p(
        doc,
        "Hình 3.1 thể hiện chi tiết phễu lưu lượng dữ liệu (Data Pipeline Funnel) và cơ cấu loại bỏ bản ghi qua từng giai đoạn của kiến trúc Medallion Lakehouse."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/01_pipeline_funnel_retention.png",
        "Hình 3.1: Phễu lưu lượng dữ liệu và tỷ lệ giữ lại qua các tầng (Bronze -> Silver -> Gold) kèm chi tiết nguyên nhân loại bỏ",
        width_inches=6.1
    )
    
    table_funnel_headers = ["Giai Đoạn Xử Lý", "Số Bản Ghi Đầu Vào", "Số Bản Ghi Loại Bỏ", "Số Bản Ghi Giữ Lại", "Tỷ Lệ Giữ Lại Tầng", "Tỷ Lệ Giữ Lại Toàn Bộ"]
    table_funnel_data = [
        ["1. Thu Nạp Bronze", "350,075", "0", "350,075", "100.00%", "100.00%"],
        ["2. Khử Trùng Lặp (Silver)", "350,075", "29,686 (Trùng)", "320,389", "91.52%", "91.52%"],
        ["3. Làm Sạch Giá & S (Silver)", "320,389", "12,932 (Thiếu giá/S)", "307,457", "95.96%", "87.83%"],
        ["4. Lọc Ngoại Lệ (Gold)", "307,457", "7,162 (Ngoại lệ IQR)", "300,295", "97.67%", "85.78%"],
        ["5. Tầng Vàng Hoàn Tất", "300,295", "0", "300,295", "100.00%", "85.78%"]
    ]
    t_funnel = doc.add_table(rows=len(table_funnel_data) + 1, cols=6)
    style_table(t_funnel, [1.4, 1.0, 1.2, 1.0, 0.9, 0.9], table_funnel_headers, table_funnel_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "3.4. Thuật toán kiểm toán chất lượng và xử lý giá trị khuyết thiếu")
    add_styled_p(
        doc,
        "Quy trình kiểm toán chất lượng dữ liệu được thực thi tự động qua tập tin data_quality_report.json, phân tích tỷ lệ khuyết thiếu trên 22 trường dữ liệu thô ban đầu. Hình 3.2 minh họa trực quan sự phân nhóm tỷ lệ khuyết thiếu theo 3 cấp độ cảnh báo màu sắc."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/02_data_quality_missing_analysis.png",
        "Hình 3.2: Phân tích tỷ lệ khuyết thiếu của các thuộc tính (Nhóm sạch <5%, Nhóm vừa 5-50%, Nhóm cao >50%)",
        width_inches=6.0
    )
    
    add_styled_p(
        doc,
        "Chiến lược xử lý khuyết thiếu được phân loại khoa học:"
    )
    add_bullet(doc, "Nhóm thuộc tính sạch (< 5% null): ", "Gồm name (0%), description (0%), province_name (0%), district_name (1.75%). Đây là khung xương nhận diện bất động sản, các bản ghi thiếu quận/huyện được điền bằng 'Không rõ' hoặc suy luận từ tiêu đề.")
    add_bullet(doc, "Nhóm thuộc tính khuyết thiếu vừa (5% - 50% null): ", "Gồm ward_name (14.41%), street_name (40.44%), bedroom_count (24.78%), house_direction (46.80%). Hệ thống điền giá trị logic 'Không rõ' cho phân loại và giá trị trung vị theo quận cho số phòng ngủ.")
    add_bullet(doc, "Nhóm thuộc tính khuyết thiếu cao (> 50% null): ", "Gồm project_name (86.13%), frontage_width (64.21%), road_width (61.54%). Tuyệt đối không xóa các cột này vì chúng mang giá trị kinh tế rất lớn khi có dữ liệu; hệ thống sử dụng thuật toán Imputation riêng biệt và trích xuất cờ chỉ báo nhị phân.")

    add_h2(doc, "3.5. Thuật toán lọc ngoại lệ thống kê kháng nhiễu (Domain & Robust Statistical IQR Filtering)")
    add_styled_p(
        doc,
        "Dữ liệu bất động sản Việt Nam chịu ảnh hưởng nặng nề bởi các tin đăng ngoại lệ cực đoan do lỗi nhập liệu của môi giới. Tại Tầng Bạc, giá nhà tối đa lên tới 881,020 tỷ đồng (gần 35 tỷ USD cho một căn nhà - phi thực tế) và diện tích tối đa lên tới 24,000,000 m² (24 km²)."
    )
    add_styled_p(
        doc,
        "Để làm sạch mà không làm méo mó bản chất thị trường, dự án kết hợp 2 lớp lọc:"
    )
    add_bullet(doc, "Lớp 1 - Miền nghiệp vụ bất động sản Việt Nam (Domain Boundaries): ", "0.1 Tỷ VNĐ <= Giá <= 500 Tỷ VNĐ; 10 m² <= Diện tích <= 5,000 m²; 2 Triệu VNĐ/m² <= Đơn giá <= 1,000 Triệu VNĐ/m².")
    add_bullet(doc, "Lớp 2 - Khoảng liên tứ phân vị (Interquartile Range - IQR): ", "Tính IQR = Q3 - Q1 trên log-scale, loại bỏ các điểm nằm ngoài ngưỡng [Q1 - 1.5 * IQR, Q3 + 1.5 * IQR].")
    
    add_styled_p(
        doc,
        "Thuật toán đã loại bỏ 7,162 bản ghi ngoại lệ (chiếm 2.33% dữ liệu Silver), thu được 300,295 bản ghi sạch tại Tầng Vàng."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/03_distribution_outlier_analysis.png",
        "Hình 3.3: So sánh phân phối và phát hiện ngoại lệ TRƯỚC và SAU khi làm sạch (Boxplot & Histogram của Giá, Diện tích, Đơn giá)",
        width_inches=6.2
    )

    add_styled_p(
        doc,
        "Dưới đây là Bảng đối chiếu số liệu chi tiết minh chứng tác động to lớn của thuật toán lọc ngoại lệ giữa Tầng Bạc (Trước) và Tầng Vàng (Sau):"
    )

    table_stat_headers = ["Thuộc Tính Thống Kê", "Tầng Bạc (Trước Lọc)", "Tầng Vàng (Sau Lọc)", "Mức Độ Cải Thiện / Nhận Xét Nghiệp Vụ"]
    table_stat_data = [
        ["Số lượng bản ghi", "307,457 dòng", "300,295 dòng", "Loại bỏ an toàn 7,162 dòng ngoại lệ (2.33%)"],
        ["Giá: Min (Tỷ VNĐ)", "0.0003 Tỷ (300k)", "0.11 Tỷ (110 triệu)", "Triệt tiêu các tin đăng giá rác dưới 100 triệu"],
        ["Giá: Phân vị Q1", "3.80 Tỷ VNĐ", "3.90 Tỷ VNĐ", "Phân vị dưới ổn định, phản ánh đúng thị trường"],
        ["Giá: Trung vị (Median)", "7.20 Tỷ VNĐ", "7.30 Tỷ VNĐ", "TRUNG VỊ BẢO TOÀN NGUYÊN VẸN (Không bị méo mó)"],
        ["Giá: Trung bình (Mean)", "25.40 Tỷ VNĐ", "14.57 Tỷ VNĐ", "Giảm 42.6% do triệt tiêu các tin ảo hàng nghìn tỷ"],
        ["Giá: Phân vị Q3", "14.90 Tỷ VNĐ", "14.80 Tỷ VNĐ", "Phân vị trên đồng nhất, phân khúc phổ biến < 15 tỷ"],
        ["Giá: Max (Tỷ VNĐ)", "881,020.0 Tỷ VNĐ", "500.0 Tỷ VNĐ", "Triệt tiêu hoàn toàn tin đăng lỗi bàn phím"],
        ["Giá: Độ lệch chuẩn (Std)", "2,006.63 Tỷ VNĐ", "25.98 Tỷ VNĐ", "GIẢM 77 LẦN! Biến thiên nhiễu được kiểm soát"],
        ["Giá: Độ lệch (Skewness)", "365.74", "6.70 (log: 0.24)", "Độ lệch phải giảm mạnh, log_price đạt chuẩn Gauss"],
        ["Giá: Độ nhọn (Kurtosis)", "146,454.50", "67.17 (log: 0.43)", "Triệt tiêu hiện tượng đuôi cực dày (Fat-tail)"],
        ["Diện tích: Min (m²)", "3.16 m²", "10.00 m²", "Loại bỏ diện tích không tưởng dưới 10 m²"],
        ["Diện tích: Trung vị (Median)", "80.00 m²", "80.00 m²", "GIỮ NGUYÊN VẸN 100% TRUNG VỊ DIỆN TÍCH THỊ TRƯỜNG"],
        ["Diện tích: Trung bình (Mean)", "393.99 m²", "130.93 m²", "Đưa trung bình về sát thực tế nhà ở đô thị"],
        ["Diện tích: Max (m²)", "24,000,000.0 m²", "5,000.0 m²", "Loại bỏ diện tích ảo ngang quy mô một phường"],
        ["Diện tích: Độ lệch chuẩn (Std)", "51,332.22 m²", "246.52 m²", "GIẢM 208 LẦN! Phương sai diện tích ổn định"],
        ["Đơn giá: Trung bình (Triệu/m²)", "251.81 Triệu/m²", "136.13 Triệu/m²", "Đơn giá trung bình thực tế, hợp lý"],
        ["Đơn giá: Độ lệch chuẩn (Std)", "48,836.72 Triệu/m²", "126.75 Triệu/m²", "GIẢM 385 LẦN! Kiểm soát hoàn toàn đơn giá ảo"]
    ]
    t_stat = doc.add_table(rows=len(table_stat_data) + 1, cols=4)
    style_table(t_stat, [1.7, 1.4, 1.4, 1.8], table_stat_headers, table_stat_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "3.6. Kỹ thuật trích xuất đặc trưng văn bản bằng NLP (Feature Engineering)")
    add_styled_p(
        doc,
        "Tiêu đề (name) và mô tả (description) chứa đựng nhiều thông tin pháp lý và vị trí có giá trị định giá cao mà dữ liệu dạng bảng chưa khai thác. Dự án xây dựng bộ trích xuất biểu thức chính quy (Regex NLP) trên PySpark:"
    )
    add_bullet(doc, "Cờ pháp lý sổ đỏ/hồng (has_so_do): ", "Nhận diện các từ khóa: 'sổ đỏ', 'sổ hồng', 'chính chủ', 'pháp lý chuẩn', 'sẵn sàng giao dịch'. Nhà có sổ đỏ có giá trị giao dịch cao hơn đáng kể.")
    add_bullet(doc, "Cờ nhà mặt phố/mặt tiền (is_frontage): ", "Nhận diện: 'mặt phố', 'mặt tiền', 'kinh doanh', 'vỉa hè', 'phố lớn'. Đây là đặc trưng đẩy đơn giá/m² lên gấp 2-3 lần so với nhà trong ngõ.")
    add_bullet(doc, "Cờ ngõ hẻm (is_alley): ", "Nhận diện: 'ngõ', 'hẻm', 'ba gác', 'xe máy tránh', 'ngõ thông'.")
    add_bullet(doc, "Cờ nội thất (has_furniture): ", "Nhận diện: 'full nội thất', 'đầy đủ đồ', 'nội thất cao cấp', 'chỉ việc xách vali về ở'.")
    add_bullet(doc, "Cờ ô tô đỗ cửa (has_car_access): ", "Nhận diện: 'ô tô đỗ cửa', 'ô tô vào nhà', 'gara ô tô', 'đường ô tô tránh'.")
    add_bullet(doc, "Biến đổi logarit chuẩn hóa: ", "Tạo log_price = log(1 + price_vnd) và log_area = log(1 + area). Kéo phân phối giá từ độ lệch Skewness = 6.70 về 0.24 (gần như đối xứng hoàn hảo quanh trung vị), giúp các giải thuật học máy hội tụ nhanh và tối ưu hóa sai số tuyệt đối.")

    # ==========================================================================
    # CHƯƠNG 4: PHÂN TÍCH KHÁM PHÁ THỊ TRƯỜNG DỮ LIỆU LỚN (BIG DATA EDA)
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 4: PHÂN TÍCH KHÁM PHÁ THỊ TRƯỜNG DỮ LIỆU LỚN (BIG DATA EDA)")
    
    add_h2(doc, "4.1. Toàn cảnh phân bố thị trường bất động sản Việt Nam")
    add_styled_p(
        doc,
        "Trên tập dữ liệu 300,295 bất động sản Tầng Vàng, hệ thống đã tiến hành phân tích khám phá quy mô lớn về cấu trúc địa lý, phân khúc loại hình và mối quan hệ giá - diện tích."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/04_market_distribution.png",
        "Hình 4.1: Toàn cảnh phân bố thị trường bất động sản Việt Nam (Giá trung vị theo tỉnh thành, cơ cấu loại hình BĐS, phân bố đơn giá theo số phòng ngủ)",
        width_inches=6.2
    )
    
    add_h2(doc, "4.2. Phân phối giá và hiệu quả biến đổi logarit")
    add_styled_p(
        doc,
        "Hình 4.2 minh chứng rõ nét sự phân bố lệch phải cực đoan của giá bán bất động sản thực tế và sự chuyển đổi kỳ diệu của biến đổi logarit sang phân phối chuẩn Gauss."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/eda_price_distribution.png",
        "Hình 4.2: Phân phối giá gốc lệch phải cực đoan và phân phối chuẩn hóa sau biến đổi logarit",
        width_inches=5.8
    )

    add_h2(doc, "4.3. Giá trung vị theo loại hình bất động sản")
    add_styled_p(
        doc,
        "Thị trường phân hóa rõ rệt theo loại hình. Nhà mặt phố và biệt thự liền kề nắm giữ vị trí dẫn đầu về giá trị trung vị, tiếp theo là nhà riêng và căn hộ chung cư."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/eda_property_types.png",
        "Hình 4.3: Giá trung vị theo các loại hình bất động sản phổ biến",
        width_inches=5.6
    )

    add_h2(doc, "4.4. So sánh giá bất động sản giữa các tỉnh/thành phố trọng điểm")
    add_styled_p(
        doc,
        "Hình 4.4 thể hiện giá trung vị của 15 tỉnh/thành có lượng tin đăng lớn nhất cả nước. Hà Nội và TP. Hồ Chí Minh tiếp tục là hai đầu tàu thị trường với mức giá trung vị vượt trội."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/eda_province_prices.png",
        "Hình 4.4: So sánh giá bất động sản trung vị tại 15 tỉnh/thành phố hàng đầu Việt Nam",
        width_inches=5.8
    )

    table_prov_headers = ["Tỉnh / Thành Phố", "Số Lượng Tin Đăng", "Giá Trung Vị (Tỷ VNĐ)", "Giá Trung Bình (Tỷ VNĐ)", "Đơn Giá Trung Vị (Tr/m²)", "Đặc Trưng Thị Trường"]
    table_prov_data = [
        ["Hà Nội", "104,821 tin", "8.90 Tỷ VNĐ", "16.82 Tỷ VNĐ", "148.5 Triệu/m²", "Thanh khoản cao, nhà ngõ và mặt phố chiếm ưu thế"],
        ["TP. Hồ Chí Minh", "105,744 tin", "8.50 Tỷ VNĐ", "17.41 Tỷ VNĐ", "135.2 Triệu/m²", "Phân hóa mạnh giữa trung tâm và các quận vệ tinh"],
        ["Đà Nẵng", "17,192 tin", "7.57 Tỷ VNĐ", "12.35 Tỷ VNĐ", "88.6 Triệu/m²", "Thị trường nghỉ dưỡng và đất nền ven biển"],
        ["Bình Dương", "13,184 tin", "2.91 Tỷ VNĐ", "4.85 Tỷ VNĐ", "35.4 Triệu/m²", "Thủ phủ công nghiệp, phân khúc nhà ở công nhân/chuyên gia"],
        ["Khánh Hòa", "9,187 tin", "4.50 Tỷ VNĐ", "8.12 Tỷ VNĐ", "52.8 Triệu/m²", "Bất động sản du lịch Nha Trang và vùng ven"],
        ["Hải Phòng", "8,245 tin", "4.20 Tỷ VNĐ", "7.64 Tỷ VNĐ", "58.1 Triệu/m²", "Khu đô thị cảng biển, dự án ven sông"],
        ["Các tỉnh khác", "41,922 tin", "2.10 Tỷ VNĐ", "3.95 Tỷ VNĐ", "24.5 Triệu/m²", "Đất nền và nhà ở nông thôn, đô thị loại 2"]
    ]
    t_prov = doc.add_table(rows=len(table_prov_data) + 1, cols=6)
    style_table(t_prov, [1.2, 1.0, 1.1, 1.1, 1.1, 1.8], table_prov_headers, table_prov_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "4.5. Ma trận tương quan đa biến giữa các thuộc tính (Correlation Matrix)")
    add_styled_p(
        doc,
        "Hình 4.5 thể hiện ma trận hệ số tương quan Pearson giữa các đặc trưng số học chính sau khi tiền xử lý. Biến log_price có tương quan thuận mạnh nhất với log_area (r = 0.68), tiếp theo là chiều rộng mặt tiền frontage_width (r = 0.42) và số phòng ngủ bedroom_count (r = 0.38)."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/eda_correlation_matrix.png",
        "Hình 4.5: Ma trận tương quan đa biến giữa các thuộc tính đặc trưng số",
        width_inches=5.8
    )

    # ==========================================================================
    # CHƯƠNG 5: THUẬT TOÁN HỌC MÁY & ĐÁNH GIÁ CHẨN ĐOÁN MÔ HÌNH
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 5: THUẬT TOÁN HỌC MÁY (MACHINE LEARNING) & ĐÁNH GIÁ CHẨN ĐOÁN MÔ HÌNH")
    
    add_h2(doc, "5.1. Giao thức phân chia dữ liệu chống rò rỉ (Strict Three-Way Split Protocol)")
    add_styled_p(
        doc,
        "Một trong những lỗi nghiêm trọng nhất trong các đồ án khoa học dữ liệu là rò rỉ dữ liệu (Data Leakage) giữa tập huấn luyện và kiểm thử. Dự án thiết lập giao thức phân chia 3 tập độc lập nghiêm ngặt với tỷ lệ 70% / 15% / 15% (Random seed = 42):"
    )
    add_bullet(doc, "Tập Huấn luyện (Train Set - 70%): ", "Gồm 210,206 bản ghi. Toàn bộ quá trình Target Encoding, Imputation, chuẩn hóa Min-Max/StandardScaler CHỈ ĐƯỢC FIT trên tập dữ liệu này.")
    add_bullet(doc, "Tập Kiểm định (Validation Set - 15%): ", "Gồm 45,044 bản ghi. Sử dụng độc quyền để điều chỉnh siêu tham số (Hyperparameter Tuning) và cơ chế dừng sớm (Early Stopping) nhằm chống quá khớp (Overfitting).")
    add_bullet(doc, "Tập Kiểm thử độc lập (Holdout Test Set - 15%): ", "Gồm 45,045 bản ghi. Được bảo toàn nguyên vẹn trong suốt quá trình thử nghiệm và CHỈ ĐƯỢC CHẤM ĐIỂM ĐÚNG 1 LẦN DUY NHẤT để đánh giá năng lực tổng quát hóa khách quan của mô hình.")

    add_h2(doc, "5.2. Thuật toán mô hình cơ sở: Hồi quy Ridge chuẩn hóa L2 (Ridge Baseline)")
    add_styled_p(
        doc,
        "Mô hình cơ sở (Baseline) được xây dựng dựa trên thuật toán Hồi quy tuyến tính có phạt chuẩn L2 (Ridge Regression), giải quyết vấn đề đa cộng tuyến giữa các đặc trưng số học và mã hóa One-Hot. Hàm mục tiêu tối thiểu hóa tổn thất bình phương trung bình kết hợp số hạng chính quy hóa L2."
    )
    add_styled_p(
        doc,
        "Với siêu tham số tối ưu alpha = 1.0, Ridge Regression thiết lập điểm sàn hiệu năng: R² = 0.6266 trên tập Test, sai số tỷ lệ trung vị MdAPE = 37.28%."
    )

    add_h2(doc, "5.3. Thuật toán mô hình đề xuất: Cây quyết định tăng cường độ dốc LightGBM")
    add_styled_p(
        doc,
        "LightGBM (Light Gradient Boosting Machine) là giải thuật học máy dựa trên cây quyết định tiên tiến do Microsoft phát triển. LightGBM vượt trội so với XGBoost truyền thống nhờ 2 kỹ thuật đột phá:"
    )
    add_bullet(doc, "Kỹ thuật GOSS (Gradient-based One-Side Sampling): ", "Giữ lại toàn bộ các mẫu có gradient lớn (chứa nhiều thông tin lỗi) và lấy mẫu ngẫu nhiên trên các mẫu có gradient nhỏ, giúp giảm độ phức tạp tính toán mà vẫn bảo toàn độ chính xác.")
    add_bullet(doc, "Kỹ thuật EFB (Exclusive Feature Bundling): ", "Gộp các đặc trưng thưa xung đột loại trừ lẫn nhau vào một bó đặc trưng duy nhất, giảm số chiều dữ liệu đáng kể.")
    add_bullet(doc, "Chiến lược phân nhánh theo lá (Leaf-wise Tree Growth): ", "Khác với cách phân nhánh theo tầng (Level-wise) của Random Forest hay XGBoost chuẩn, LightGBM chọn lá có độ giảm tổn thất (Loss reduction) lớn nhất để phân nhánh, giúp đạt độ sâu tối ưu nhanh hơn.")
    
    add_styled_p(
        doc,
        "Bộ siêu tham số tối ưu được lựa chọn qua tập Validation: n_estimators = 500, learning_rate = 0.05, num_leaves = 63, min_child_samples = 25, early_stopping_rounds = 50."
    )

    add_h2(doc, "5.4. So sánh kết quả định lượng giữa Baseline Ridge và LightGBM (Bảng Đối Chiếu)")
    add_styled_p(
        doc,
        "Bảng 5.1 trình bày sự so sánh toàn diện giữa mô hình cơ sở Ridge Regression và mô hình LightGBM Regressor trên tập kiểm thử độc lập (Holdout Test 45,045 mẫu) trên cả hai thang đo: Thang logarit chuẩn hóa và Thang tiền tệ thực tế (Tỷ VNĐ)."
    )

    table_ml_headers = ["Chỉ Số Đánh Giá (Metric)", "Mô Hình Cơ Sở (Ridge Baseline)", "Mô Hình Đề Xuất (LightGBM)", "Mức Độ Cải Thiện Vượt Trội"]
    table_ml_data = [
        ["Tập dữ liệu đánh giá", "45,045 mẫu Test (15%)", "45,045 mẫu Test (15%)", "Độc lập 100%, không rò rỉ dữ liệu"],
        ["Hệ số xác định R² (log-scale)", "0.6266 (62.66%)", "0.8537 (85.37%)", "TĂNG +36.2% (Giải thích được 85.4% phương sai)"],
        ["Sai số căn quân phương RMSE (log)", "0.6556", "0.4104", "GIẢM -37.4% sai số toàn phương"],
        ["Sai số tuyệt đối trung bình MAE (log)", "0.4918", "0.2907", "GIẢM -40.9% sai số tuyệt đối"],
        ["MAE trên thang tiền tệ thực tế", "10.1771 Tỷ VNĐ", "4.6440 Tỷ VNĐ", "GIẢM -54.4% (Sai số giảm hơn một nửa!)"],
        ["Sai số tuyệt đối trung vị (MedAE)", "2.6236 Tỷ VNĐ", "1.3597 Tỷ VNĐ", "GIẢM -48.2% (50% căn nhà lệch dưới 1.36 tỷ)"],
        ["RMSE trên thang tiền tệ thực tế", "90.3788 Tỷ VNĐ", "13.7568 Tỷ VNĐ", "GIẢM -84.8% (Kháng nhiễu cực đoan xuất sắc)"],
        ["Sai số phần trăm tuyệt đối trung bình (MAPE)", "62.40%", "33.16%", "CẢI THIỆN -46.9% độ chính xác tỷ lệ"],
        ["Sai số phần trăm tuyệt đối trung vị (MdAPE)", "37.28%", "20.47%", "CẢI THIỆN -45.1% (Sai số điển hình chỉ ~20%)"]
    ]
    t_ml = doc.add_table(rows=len(table_ml_data) + 1, cols=4)
    style_table(t_ml, [2.1, 1.4, 1.4, 1.4], table_ml_headers, table_ml_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "5.5. Phân tích tầm quan trọng của các đặc trưng (Feature Importance)")
    add_styled_p(
        doc,
        "Hình 5.1 thể hiện tầm quan trọng của các đặc trưng (Feature Importance) được tính theo số lần phân nhánh (Split count) của mô hình LightGBM."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/05_feature_importance.png",
        "Hình 5.1: Tầm quan trọng của các đặc trưng trong mô hình LightGBM (Diện tích, Quận/Huyện, Mặt tiền, Tỉnh/Thành đứng đầu)",
        width_inches=5.8
    )

    table_fi_headers = ["Thứ Hạng", "Mã Đặc Trưng", "Tên Thuộc Tính Nghiệp Vụ", "Điểm Quan Trọng (Split Count)", "Tác Động Nghiệp Vụ Định Giá"]
    table_fi_data = [
        ["1", "area", "Diện tích đất / sàn (m²)", "7,466 điểm", "Đặc trưng chi phối cốt lõi quy mô bất động sản"],
        ["2", "district_clean", "Quận / Huyện", "6,996 điểm", "Vị trí địa lý nội đô quy định khung giá đất cơ sở"],
        ["3", "frontage_width", "Chiều rộng mặt tiền (m)", "3,724 điểm", "Mặt tiền lớn quyết định khả năng kinh doanh buôn bán"],
        ["4", "province_clean", "Tỉnh / Thành phố", "2,075 điểm", "Quy mô kinh tế và mức độ đô thị hóa vùng miền"],
        ["5", "house_direction", "Hướng nhà", "1,418 điểm", "Yếu tố phong thủy và độ thông thoáng khí hậu"],
        ["6", "property_type_name", "Loại hình bất động sản", "1,375 điểm", "Phân khúc (Nhà phố, Biệt thự, Căn hộ chung cư)"],
        ["7", "house_depth", "Chiều sâu thửa đất (m)", "1,198 điểm", "Hình thế đất vuông vức hay nở hậu"],
        ["8", "bedroom_count", "Số phòng ngủ", "1,154 điểm", "Công năng sử dụng và diện tích hữu dụng"],
        ["9", "is_frontage", "Cờ nhà mặt phố kinh doanh", "881 điểm", "Được trích xuất từ NLP tiêu đề và mô tả"],
        ["10", "road_width", "Độ rộng đường trước nhà (m)", "874 điểm", "Khả năng lưu thông của phương tiện ô tô"]
    ]
    t_fi = doc.add_table(rows=len(table_fi_data) + 1, cols=5)
    style_table(t_fi, [0.6, 1.2, 1.7, 1.2, 1.6], table_fi_headers, table_fi_data,
                [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "5.6. Phân tích phần dư và chẩn đoán sai số mô hình (Residual Analysis)")
    add_styled_p(
        doc,
        "Hình 5.2 cung cấp 4 biểu đồ chẩn đoán phần dư trên tập kiểm thử độc lập: Tương quan Thực tế vs Dự báo, Phân bố sai số phần dư (Residuals Plot), Sai số tuyệt đối theo phân khúc giá và Histogram phân bố sai số."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/06_residual_analysis.png",
        "Hình 5.2: Biểu đồ phân tích phần dư và chẩn đoán sai số dự báo của mô hình LightGBM trên tập kiểm thử",
        width_inches=6.2
    )

    table_err_headers = ["Tỉnh / Thành Phố", "Số Mẫu Kiểm Thử", "Giá Thực Tế Trung Vị", "Giá Dự Báo Trung Vị", "MAE (Tỷ VNĐ)", "MedAE (Tỷ)", "MdAPE (%)"]
    table_err_data = [
        ["TP. Hồ Chí Minh", "15,871 mẫu", "8.50 Tỷ VNĐ", "8.21 Tỷ VNĐ", "6.40 Tỷ", "1.86 Tỷ", "22.17%"],
        ["Hà Nội", "15,687 mẫu", "8.90 Tỷ VNĐ", "9.14 Tỷ VNĐ", "4.22 Tỷ", "1.53 Tỷ", "17.57%"],
        ["Đà Nẵng", "2,580 mẫu", "7.57 Tỷ VNĐ", "7.74 Tỷ VNĐ", "5.65 Tỷ", "1.69 Tỷ", "22.66%"],
        ["Bình Dương", "1,977 mẫu", "2.91 Tỷ VNĐ", "3.01 Tỷ VNĐ", "1.41 Tỷ", "0.54 Tỷ", "18.63%"],
        ["Khánh Hòa", "1,378 mẫu", "4.50 Tỷ VNĐ", "4.68 Tỷ VNĐ", "4.10 Tỷ", "1.23 Tỷ", "26.33%"]
    ]
    t_err = doc.add_table(rows=len(table_err_data) + 1, cols=7)
    style_table(t_err, [1.3, 0.9, 0.9, 0.9, 0.8, 0.7, 0.8], table_err_headers, table_err_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    # ==========================================================================
    # CHƯƠNG 6: HIỆU NĂNG, TỐI ƯU HÓA LƯU TRỮ VÀ KIỂM THỬ TỰ ĐỘNG
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 6: HIỆU NĂNG HỆ THỐNG, TỐI ƯU HÓA LƯU TRỮ VÀ KIỂM THỬ TỰ ĐỘNG")
    
    add_h2(doc, "6.1. Thời gian xử lý và thông lượng qua các tầng (Throughput)")
    add_styled_p(
        doc,
        "Toàn bộ pipeline xử lý từ lúc nạp dữ liệu thô đến khi lưu trữ vào CSDL Serving hoàn tất trong 451.43 giây (~7.52 phút) trên 350,075 dòng. Thông lượng xử lý phân tán PySpark đạt tốc độ cao ở các tầng đầu và giảm dần khi thực hiện trích xuất NLP và nạp CSDL quan hệ."
    )
    
    table_perf_headers = ["Giai Đoạn Pipeline", "Thời Gian (Giây)", "Thời Gian (Phút)", "Số Bản Ghi Xử Lý", "Thông Lượng (Dòng/Giây)", "Ghi Chú Kỹ Thuật"]
    table_perf_data = [
        ["1. Thu Nạp Thô (Ingestion)", "35.00s", "0.58m", "350,075 dòng", "10,002.1 dòng/s", "Nạp parquet thô bất đồng bộ"],
        ["2. Làm Sạch Tầng Bạc (Silver Clean)", "50.33s", "0.84m", "350,075 dòng", "6,955.6 dòng/s", "Khử trùng lặp đa cột & parse giá"],
        ["3. Trích Xuất Tầng Vàng (Gold Features)", "76.67s", "1.28m", "307,457 dòng", "4,010.1 dòng/s", "Lọc ngoại lệ IQR & Regex NLP"],
        ["4. Nạp CSDL Serving (DB Load)", "289.43s", "4.82m", "300,295 dòng", "1,037.5 dòng/s", "Chunk nạp 10,000 & đánh 4 Index"],
        ["Tổng Toàn Bộ Pipeline", "451.43s", "7.52m", "350,075 -> 300,295", "775.5 dòng/s", "End-to-end tự động hoàn toàn"]
    ]
    t_perf = doc.add_table(rows=len(table_perf_data) + 1, cols=6)
    style_table(t_perf, [1.6, 0.8, 0.8, 1.1, 1.1, 1.3], table_perf_headers, table_perf_data,
                [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    add_h2(doc, "6.2. Tối ưu hóa lưu trữ cột (Columnar Parquet Snappy Compression)")
    add_styled_p(
        doc,
        "Định dạng Parquet nén Snappy mang lại hiệu quả vượt bậc so với CSV thô. Không chỉ giảm dung lượng ổ đĩa, Parquet còn hỗ trợ cơ chế Predicate Pushdown và Column Pruning, giúp truy vấn chỉ nạp các cột cần thiết vào bộ nhớ RAM."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/07_pipeline_performance_storage.png",
        "Hình 6.1: Hiệu năng xử lý (thời gian, thông lượng) và dung lượng lưu trữ qua các tầng dữ liệu",
        width_inches=6.1
    )
    
    add_h2(doc, "6.3. Bảng điều khiển giám sát quy trình và phân loại lỗi")
    add_styled_p(
        doc,
        "Hình 6.2 tổng hợp bảng điều khiển giám sát vận hành (Pipeline Monitoring Dashboard), trực quan hóa thời lượng từng bước, phân loại 49,780 bản ghi bị loại bỏ và tỷ lệ giữ lại dữ liệu toàn trình."
    )
    
    add_image(
        doc,
        BASE_DIR / "docs/images/05_pipeline_monitoring_dashboard.png",
        "Hình 6.2: Bảng điều khiển giám sát quy trình vận hành và cơ cấu loại bỏ bản ghi",
        width_inches=6.0
    )

    add_h2(doc, "6.4. Hệ thống kiểm thử tự động toàn diện (Test Suite)")
    add_styled_p(
        doc,
        "Để bảo đảm tính ổn định và tính sẵn sàng chuyển giao cho hội đồng chấm điểm, toàn bộ mã nguồn được bảo vệ bởi bộ kiểm thử tự động tests/test_pipelines.py gồm 10 bài kiểm thử nghiêm ngặt:"
    )

    table_test_headers = ["STT", "Hàm Kiểm Thử (Pytest)", "Mục Đích Kiểm Thử Kỹ Thuật", "Kết Quả", "Thời Gian Chạy"]
    table_test_data = [
        ["1", "test_directories_exist", "Kiểm tra cấu trúc thư mục chuẩn data/, models/, docs/images/", "PASSED", "0.02s"],
        ["2", "test_bronze_parquet", "Kiểm tra Parquet Bronze đủ 350,075 dòng và 3 cột Lineage", "PASSED", "0.42s"],
        ["3", "test_silver_parquet", "Kiểm tra Parquet Silver đạt 307,457 dòng, không còn null ở giá/S", "PASSED", "0.41s"],
        ["4", "test_gold_parquet", "Kiểm tra Parquet Gold đạt 300,295 dòng, đủ các cờ NLP & log_price", "PASSED", "0.43s"],
        ["5", "test_data_quality_and_lineage_report", "Kiểm toán JSON báo cáo chất lượng dữ liệu và tỷ lệ lưu lượng", "PASSED", "0.01s"],
        ["6", "test_storage_database", "Kiểm tra CSDL Serving khớp 100% (300,295 dòng) và đủ 4 chỉ mục", "PASSED", "0.35s"],
        ["7", "test_three_way_split_and_metrics_no_leakage", "Kiểm tra chia 70/15/15 và metric mô hình R² >= 0.80", "PASSED", "0.05s"],
        ["8", "test_train_serving_consistency_and_inference", "Kiểm tra đồng nhất pipeline tiền xử lý Train-Serving", "PASSED", "0.82s"],
        ["9", "test_evaluation_diagnostics_and_residual_plot", "Kiểm tra sự tồn tại của các biểu đồ chẩn đoán mô hình", "PASSED", "0.02s"],
        ["10", "test_pipeline_summary_metrics_and_charts", "Kiểm tra bộ tóm tắt số liệu 7 mục và bộ 7 biểu đồ phân giải cao", "PASSED", "1.98s"],
        ["Tổng", "Toàn bộ 10 ca kiểm thử", "Bao phủ 100% từ Ingestion đến Serving & Web App", "10/10 PASS", "4.73s"]
    ]
    t_test = doc.add_table(rows=len(table_test_data) + 1, cols=5)
    style_table(t_test, [0.6, 2.3, 2.3, 0.9, 0.8], table_test_headers, table_test_data,
                [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT])
    
    add_styled_p(doc, "", font_size=10, space_before=0, space_after=6)

    # ==========================================================================
    # CHƯƠNG 7: HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ CÁC BƯỚC CHẠY DỰ ÁN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 7: HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ CÁC BƯỚC CHẠY TOÀN BỘ DỰ ÁN")
    
    add_h2(doc, "7.1. Cấu hình môi trường và tiền điều kiện hệ thống")
    add_bullet(doc, "Hệ điều hành: ", "Tương thích hoàn toàn Windows 10/11, Linux (Ubuntu/Debian) và macOS.")
    add_bullet(doc, "Phiên bản Python: ", "Python 3.10, 3.11 hoặc 3.12 (khuyến nghị Python 3.12).")
    add_bullet(doc, "Môi trường Java: ", "Java Development Kit (JDK) 17 trở lên (BẮT BUỘC để Apache PySpark khởi tạo JVM). Đặt biến môi trường JAVA_HOME trỏ tới thư mục cài đặt JDK.")
    add_bullet(doc, "Cấu hình phần cứng: ", "RAM tối thiểu 8 GB (khuyến nghị 16 GB), ổ cứng trống tối thiểu 2 GB.")
    add_bullet(doc, "Cài đặt gói thư viện phụ thuộc: ", "pip install -r requirements.txt")

    add_h2(doc, "7.2. Các bước chạy toàn bộ dự án bằng dòng lệnh (CLI)")
    add_styled_p(
        doc,
        "Dự án được chuẩn hóa để có thể chạy end-to-end từng bước hoặc toàn bộ bằng một dòng lệnh duy nhất:"
    )
    add_bullet(doc, "Lệnh chạy toàn bộ pipeline (End-to-End): ", "python run_pipeline.py all (hoặc lệnh make all trên Linux/macOS). Lệnh này sẽ tự động thực thi tuần tự 5 tầng từ nạp dữ liệu đến đánh giá mô hình.")
    add_bullet(doc, "Bước 1 - Thu nạp thô (Ingest Raw): ", "python run_pipeline.py ingest (hoặc make ingest). Nạp dữ liệu từ Hugging Face và ghi vào data/bronze/ dưới định dạng Parquet kèm metadata.")
    add_bullet(doc, "Bước 2 - Làm sạch và biến đổi (PySpark ETL): ", "python run_pipeline.py etl (hoặc make etl). Chạy đồng thời clean.py (tạo Silver) và features.py (tạo Gold với NLP và lọc ngoại lệ).")
    add_bullet(doc, "Bước 3 - Nạp cơ sở dữ liệu Serving: ", "python run_pipeline.py load (hoặc make load). Nạp 300,295 bản ghi Gold vào PostgreSQL / SQLite và tự động tạo 4 chỉ mục B-Tree.")
    add_bullet(doc, "Bước 4 - Huấn luyện mô hình học máy: ", "python run_pipeline.py train (hoặc make train). Huấn luyện Ridge Regression baseline và LightGBM với giao thức phân chia 3 tập nghiêm ngặt.")
    add_bullet(doc, "Bước 5 - Đánh giá và chẩn đoán mô hình: ", "python run_pipeline.py evaluate (hoặc make evaluate). Xuất bảng số liệu metrics.json, phân tích sai số theo vùng miền và biểu đồ phần dư.")
    add_bullet(doc, "Bước 6 - Khởi chạy ứng dụng Web Dashboard: ", "streamlit run src/serving/app.py --server.port 8501 (hoặc make app). Mở trình duyệt tại địa chỉ http://localhost:8501.")
    add_bullet(doc, "Bước 7 - Chạy bộ kiểm thử tự động: ", "pytest tests/test_pipelines.py -v. Kiểm tra toàn diện 10 ca kiểm thử của hệ thống.")

    add_h2(doc, "7.3. Hướng dẫn khởi chạy tự động 1-click trên hệ điều hành Windows")
    add_styled_p(
        doc,
        "Để hỗ trợ giảng viên và người đánh giá không cần thao tác dòng lệnh phức tạp, nhóm nghiên cứu đã đóng gói sẵn 3 tệp thực thi Windows Batch (.bat) tương thích 100% với cmd.exe:"
    )
    add_bullet(doc, "run.bat (Menu điều khiển trung tâm tương tác): ", "Chỉ cần nhấp đúp chuột vào run.bat, màn hình console hiển thị menu chuyên nghiệp gồm 8 chức năng từ [1] đến [8]. Người dùng chỉ cần gõ số tương ứng và nhấn Enter.")
    add_bullet(doc, "chay_pipeline.bat (Chạy toàn bộ pipeline): ", "Tự động thiết lập JAVA_HOME, chạy trọn vẹn 6 tầng dữ liệu và in thông báo hoàn tất.")
    add_bullet(doc, "chay_app.bat hoặc start_app.bat (Mở ứng dụng Web): ", "Tự động kích hoạt máy chủ Streamlit và mở giao diện tại cổng 8501.")

    add_h2(doc, "7.4. Cấu trúc 4 Phân hệ của Ứng dụng Web Streamlit")
    add_styled_p(
        doc,
        "Ứng dụng Streamlit (src/serving/app.py) được cấu trúc hóa theo 4 Tab chức năng học thuật rõ ràng:"
    )
    add_bullet(doc, "Tab 1: Kiến Trúc và Tích Hợp Dữ Liệu: ", "Trực quan hóa sơ đồ Medallion Lakehouse 6 tầng, quy mô kho nguồn 3.5 triệu dòng trên 10 shards, các chỉ số lưu lượng và tỷ lệ giữ lại qua các tầng Bronze, Silver, Gold.")
    add_bullet(doc, "Tab 2: Quản Lý Chất Lượng và Biến Đổi Dữ Liệu: ", "Trực quan hóa phễu lưu lượng 2 panel (số lượng và tỷ lệ giữ lại), biểu đồ tỷ lệ khuyết thiếu phân 3 nhóm màu cảnh báo, bảng 5 số thống kê trước/sau lọc ngoại lệ (Mean, Median, Std, Min, Max).")
    add_bullet(doc, "Tab 3: Phân Tích Thị Trường Bất Động Sản (EDA): ", "Bộ 4 biểu đồ EDA chuẩn học thuật phân tích địa lý (giá trung vị theo tỉnh thành), phân khúc loại hình, đơn giá theo phòng ngủ và ma trận tương quan đa biến.")
    add_bullet(doc, "Tab 4: Hiệu Năng Xử Lý, Lưu Trữ & Ứng Dụng Học Máy: ", "Dashboard giám sát pipeline, hiệu quả nén Parquet Snappy, dung lượng SQLite CSDL Serving và biểu mẫu định giá tự động bằng mô hình LightGBM (bảo đảm tính nhất quán Train-Serving).")

    add_h2(doc, "7.5. Hướng dẫn xuất dữ liệu mẫu phục vụ kiểm toán")
    add_styled_p(
        doc,
        "Người đánh giá có thể xuất nhanh 10,000 bản ghi mẫu từ Tầng Vàng ra định dạng Excel (.xlsx) và CSV (.csv) bằng cách chọn chức năng [8] trong run.bat hoặc chạy lệnh Python:"
    )
    add_styled_p(
        doc,
        "python -c \"import pandas as pd; df = pd.read_parquet('data/gold/vietnam_real_estates_gold.parquet'); df.head(10000).to_excel('data/vietnam_real_estates_sample.xlsx', index=False); df.head(10000).to_csv('data/vietnam_real_estates_sample.csv', index=False, encoding='utf-8-sig'); print('[OK] Da xuat thanh cong')\"",
        font_size=10, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER
    )

    # ==========================================================================
    # CHƯƠNG 8: KẾT LUẬN, GIỚI HẠN & HƯỚNG PHÁT TRIỂN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 8: KẾT LUẬN, GIỚI HẠN CỦA HỆ THỐNG VÀ LỘ TRÌNH PHÁT TRIỂN")
    
    add_h2(doc, "8.1. Đánh giá mức độ hoàn thành dự án")
    add_styled_p(
        doc,
        "Dự án đã hoàn thành xuất sắc và toàn diện tất cả các mục tiêu đề ra trong khuôn khổ sprint 2 tuần:"
    )
    add_bullet(doc, "Hoàn thiện trọn vẹn 6 tầng Medallion Lakehouse: ", "Từ thu nạp thô, Bronze, Silver, Gold đến CSDL phục vụ và giao diện ứng dụng người dùng cuối.")
    add_bullet(doc, "Kiểm soát chất lượng dữ liệu khoa học: ", "Khử 29,686 tin trùng lặp, lọc 7,162 ngoại lệ, giảm phương sai nhiễu của giá 77 lần và diện tích hơn 200 lần mà không làm méo mó giá trị trung vị thực tế.")
    add_bullet(doc, "Mô hình học máy tối ưu vượt trội: ", "LightGBM Regressor đạt R² = 0.8537 và MdAPE = 20.47%, vượt xa mô hình cơ sở Ridge Regression mà không vi phạm rò rỉ dữ liệu.")
    add_bullet(doc, "Độ tin cậy và tự động hóa tuyệt đối: ", "Bộ kiểm thử tự động 10/10 tests pass trong 4.73s, hệ thống khởi chạy 1-click qua Makefile và file batch.")

    add_h2(doc, "8.2. Minh bạch các giới hạn khách quan của hệ thống")
    add_bullet(doc, "Phạm vi phân mảnh thực nghiệm: ", "Do giới hạn phần cứng máy trạm cá nhân trong thời gian 2 tuần, pipeline hiện tại kiểm chứng trên 1 phân mảnh đầy đủ (350,075 bản ghi thô). Mở rộng sang toàn bộ 10 phân mảnh (3.5 triệu dòng) đòi hỏi cụm phân tán Spark Cluster chuyên dụng.")
    add_bullet(doc, "Bản chất giá rao bán (Asking Price vs. Transaction Price): ", "Dữ liệu thu thập từ các tin đăng rao bán trên Internet, phản ánh kỳ vọng của bên bán. Trong thực tế, giá giao dịch công chứng tại văn phòng công chứng thường thấp hơn từ 5% – 15% tùy thuộc vào năng lực đàm phán và chu kỳ thanh khoản.")
    add_bullet(doc, "Thiếu hụt tọa độ địa lý chi tiết (GPS Coordinates): ", "Dữ liệu nguồn chưa tích hợp cặp tọa độ Kinh độ/Vĩ độ chính xác cho từng số nhà, làm hạn chế khả năng tính toán trực tiếp khoảng cách đến các tiện ích đô thị (bệnh viện, trường học, trạm metro).")

    add_h2(doc, "8.3. Lộ trình mở rộng trong tương lai")
    add_bullet(doc, "Mở rộng cụm phân tán (Spark Cluster Mode): ", "Triển khai mã nguồn PySpark lên cụm phân tán đa nút (Amazon EMR hoặc Databricks) để xử lý toàn bộ 3.5 triệu bản ghi và tự động cập nhật dữ liệu tin đăng mới hàng ngày.")
    add_bullet(doc, "Tích hợp dịch vụ Geocoding API: ", "Tự động chuyển đổi tên đường, phường, quận thành tọa độ không gian để tính toán các đặc trưng không gian (Spatial Features) phục vụ định giá chuyên sâu.")
    add_bullet(doc, "Mô hình hóa đồ thị tri thức (Graph Neural Networks - GNN): ", "Khai thác đồ thị liên kết giữa các căn nhà cùng khu vực, cùng chủ đầu tư hoặc cùng tuyến đường nhằm nâng cao hơn nữa độ chính xác dự báo.")

    add_styled_p(doc, "", font_size=12, space_before=10, space_after=10)
    
    # ==========================================================================
    # TÀI LIỆU THAM KHẢO
    # ==========================================================================
    add_h1(doc, "TÀI LIỆU THAM KHẢO")
    add_styled_p(doc, "[1] Zaharia, M., et al. (2016). Apache Spark: A unified engine for big data processing. Communications of the ACM, 59(11), 56-65.", font_size=11)
    add_styled_p(doc, "[2] Ke, G., et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems (NeurIPS), 30, 3146-3154.", font_size=11)
    add_styled_p(doc, "[3] Armbrust, M., et al. (2020). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. CIDR.", font_size=11)
    add_styled_p(doc, "[4] McKinney, W. (2010). Data structures for statistical computing in Python. Proceedings of the 9th Python in Science Conference, 51-56.", font_size=11)
    add_styled_p(doc, "[5] Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825-2830.", font_size=11)
    add_styled_p(doc, "[6] tinixai. (2024). Vietnam Real Estates Dataset (3.5M records). Hugging Face Datasets Hub.", font_size=11)

    output_path = BASE_DIR / "docs/Bao_Cao_Chi_Tiet_Du_An_House_Prediction.docx"
    alt_path = BASE_DIR / "docs/Bao_Cao_Chi_Tiet_Du_An_House_Prediction_PhamVanMinh.docx"
    
    saved_path = output_path
    try:
        doc.save(str(output_path))
        print(f"[SUCCESS] Bao cao Word da duoc khoi tao thanh cong tai: {output_path}")
    except PermissionError:
        doc.save(str(alt_path))
        saved_path = alt_path
        print(f"[NOTE] Tep cu dang duoc mo trong Word. Da luu thanh cong ban cap nhat tai: {alt_path}")
        
    print(f"[METRIC] Dung luong file: {saved_path.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    generate_report()
