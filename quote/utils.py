from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.platypus.flowables import Flowable
from django.utils import timezone
from django.contrib.staticfiles.finders import find
from decimal import Decimal
from django.conf import settings
import os
from PyPDF2 import PdfReader, PdfWriter

class HorizontalRule(Flowable):
    def __init__(self, width, thickness=1, color=colors.black):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

def generate_quote_pdf(booking):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=1*cm, rightMargin=1*cm, 
                            topMargin=1*cm, bottomMargin=1*cm)

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterBold', alignment=TA_CENTER, fontSize=16, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='RightAligned', alignment=TA_RIGHT, fontSize=10, fontName='Helvetica'))

    def create_header():
        # Use Django's static file finder to get the path
        logo_path = find('images/logo_travel.png')
        
        try:
            if logo_path and os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=100)  # Adjust width and height as needed
            else:
                raise FileNotFoundError("Logo file not found")
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Create a placeholder if there's any error
            logo = Drawing(100, 50)
            logo.add(Rect(0, 0, 100, 50, fillColor=colors.gray, strokeColor=None))
        
        header_text = [
            Paragraph("Travel Quote", styles['CenterBold']),
            Spacer(1, 0.5*cm),
            Paragraph(f"Quote Number: TS/{booking.id}", styles['Normal']),
            Paragraph(f"Date: {timezone.now().strftime('%d-%m-%Y')}", styles['Normal']),
        ]
        
        company_info = [
            Paragraph("Travel In Style", styles['RightAligned']),
            Paragraph("25, Rue Maximilien L-6463 Echternach", styles['RightAligned']),
            Paragraph("+352 2877 55 31", styles['RightAligned']),
            Paragraph("info@travelinstyle.lu", styles['RightAligned']),
        ]
        
        t = Table([[logo, header_text, company_info]], colWidths=[3*cm, 9*cm, 6*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        return [t, HorizontalRule(doc.width)]

    def create_client_info():
        passenger = booking.passengers.first()  # Get the first passenger
        data = [
            ["Client Information"],
            [f"Name: {passenger.first_name} {passenger.last_name}" if passenger else '[Please provide your email]'],
            [f"Email: {passenger.email or '[Please provide your email]'}"],
            [f"Phone: {passenger.phone or '[Please provide your phone number]'}"],
            ["Address: [Please provide your address]"],
        ]
        t = Table(data, colWidths=[doc.width])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))
        return [t, Spacer(1, 0.5*cm)]

    def create_journey_details():
        data = [
            ["Journey Details", ""],
            ["Cruise", booking.cruise_session.cruise.name],
            ["Departure", booking.cruise_session.start_date.strftime('%d-%m-%Y')],
            ["Return", booking.cruise_session.end_date.strftime('%d-%m-%Y')],
            ["Duration", f"{(booking.cruise_session.end_date - booking.cruise_session.start_date).days} days"],
            ["Ship", booking.cruise_session.cruise.company.name],
            ["From", "[Departure Port]"],
            ["To", "[Arrival Port]"],
            ["Category", booking.cruise_category_price.category.name],
            ["Passengers", str(booking.number_of_passengers)],
        ]
        t = Table(data, colWidths=[4*cm, doc.width-4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 1), (0, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))
        return [t, Spacer(1, 0.5*cm)]

    def create_pricing():
        total_price = booking.total_price
        deposit = total_price * Decimal('0.2')
        balance = total_price * Decimal('0.8')
        data = [
            ["Pricing", ""],
            ["Total Price", f"€{total_price:.2f}"],
            ["Deposit (20%)", f"€{deposit:.2f}"],
            ["Balance Due", f"€{balance:.2f}"],
        ]
        t = Table(data, colWidths=[6*cm, doc.width-6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 1), (0, -1), colors.beige),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))
        return [t, Spacer(1, 0.5*cm)]

    def create_notes():
        notes = """
        1. This is a quote and is subject to availability at the time of booking.
        2. Please review all details and contact us to complete your booking or for any questions.
        3. A deposit of 20% is required to confirm your booking.
        4. Full payment is due 30 days before departure.
        5. Please ensure all traveler details match their passport exactly.
        6. Travel insurance is strongly recommended.
        """
        return [
            Paragraph("Notes", styles['Heading2']),
            Paragraph(notes, styles['BodyText']),
            Spacer(1, 0.5*cm)
        ]

    def create_footer():
        return [
            HorizontalRule(doc.width),
            Paragraph("Thank you for choosing Travel In Style. We look forward to helping you create unforgettable memories.", styles['Italic']),
            Paragraph(f"Quote generated on {timezone.now().strftime('%d-%m-%Y at %H:%M')}. Valid for 14 days.", styles['Italic']),
        ]

    def create_cruise_flyer_section():
        if booking.cruise_session.cruise.flyer_pdf:
            return [
                Paragraph("Cruise Flyer", styles['Heading2']),
                Paragraph("Please find the cruise flyer attached at the end of this document.", styles['BodyText']),
                Spacer(1, 0.5*cm)
            ]
        else:
            return []

    # Build the document
    elements = []
    elements.extend(create_header())
    elements.extend(create_client_info())
    elements.extend(create_journey_details())
    elements.extend(create_pricing())
    elements.extend(create_cruise_flyer_section())  # New section
    elements.extend(create_notes())
    elements.extend(create_footer())

    # Generate the PDF
    doc.build(elements)
    buffer.seek(0)

    if booking.cruise_session.cruise.flyer_pdf:
        # Create a PDF writer object
        output = PdfWriter()

        # Add the pages from the quote PDF
        quote_pdf = PdfReader(buffer)
        for page in quote_pdf.pages:
            output.add_page(page)

        # Add the pages from the cruise flyer PDF
        flyer_pdf = PdfReader(booking.cruise_session.cruise.flyer_pdf.path)
        for page in flyer_pdf.pages:
            output.add_page(page)

        # Write the result to a new buffer
        buffer_final = BytesIO()
        output.write(buffer_final)
        buffer_final.seek(0)
        return buffer_final
    else:
        return buffer
