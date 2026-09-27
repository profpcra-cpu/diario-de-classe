import io
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawRightString(landscape(A4)[0] - 20, 15, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

def gerar_pdf_afin(df_matriz, turma, semestre):
    buffer = io.BytesIO()
    # Usar A4 em paisagem para acomodar todas as colunas de UCs (FAL/CON)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=25
    )

    story = []
    styles = getSampleStyleSheet()

    colunas_df = list(df_matriz.columns)
    
    col_mat = 'matricula' if 'matricula' in colunas_df else colunas_df[0]
    col_nome = 'nome' if 'nome' in colunas_df else ('ESTUDANTE' if 'ESTUDANTE' in colunas_df else colunas_df[1])

    uc_cols = [c for c in colunas_df if c not in [col_mat, col_nome]]

    ucs_unicas = []
    for c in uc_cols:
        if c.endswith(" - FAL"):
            uc_name = c.replace(" - FAL", "")
            if uc_name not in ucs_unicas:
                ucs_unicas.append(uc_name)

    # Construção do Cabeçalho da Tabela idêntico ao modelo oficial
    row_h0 = ["SEEDF CEP ETP - AFIN", "", "CURSO", "TÉCNICO EM SECRETARIA ESCOLAR"] + [""] * (len(uc_cols) - 1)
    row_h1 = ["SEMESTRE", semestre, ""] + [""] * (len(uc_cols) + 1)
    row_h2 = ["TURMA", turma, ""] + [""] * (len(uc_cols) + 1)
    
    row_h3 = ["MATRÍCULA", "ESTUDANTE"]
    for uc in ucs_unicas:
        row_h3.extend([uc, ""])

    row_h4 = ["", ""]
    for _ in ucs_unicas:
        row_h4.extend(["FAL", "CON"])

    table_data = [row_h0, row_h1, row_h2, row_h3, row_h4]

    # Preenchimento dos dados dos alunos
    for _, row in df_matriz.iterrows():
        r_data = [str(row[col_mat]), str(row[col_nome])]
        for uc in ucs_unicas:
            val_fal = row.get(f"{uc} - FAL", "0")
            val_con = row.get(f"{uc} - CON", "AP")
            r_data.extend([str(val_fal) if pd.notna(val_fal) else "0", str(val_con) if pd.notna(val_con) else "AP"])
        table_data.append(r_data)

    # Larguras das colunas proporcionais
    num_ucs = len(ucs_unicas)
    col_widths = [65, 140] + [25, 25] * num_ucs
    
    t = Table(table_data, colWidths=col_widths, repeatRows=5)

    t_style = TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#002060')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#002060')),
        ('TEXTCOLOR', (2, 0), (3, 0), colors.whitesmoke),
        ('FONTNAME', (2, 0), (3, 0), 'Helvetica-Bold'),
        
        ('BACKGROUND', (0, 1), (0, 2), colors.HexColor('#002060')),
        ('TEXTCOLOR', (0, 1), (0, 2), colors.whitesmoke),
        ('FONTNAME', (0, 1), (0, 2), 'Helvetica-Bold'),
        ('BACKGROUND', (1, 1), (1, 2), colors.HexColor('#D9D9D9')),
        ('TEXTCOLOR', (1, 1), (1, 2), colors.black),
        ('FONTNAME', (1, 1), (1, 2), 'Helvetica-Bold'),

        ('BACKGROUND', (0, 3), (-1, 4), colors.HexColor('#002060')),
        ('TEXTCOLOR', (0, 3), (-1, 4), colors.whitesmoke),
        ('FONTNAME', (0, 3), (-1, 4), 'Helvetica-Bold'),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#888888')),
        
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (3, 0), (-1, 0)),
        ('SPAN', (1, 1), (-1, 1)),
        ('SPAN', (1, 2), (-1, 2)),
    ])

    for i in range(num_ucs):
        col_idx = 2 + (i * 2)
        t_style.add('SPAN', (col_idx, 3), (col_idx + 1, 3))

    for i in range(5, len(table_data)):
        if i % 2 == 0:
            t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9F9F9'))
        else:
            t_style.add('BACKGROUND', (0, i), (-1, i), colors.white)
        t_style.add('ALIGN', (1, i), (1, i), 'LEFT')

    t.setStyle(t_style)
    story.append(t)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
