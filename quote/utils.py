import logging
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.graphics.shapes import Drawing, Rect
from django.utils import timezone
from django.contrib.staticfiles.finders import find
from reportlab.platypus.flowables import Flowable
from decimal import Decimal
import os
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

class HorizontalRule(Flowable):
    def __init__(self, width, thickness=1, color=colors.black):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

def get_logo(logo_path):
    try:
        if logo_path and os.path.exists(logo_path):
            return Image(logo_path, width=100, height=100)
        raise FileNotFoundError("Logo file not found")
    except Exception as e:
        logger.error(f"Error loading logo: {e}")
        logo = Drawing(100, 50)
        logo.add(Rect(0, 0, 100, 50, fillColor=colors.gray, strokeColor=None))
        return logo

def create_header(quote, styles, doc):
    logo_path = find('images/logo_travel.png')
    logo = get_logo(logo_path)
    
    header_text = [
        Paragraph("Travel Quote", styles['CenterBold']),
        Spacer(1, 0.5*cm),
        Paragraph(f"Quote Number: TS/{quote.id}", styles['Normal']),
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

def create_client_info(quote, doc):
    passenger = quote.passengers.first()
    data = [
        ["Client Information"],
        [f"Name: {passenger.first_name} {passenger.last_name}" if passenger else '[Please provide your name]'],
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

def create_journey_details(quote, styles, doc):
    cruise = quote.cruise_session.cruise
    data = [
        ["Journey Details", ""],
        ["Cruise", cruise.name],
        ["Departure", quote.cruise_session.start_date.strftime('%d-%m-%Y')],
        ["Return", quote.cruise_session.end_date.strftime('%d-%m-%Y')],
        ["Duration", f"{quote.cruise_session.duration()} days"],
        ["Ship", cruise.company.name],
        ["Type", cruise.cruise_type.name],
        ["Brand", cruise.brand.name if cruise.brand else "N/A"],
        ["Category", quote.cruise_cabin_price.cabin_type.name],
        ["Passengers", str(quote.number_of_passengers)],
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

    itinerary_data = [["Day", "Port", "Arrival", "Departure", "Description"]]
    itineraries = cruise.itineraries.all().order_by('day')
    for itinerary in itineraries:
        itinerary_data.append([
            str(itinerary.day),
            itinerary.port.name if itinerary.port else "At Sea",
            itinerary.arrival_time.strftime('%H:%M') if itinerary.arrival_time else '-',
            itinerary.departure_time.strftime('%H:%M') if itinerary.departure_time else '-',
            Paragraph(itinerary.description[:100] + '...' if len(itinerary.description) > 100 else itinerary.description, styles['BodyText'])
        ])

    itinerary_table = Table(itinerary_data, colWidths=[1.5*cm, 4*cm, 2*cm, 2*cm, 5*cm])
    itinerary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (-1, 1), (-1, -1), 'LEFT'),
    ]))

    return [
        t, 
        Spacer(1, 0.5*cm),
        Paragraph("Itinerary", styles['Heading2']),
        itinerary_table,
        Spacer(1, 0.5*cm)
    ]

def create_pricing(quote, doc):
    total_price = quote.total_price
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

def create_notes(styles):
    notes = """
    1. This is a quote and is subject to availability at the time of quote.
    2. Please review all details and contact us to complete your quote or for any questions.
    3. A deposit of 20% is required to confirm your quote.
    4. Full payment is due 30 days before departure.
    5. Please ensure all traveler details match their passport exactly.
    6. Travel insurance is strongly recommended.
    """
    return [
        Paragraph("Notes", styles['Heading2']),
        Paragraph(notes, styles['BodyText']),
        Spacer(1, 0.5*cm)
    ]

def create_footer(styles, doc):
    return [
        HorizontalRule(doc.width),
        Paragraph("Thank you for choosing Travel In Style. We look forward to helping you create unforgettable memories.", styles['Italic']),
        Paragraph(f"Quote generated on {timezone.now().strftime('%d-%m-%Y at %H:%M')}. Valid for 14 days.", styles['Italic']),
    ]

def create_cruise_flyer_section(quote, styles):
    if quote.cruise_session.cruise.flyer_pdf:
        return [
            Paragraph("Cruise Flyer", styles['Heading2']),
            Paragraph("Please find the cruise flyer attached at the end of this document.", styles['BodyText']),
            Spacer(1, 0.5*cm)
        ]
    return []

def generate_quote_pdf(quote):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                leftMargin=1*cm, rightMargin=1*cm, 
                                topMargin=1*cm, bottomMargin=1*cm)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CenterBold', alignment=TA_CENTER, fontSize=16, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='RightAligned', alignment=TA_RIGHT, fontSize=10, fontName='Helvetica'))

        elements = []
        elements.extend(create_header(quote, styles, doc))
        elements.extend(create_client_info(quote, doc))
        elements.extend(create_journey_details(quote, styles, doc))
        elements.extend(create_pricing(quote, doc))
        elements.extend(create_cruise_flyer_section(quote, styles))
        elements.extend(create_notes(styles))
        elements.extend(create_footer(styles, doc))

        doc.build(elements)
        buffer.seek(0)

        if quote.cruise_session.cruise.flyer_pdf:
            output = PdfWriter()
            quote_pdf = PdfReader(buffer)
            for page in quote_pdf.pages:
                output.add_page(page)

            flyer_pdf = PdfReader(quote.cruise_session.cruise.flyer_pdf.path)
            for page in flyer_pdf.pages:
                output.add_page(page)

            buffer_final = BytesIO()
            output.write(buffer_final)
            buffer_final.seek(0)
            return buffer_final

        return buffer
    except Exception as e:
        logger.error(f"Error generating PDF for quote {quote.id}: {str(e)}")
        raise