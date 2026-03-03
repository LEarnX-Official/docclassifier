from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import os

def generate_pdf(doc_type):
    filename = f"test_{doc_type}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)

    if doc_type == "identity_document":
        c.drawString(20 * mm, height - 20 * mm, "PASSPORT - EUROPEAN UNION")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "Surname: ROSSI")
        c.drawString(20 * mm, height - 50 * mm, "Given Names: MARIO")
        c.drawString(20 * mm, height - 60 * mm, "Date of Birth: 15 MAY 1985")
        c.drawString(20 * mm, height - 70 * mm, "Document Number: AA1234567")
        c.drawString(20 * mm, height - 80 * mm, "Expiry Date: 14 MAY 2030")

    elif doc_type == "employment_contract":
        c.drawString(20 * mm, height - 20 * mm, "LABOUR CONTRACT")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "Employer: Arletti Partners SRL")
        c.drawString(20 * mm, height - 50 * mm, "Employee: Mario Rossi")
        c.drawString(20 * mm, height - 60 * mm, "Position: Senior AI Engineer")
        c.drawString(20 * mm, height - 70 * mm, "Salary: 60,000 EUR per annum")

    elif doc_type == "payslip":
        c.drawString(20 * mm, height - 20 * mm, "CEDOLINO PAGA / PAYSLIP")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "Period: March 2026")
        c.drawString(20 * mm, height - 50 * mm, "Employee: Mario Rossi")
        c.drawString(20 * mm, height - 60 * mm, "Net Salary: 2.015,00 EUR")
        c.drawString(20 * mm, height - 70 * mm, "Employer: Arletti Partners SRL")

    elif doc_type == "invoice":
        c.drawString(20 * mm, height - 20 * mm, "INVOICE #2026-001")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "Issuer: Cloud Services Ltd")
        c.drawString(20 * mm, height - 50 * mm, "Recipient: Arletti Partners")
        c.drawString(20 * mm, height - 60 * mm, "Total Amount: 500,00 EUR")
        c.drawString(20 * mm, height - 70 * mm, "Date: 03/03/2026")

    elif doc_type == "tax_form":
        c.drawString(20 * mm, height - 20 * mm, "CERTIFICAZIONE UNICA (CU)")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "Fiscal Year: 2025")
        c.drawString(20 * mm, height - 50 * mm, "Sostituto d'imposta: Arletti Partners")
        c.drawString(20 * mm, height - 60 * mm, "Codice Fiscale: RSSMRA85E15H501Z")

    else: # other
        c.drawString(20 * mm, height - 20 * mm, "RANDOM NOTES")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, height - 40 * mm, "This is just a grocery list.")
        c.drawString(20 * mm, height - 50 * mm, "1. Milk, 2. Eggs, 3. Bread.")

    c.showPage()
    c.save()
    print(f"\nSuccessfully generated: {filename}")

if __name__ == "__main__":
    print("Select document type to generate:")
    print("1. identity_document\n2. employment_contract\n3. payslip\n4. invoice\n5. tax_form\n6. other")

    options = {
        "1": "identity_document",
        "2": "employment_contract",
        "3": "payslip",
        "4": "invoice",
        "5": "tax_form",
        "6": "other"
    }

    choice = input("Enter number (1-6): ")
    if choice in options:
        generate_pdf(options[choice])
    else:
        print("Invalid choice.")
