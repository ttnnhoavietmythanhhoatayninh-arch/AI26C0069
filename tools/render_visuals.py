"""Render precise vector information poster and explicitly labelled UI mockup."""
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parent.parent

def text(x,y,value,size=24,color='#e7f0ff',weight='400'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="DejaVu Sans, sans-serif">{escape(value)}</text>'
def rect(x,y,w,h,fill,rx=20,stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def svg(w,h,body):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
def main():
    out=ROOT/'assets';out.mkdir(exist_ok=True)
    p=[rect(0,0,1400,1980,'#0b1528',0),rect(80,75,340,56,'#18334a',28),text(103,112,'AI26C0069 · EXCEL QA',23,'#72e9d0','700'),text(80,245,'HỎI ĐÁP',98,weight='700'),text(80,355,'BẢNG TÍNH EXCEL',86,weight='700'),text(84,425,'Đọc bảng đúng. Tính từ ô nguồn. Kiểm tra kết quả.',29,'#a9bcd5')]
    p += [rect(80,490,1240,240,'#14263e'),text(120,547,'QUY TRÌNH GIẢI BÀI',23,'#72e9d0','700')]
    for i,(title,sub) in enumerate([('Excel + câu hỏi','Nhiều sheet, ô gộp'),('Python','Tra cứu và tính toán'),('Qwen khi cần','Kế hoạch JSON'),('CSV','id,answer · UTF-8')]):
        x=120+i*305;p += [text(x,610,f'0{i+1}',27,'#72e9d0','700'),text(x,655,title,25,weight='700'),text(x,693,sub,18,'#a9bcd5')]
    p += [text(80,825,'KẾT QUẢ ĐÃ ĐO · KHÔNG GỌI API',28,'#72e9d0','700')]
    for x,n,label in [(80,'14/20','Dữ liệu công khai đợt 1'),(720,'30/30','Dữ liệu công khai đợt 2')]:
        p += [rect(x,870,600,235,'#182b44'),text(x+42,985,n,86,weight='700'),text(x+44,1055,label,24,'#a9bcd5')]
    p += [text(85,1155,'103 test đạt · Có bằng chứng ô nguồn · Không thực thi mã do LLM sinh',24),text(85,1200,'Public 1 còn 6 câu trống; public 2 đã giải đủ 30 câu.',23,'#a9bcd5'),text(85,1243,'Kết quả offline không đại diện điểm tập ẩn hoặc chất lượng Qwen.',22,'#a9bcd5')]
    p += [rect(80,1310,1240,360,'#14263e'),text(120,1373,'HAI CÁCH SỬ DỤNG',28,'#72e9d0','700'),text(120,1440,'LOCAL',28,weight='700'),text(120,1484,'Giao diện Python tùy chọn · Offline hoặc hybrid',25),text(120,1555,'BÀI CHẤM',28,weight='700'),text(120,1599,'Docker Linux amd64 · CLI nhận sáu tham số BTC',25)]
    p += [text(80,1760,'Minh bạch về chi phí và giới hạn',35,weight='700'),text(80,1818,'Offline: không phí API. Hybrid: chỉ mô hình BTC quy định, có thể tính phí.',23,'#a9bcd5'),text(80,1861,'API thật bản cũ: 3/5 đúng; bản vá mới chưa thử lại API.',23,'#a9bcd5'),text(80,1920,'github.com/ttnnhoavietmythanhhoatayninh-arch/AI26C0069',21,'#72e9d0')]
    poster=svg(1400,1980,''.join(p));(out/'poster.svg').write_text(poster,encoding='utf-8')
    g=[rect(0,0,1400,940,'#dce5f1',0),rect(38,38,1324,864,'#f3f6fb',16),rect(38,38,1324,44,'#13243b',16),text(62,67,'ExcelQA | AI26C0069',19),text(80,150,'ExcelQA',43,'#12223c','700'),text(82,188,'Giao diện Python local · MINH HỌA THIẾT KẾ, không phải ảnh chạy thực tế',22,'#516580')]
    for y,label,placeholder in [(240,'Thư mục dữ liệu','Chọn thư mục chứa queries.json và xlsx_files'),(310,'Thư mục kết quả','Chọn thư mục kết quả ở ngoài dữ liệu')]:
        g += [text(82,y+30,label,21,'#172a44'),rect(300,y,790,46,'white',7,'#c7d3e3'),text(318,y+30,placeholder,20,'#6c7b90'),rect(1110,y,190,46,'#e4edf8',7),text(1126,y+30,'Chọn thư mục',19,'#172a44')]
    g += [text(82,410,'Chế độ',21,'#172a44'),rect(300,378,240,46,'white',7,'#c7d3e3'),text(319,408,'offline',21,'#172a44'),text(82,477,'OpenRouter key',21,'#172a44'),rect(300,445,790,46,'white',7,'#c7d3e3'),text(318,475,'Chỉ nhập nếu chọn hybrid',20,'#6c7b90'),text(82,535,'Offline không gọi API · Hybrid có thể phát sinh phí · Không lưu key vào tệp',21,'#516580'),rect(82,561,250,49,'#166d79',7),text(109,593,'Chạy bộ câu hỏi',22,'white','700'),rect(350,561,125,49,'#e4edf8',7),text(380,593,'Dừng',22,'#172a44'),text(510,593,'Sẵn sàng. Chưa chạy dữ liệu.',22,'#516580'),rect(82,632,1218,12,'#d4dfed',6),rect(82,668,1218,147,'white',7,'#c7d3e3'),rect(82,668,1218,42,'#e4edf8',7),text(102,697,'ID',20,'#172a44','700'),text(232,697,'Đáp án',20,'#172a44','700'),text(100,757,'Kết quả sẽ xuất hiện sau khi chạy.',20,'#6c7b90'),text(82,858,'Có đáp án không đồng nghĩa đã đúng đáp án BTC. Xem đánh giá riêng.',21,'#516580')]
    preview=svg(1400,940,''.join(g));(out/'gui_preview.svg').write_text(preview,encoding='utf-8')
    from PIL import Image,ImageDraw,ImageFont
    import xml.etree.ElementTree as ET
    for name in ('poster','gui_preview'):
        doc=ET.fromstring((out/(name+'.svg')).read_text())
        im=Image.new('RGB',(int(doc.attrib['width']),int(doc.attrib['height'])),'white');draw=ImageDraw.Draw(im)
        for e in doc:
            a=e.attrib;kind=e.tag.split('}')[-1]
            if kind=='rect':
                x,y,w,h=[float(a[k]) for k in ('x','y','width','height')]
                stroke=a.get('stroke');stroke=None if stroke=='none' else stroke
                draw.rounded_rectangle((x,y,x+w,y+h),radius=float(a.get('rx',0)),fill=a['fill'],outline=stroke)
            elif kind=='text':
                bold=a.get('font-weight')=='700'
                font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',int(a['font-size']))
                draw.text((float(a['x']),float(a['y'])),e.text or '',font=font,fill=a['fill'],anchor='ls')
        im.save(out/(name+'.png'))
    print(out)
if __name__=='__main__':main()
