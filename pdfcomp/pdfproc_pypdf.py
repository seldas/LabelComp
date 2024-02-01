import PyPDF2

def extract_pdf_text(file_path):
    pdf_file = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    text_data = []
    
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        content = page.extractText()
        font = page.get("/Font")
        font_size = page.get("/FontSize")
        if not font or not font_size:
            print('not available', page_num)
            continue
        for char in content:
            if "/F" in font[char[0]]:
                font_style = font[char[0]]["/F"].get("/FontDescriptor").get("/Flags")
                if font_style & 1 == 1:
                    text_data.append({"text": char[1], "font_size": font_size[char[0]], "bold": True})
                else:
                    text_data.append({"text": char[1], "font_size": font_size[char[0]], "bold": False})
            else:
                text_data.append({"text": char[1], "font_size": font_size[char[0]], "bold": False})
    return text_data

file_path = "../static/example/Adcetris_125388s094lbl_03_20_2018.pdf"
text_data = extract_pdf_text(file_path)

for data in text_data[:10]:
    print("Text: ", data["text"], " Font Size: ", data["font_size"], " Bold: ", data["bold"])