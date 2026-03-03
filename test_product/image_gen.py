from PIL import Image, ImageDraw, ImageFont
import os

def generate_test_image(doc_type):
    filename = f"test_{doc_type}.png"
    # Create a 800x1000 white image (resembles a scanned document)
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Try to load a font, otherwise use default
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        text_font = ImageFont.truetype("arial.ttf", 25)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    y_offset = 50

    if doc_type == "identity_document":
        d.text((50, y_offset), "IDENTITY CARD / CARTA D'IDENTITÀ", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "Surname: ROSSI",
            "Name: MARIO",
            "Nationality: ITALIAN",
            "Doc Number: AB12345XY",
            "Expiry: 20/05/2031"
        ]

    elif doc_type == "employment_contract":
        d.text((50, y_offset), "JOB OFFER / CONTRACT", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "Employer: Arletti Partners SRL",
            "Employee: Mario Rossi",
            "Position: Backend Developer",
            "Start Date: 01-04-2026",
            "Salary: 55.000 EUR"
        ]

    elif doc_type == "payslip":
        d.text((50, y_offset), "PAYSLIP - MARCH 2026", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "Company: Arletti Partners SRL",
            "Employee: Mario Rossi",
            "Gross Salary: 4.200,00",
            "Net Pay: 2.850,00 EUR",
            "Tax ID: RSSMRA85E15H501Z"
        ]

    elif doc_type == "invoice":
        d.text((50, y_offset), "TAX INVOICE", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "Invoice #: INV-2026-99",
            "Issuer: Tech Equipment Ltd",
            "Customer: Mario Rossi",
            "Total Amount: 1.250,00 EUR",
            "Date: 03/03/2026"
        ]

    elif doc_type == "tax_form":
        d.text((50, y_offset), "CERTIFICAZIONE UNICA 2026", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "Period: 2025",
            "Sostituto: Arletti Partners",
            "Recipient: Mario Rossi",
            "Redditi: 45.000,00 EUR"
        ]

    else: # other
        d.text((50, y_offset), "RANDOM DOCUMENT", fill=(0, 0, 0), font=title_font)
        y_offset += 100
        fields = [
            "This is a handwritten note.",
            "Meeting scheduled for 3 PM.",
            "Don't forget the coffee."
        ]

    for field in fields:
        d.text((50, y_offset), field, fill=(0, 0, 0), font=text_font)
        y_offset += 50

    img.save(filename)
    print(f"Generated image: {filename}")

if __name__ == "__main__":
    print("Select image type to generate:")
    types = ["identity_document", "employment_contract", "payslip", "invoice", "tax_form", "other"]
    for i, t in enumerate(types, 1):
        print(f"{i}. {t}")

    choice = input("Enter number (1-6): ")
    if choice.isdigit() and 1 <= int(choice) <= 6:
        generate_test_image(types[int(choice)-1])
    else:
        print("Invalid choice.")
