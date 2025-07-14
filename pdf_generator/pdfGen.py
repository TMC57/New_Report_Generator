from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import datetime
from fpdf import FPDF
import os
import json
    
def create_pdf(json_text: str, filename="rapport.pdf"):
    try:
        # Si c'est un texte JSON, on l'indente joliment
        try:
            data = json.loads(json_text)
            pretty_text = json.dumps(data, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            # Si ce n'est pas un JSON valide, on l'utilise brut
            pretty_text = json_text

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font("Courier", size=10)

        # Découpe le texte en lignes (max 100 caractères par ligne)
        lines = pretty_text.splitlines()
        for line in lines:
            pdf.multi_cell(0, 5, line)

        pdf.output(filename)
        print(f"PDF généré : {filename}")

    except Exception as e:
        print(f"Erreur lors de la création du PDF : {e}")

