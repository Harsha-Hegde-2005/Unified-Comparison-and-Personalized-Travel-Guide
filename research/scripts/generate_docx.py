import zipfile
import xml.sax.saxutils as saxutils
import os

def escape(s):
    return saxutils.escape(s)

content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

with open("Research_Paper_Corrected.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

body_xml = []
in_table = False
table_rows = []
is_first_table_row = True
in_code_block = False

for line in lines:
    line = line.strip()
    if not line:
        continue

    # Code block detection
    if line.startswith("```"):
        in_code_block = not in_code_block
        continue

    if in_code_block:
        text = escape(line)
        body_xml.append(
            '<w:p><w:pPr><w:spacing w:after="40"/><w:ind w:left="360"/><w:shd w:val="clear" w:color="auto" w:fill="F8F9FA"/></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/></w:rPr>'
            '<w:t xml:space="preserve">' + text + '</w:t></w:r></w:p>'
        )
        continue

    # Table detection
    if line.startswith("|") and line.endswith("|"):
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if all(set(p).issubset({'-', ' ', ':'}) for p in parts if p):
            continue
        if not in_table:
            in_table = True
            is_first_table_row = True
            table_rows = [
                '<w:tbl><w:tblPr>'
                '<w:tblW w:w="5000" w:type="pct"/>'
                '<w:jc w:val="center"/>'
                '<w:tblBorders>'
                '<w:top w:val="single" w:sz="6" w:space="0" w:color="4A607A"/>'
                '<w:left w:val="none"/>'
                '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="4A607A"/>'
                '<w:right w:val="none"/>'
                '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>'
                '<w:insideV w:val="none"/>'
                '</w:tblBorders>'
                '</w:tblPr>'
            ]
        
        row_xml = ['<w:tr>']
        for p in parts:
            cell_text = escape(p)
            if is_first_table_row:
                row_xml.append(
                    '<w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="EBF1F5"/></w:tcPr>'
                    '<w:p><w:pPr><w:spacing w:before="60" w:after="60"/><w:jc w:val="center"/></w:pPr>'
                    '<w:r><w:rPr><w:b/><w:sz w:val="19"/><w:color w:val="1F3864"/></w:rPr>'
                    '<w:t>' + cell_text + '</w:t></w:r></w:p></w:tc>'
                )
            else:
                row_xml.append(
                    '<w:tc><w:p><w:pPr><w:spacing w:before="40" w:after="40"/></w:pPr>'
                    '<w:r><w:rPr><w:sz w:val="19"/></w:rPr>'
                    '<w:t>' + cell_text + '</w:t></w:r></w:p></w:tc>'
                )
        row_xml.append('</w:tr>')
        table_rows.append(''.join(row_xml))
        is_first_table_row = False
    else:
        if in_table:
            in_table = False
            table_rows.append('</w:tbl>')
            body_xml.append(''.join(table_rows))
            table_rows = []

        if line.startswith("# "):
            title = escape(line[2:])
            body_xml.append(
                '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="240"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="34"/><w:color w:val="1F3864"/></w:rPr>'
                '<w:t>' + title + '</w:t></w:r></w:p>'
            )
        elif line.startswith("## "):
            h1 = escape(line[3:])
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:before="240" w:after="100"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="2F5597"/></w:rPr>'
                '<w:t>' + h1 + '</w:t></w:r></w:p>'
            )
        elif line.startswith("### "):
            h2 = escape(line[4:])
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:before="180" w:after="80"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="23"/><w:color w:val="203764"/></w:rPr>'
                '<w:t>' + h2 + '</w:t></w:r></w:p>'
            )
        elif line.startswith("#### "):
            h3 = escape(line[5:])
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:before="140" w:after="60"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="21"/><w:color w:val="333333"/></w:rPr>'
                '<w:t>' + h3 + '</w:t></w:r></w:p>'
            )
        elif line.startswith("* ") or line.startswith("- "):
            bullet_text = escape(line[2:])
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="360"/><w:jc w:val="both"/></w:pPr>'
                '<w:r><w:rPr><w:sz w:val="21"/></w:rPr>'
                '<w:t xml:space="preserve">&#x2022; ' + bullet_text + '</w:t></w:r></w:p>'
            )
        elif line.startswith("> "):
            quote_text = escape(line[2:])
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:before="80" w:after="80"/><w:ind w:left="480" w:right="480"/><w:jc w:val="both"/></w:pPr>'
                '<w:r><w:rPr><w:i/><w:sz w:val="21"/><w:color w:val="595959"/></w:rPr>'
                '<w:t>' + quote_text + '</w:t></w:r></w:p>'
            )
        else:
            text = escape(line)
            body_xml.append(
                '<w:p><w:pPr><w:spacing w:after="100"/><w:jc w:val="both"/></w:pPr>'
                '<w:r><w:rPr><w:sz w:val="21"/></w:rPr>'
                '<w:t>' + text + '</w:t></w:r></w:p>'
            )

if in_table:
    table_rows.append('</w:tbl>')
    body_xml.append(''.join(table_rows))

doc_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body>' + ''.join(body_xml) + '</w:body>'
    '</w:document>'
)

output_docx = "Research_Paper_Corrected.docx"
with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", doc_xml)

print(f"Generated {output_docx} successfully! Size: {os.path.getsize(output_docx)} bytes")
