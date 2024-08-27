import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, 
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

from ..models import Cruise, CruiseSession, CruiseCategoryPrice
from .styles import StyleSheet

from .flowables import HeaderFlowable
from ..utils import image_utils
from ..utils.pdf_utils import create_colored_box  # Add this import


class CruiseFlyerGenerator:
    def __init__(self, cruise_id):
        self.cruise = Cruise.objects.get(id=cruise_id)
        self.sessions = CruiseSession.objects.filter(cruise=self.cruise).order_by('start_date')
        self.prices = CruiseCategoryPrice.objects.filter(cruise=self.cruise).select_related('category')
        self.styles = StyleSheet().styles
        self.main_color = colors.HexColor("#007a99")
        self.light_color = colors.HexColor("#e6f3f7")
        self.width, self.height = A4

    def generate(self):
        flyer_dir = os.path.join(settings.MEDIA_ROOT, 'flyers')
        os.makedirs(flyer_dir, exist_ok=True)
        output_path = os.path.join(flyer_dir, f'{self.cruise.name}_flyer.pdf')


        def on_page(canvas, doc):
            if doc.page == 1:
                header = HeaderFlowable(self.cruise)  # Define header here
                header.canv = canvas
                header.wrap(doc.width, doc.topMargin)
                header.draw()


                canvas.saveState()
                # Add any other page-level drawings here
                canvas.restoreState()


        page_template = PageTemplate(
            id='normal', 
            frames=[Frame(0, 0, self.width, self.height, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)],
            onPage=on_page
        )

        # Use BaseDocTemplate instead of SimpleDocTemplate
        doc = BaseDocTemplate(output_path, pagesize=A4, rightMargin=0, leftMargin=0, topMargin=0, bottomMargin=0)
        doc.addPageTemplates(page_template)

        self._register_fonts()
        content = self._build_content()
        doc.build(content)
        return output_path

    def _register_fonts(self):
        pdfmetrics.registerFont(TTFont('Roboto', os.path.join(settings.BASE_DIR, 'fonts', 'Roboto-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', os.path.join(settings.BASE_DIR, 'fonts', 'Roboto-Bold.ttf')))

    def _build_content(self):
        content = []
        content.extend(self._header_section())
        content.extend(self._cruise_details_section())
        content.extend(self._features_section())
        content.extend(self._price_and_image_section())
        content.extend(self._itinerary_section())
        content.extend(self._dates_and_prices_section())
        content.append(PageBreak())
        content.extend(self._included_services_section())
        content.extend(self._not_included_section())
        content.extend(self._footer_section())
        return content

    def _header_section(self):
        return [
            HeaderFlowable(self.cruise),
            Spacer(1, 0.3*inch)
        ]
    

    def _cruise_details_section(self):
        if self.sessions.exists():
            first_session = self.sessions.first()
            duration = (first_session.end_date - first_session.start_date).days + 1
            date_range = f"{first_session.start_date.strftime('%d.%m.')} - {first_session.end_date.strftime('%d.%m.%Y')}"
        else:
            duration = "N/A"
            date_range = "N/A"

        return [
            Paragraph(f"{self.cruise.name.upper()}", ParagraphStyle('CruiseTitle', parent=self.styles['CruiseTitle'], leftIndent=0.5*inch, rightIndent=0.5*inch)),
            Paragraph(f"{getattr(self.cruise, 'cruise_type', 'Cruise')} | {duration} Tage | {date_range}", ParagraphStyle('CruiseSubtitle', parent=self.styles['CruiseSubtitle'], leftIndent=0.5*inch, rightIndent=0.5*inch)),
            Spacer(1, 0.2*inch)
        ]

    def _features_section(self):
        features = [
            f"{self.sessions.count()} ABFAHRTEN im {self.sessions.first().start_date.strftime('%B %Y')}" if self.sessions.exists() else "ABFAHRTEN N/A",
            "INKL. BUSTRANSFERS",
            "ALLES INKLUSIVE an Bord",
            "BELIEBTES FLUSSSCHIFF"
        ]
        feature_table_data = [[create_colored_box(feature, A4[0], 0.5*inch, self.main_color, colors.white)] for feature in features]
        feature_table = Table(feature_table_data, colWidths=[A4[0]])
        feature_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        return [feature_table, Spacer(1, 0.3*inch)]

    def _price_and_image_section(self):
        min_price = min(price.price for price in self.prices) if self.prices else "N/A"
        price_box = create_colored_box(f"ab {min_price} € p.P.", A4[0], inch, self.main_color, colors.white)
        
        if self.cruise.image:
            img = Image(self.cruise.image.path, width=A4[0], height=A4[0] * 0.5625)
        elif self.cruise.image_url:
            img = Image(self.cruise.image_url, width=A4[0], height=A4[0] * 0.5625)
        else:
            img = Image("/api/placeholder/400/300", width=A4[0], height=A4[0] * 0.5625)
        
        return [price_box, Spacer(1, 0.3*inch), img, Spacer(1, 0.3*inch)]

    def _itinerary_section(self):

        content = [Paragraph("REISEVERLAUF", ParagraphStyle('FlyerHeading', parent=self.styles['FlyerHeading'], leftIndent=0.5*inch, rightIndent=0.5*inch))]
        itinerary = [['TAG', 'HAFEN', 'ANKUNFT', 'ABFAHRT']]
        # Add actual itinerary data here if available
        # For now, we'll just add a placeholder row
        itinerary.append(['1', 'Placeholder Port', '00:00', '00:00'])
        
        itinerary_table = Table(itinerary, colWidths=[0.7*inch, 3*inch, 1.5*inch, 1.5*inch])
        itinerary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.main_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), self.light_color),
            ('GRID', (0,0), (-1,-1), 1, colors.white)
        ]))
        content.append(itinerary_table)
        content.append(Spacer(1, 0.3*inch))
        return content
    

    def _dates_and_prices_section(self):
        content = []
        content.append(Paragraph("REISETERMINE", ParagraphStyle('FlyerHeading', parent=self.styles['FlyerHeading'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        dates = [f"{session.start_date.strftime('%d.%m.')} - {session.end_date.strftime('%d.%m.%Y')}" for session in self.sessions]
        date_table = Table([[date] for date in dates], colWidths=[A4[0] - inch])
        date_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.light_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Roboto'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        content.append(date_table)
        content.append(Spacer(1, 0.3*inch))

        content.append(Paragraph("PREISE", ParagraphStyle('FlyerHeading', parent=self.styles['FlyerHeading'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        price_data = [['DECK', 'AUSSENKABINE', 'PREIS P.P.']]
        price_data.extend([[price.category.name, getattr(price.category, 'description', 'Standard'), f"{price.price} €"] for price in self.prices])
        price_table = Table(price_data, colWidths=[2*inch, 3*inch, 2*inch])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.main_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), self.light_color),
            ('GRID', (0,0), (-1,-1), 1, colors.white)
        ]))
        content.append(price_table)
        content.append(Spacer(1, 0.3*inch))
        return content

    def _included_services_section(self):
        content = []
        content.append(Paragraph("IM PREIS INBEGRIFFEN", ParagraphStyle('FlyerHeading', parent=self.styles['FlyerHeading'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        included_services = [
            "• Hin- und Rückfahrt mit dem Bus von Luxemburg",
            "• Kreuzfahrt nach Fahrplan",
            "• Unterkunft in gebuchter Kategorie",
            "• Vollpension mit Frühstücksbuffet, Mittagsessen, Abendessen",
            "• Ganztags hochwertige, kalte und warme nicht alkoholische Getränke",
            "• High Tea: einmalig pro Reise",
            "• Täglich frisch gefüllte Mini-Bar",
            "• Herzlich Willkommen mit einem Begrüssungssekt",
            "• Ausgesuchte Beauty-Produkte von RITUALS",
            "• Freies WLAN an Bord",
            "• Trinkgelder für die gesamte Crew",
            "• Hafengebühren und Steuern"
        ]
        for service in included_services:
            content.append(Paragraph(service, ParagraphStyle('FlyerBody', parent=self.styles['FlyerBody'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        content.append(Spacer(1, 0.2*inch))
        return content

    def _not_included_section(self):
        content = []
        content.append(Paragraph("NICHT IM PREIS INBEGRIFFEN", ParagraphStyle('FlyerHeading', parent=self.styles['FlyerHeading'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        content.append(Paragraph("• Ausflüge - Lokale Transfers - Persönliche Ausgaben - Reiseversicherung", ParagraphStyle('FlyerBody', parent=self.styles['FlyerBody'], leftIndent=0.5*inch, rightIndent=0.5*inch)))
        content.append(Spacer(1, 0.2*inch))
        return content

    def _footer_section(self):
        footer_text = """
        Wenden Sie sich an Travel In Style / Cruise Selection
        info@travelinstyle.lu | tel. (+352) 2877 55 31 | www.fluss.lu
        Die Preise verstehen sich in Euro bei Doppelbelegung. Hafengebühren, Mehrwertsteuer und Steuern sind inbegriffen.
        Routen und Preise sind freibleibend und können von der Reederei jederzeit ohne vorherige Ankündigung geändert oder zurückgezogen werden, solange eine Reservierung nicht endgültig ist. Es gelten die Geschäftsbedingungen der Reederei.
        """
        return [Paragraph(footer_text, ParagraphStyle('FlyerSmall', parent=self.styles['FlyerSmall'], leftIndent=0.5*inch, rightIndent=0.5*inch))]

    