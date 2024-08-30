#cruises/flyer/generator.py

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
        self.header_height = self.height * 0.45  # Match the HeaderFlowable height

    def generate(self):
        flyer_dir = os.path.join(settings.MEDIA_ROOT, 'flyers')
        os.makedirs(flyer_dir, exist_ok=True)
        output_path = os.path.join(flyer_dir, f'{self.cruise.name}_flyer.pdf')

        def on_page(canvas, doc):
            header = HeaderFlowable(self.cruise)
            header.canv = canvas
            header.wrap(doc.width, self.header_height)
            header.draw()

        # Adjust the frame to start after the header
        content_height = self.height - self.header_height - inch

        page_template = PageTemplate(
            id='normal',
            frames=[Frame(0.5*inch, 0.5*inch, self.width-inch, content_height, id='normal')],
            onPage=on_page
        )

        doc = BaseDocTemplate(output_path, pagesize=A4)
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
        content.extend(self._dates_and_prices_section())
        content.extend(self._included_services_section())
        content.extend(self._not_included_section())
        content.extend(self._cruise_description_section())
        content.extend(self._ship_details_section())
        content.extend(self._footer_section())
        return content

    def _header_section(self):
        return [HeaderFlowable(self.cruise), Spacer(1, 0.3*inch)]
    
    def _cruise_details_section(self):
        duration = self.cruise.duration or "N/A"
        if self.sessions.exists():
            first_session = self.sessions.first()
            date_range = f"{first_session.start_date.strftime('%d.%m.')} - {first_session.end_date.strftime('%d.%m.%Y')}"
        else:
            date_range = "N/A"

        return [
            Paragraph(f"{self.cruise.name.upper()}", self.styles['FlyerTitle']),
            Paragraph(f"{self.cruise.company.name} | {duration} Tage | {self.cruise.cruise_type}", self.styles['FlyerSubtitle']),
            Spacer(1, 0.2*inch)
        ]

    def _features_section(self):
        duration = self.cruise.duration or "N/A"

        features = [
            f"{self.sessions.count()} REISETERMINE",
            f"{duration} NÄCHTE",
            "INKL. BUSTRANSFERS",
            "ALLES INKLUSIVE an Bord",
            "1 KOSTENLOSER AUSFLUG",
            "BELIEBTES FLUSSSCHIFF"
        ]
        feature_boxes = [create_colored_box(feature, self.width-inch, 0.3*inch, self.main_color, colors.white) for feature in features]
        return feature_boxes + [Spacer(1, 0.3*inch)]

#    def _itinerary_section(self):
#        content = []
#        content.append(Paragraph("IHR AUFENTHALT", self.styles['FlyerHeading1']))
#        
#        itinerary_data = [['TAG', 'HAFEN']]
#        
#        if not self.sessions.exists():
#            itinerary_data.append(['1', 'Placeholder Port'])
#        else:
#            for i, session in enumerate(self.sessions, start=1):
#                itinerary_data.append([
#                    f"Tag {i}",
#                    session.description or session.cruise.name
#                ])

        table = Table(itinerary_data, colWidths=[inch, 5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.main_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Roboto-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), self.light_color),
            ('GRID', (0,0), (-1,-1), 1, colors.white)
        ]))
        
        content.append(table)
        content.append(Spacer(1, 0.2*inch))
        return content

    def _dates_and_prices_section(self):
        content = []
        content.append(Paragraph("REISETERMINE", self.styles['FlyerHeading1']))
        
        dates = [f"{session.start_date.strftime('%d.%m.')} - {session.end_date.strftime('%d.%m.%Y')}" for session in self.sessions]
        date_table = Table([[date] for date in dates], colWidths=[self.width - 1.5*inch])
        date_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.light_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Roboto-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        content.append(date_table)
        content.append(Spacer(1, 0.2*inch))

        content.append(Paragraph("PREISE", self.styles['FlyerHeading1']))
        price_data = [['DECK/LAGE', 'AUSSENKABINE', 'PREIS P.P.']]
        price_data.extend([[price.category.name, getattr(price.category, 'description', 'Standard'), f"{price.price} €"] for price in self.prices])
        price_table = Table(price_data, colWidths=[2.5*inch, 3*inch, 2*inch])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.main_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Roboto-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,1), (-1,-1), self.light_color),
            ('GRID', (0,0), (-1,-1), 1, colors.white)
        ]))
        content.append(price_table)
        content.append(Spacer(1, 0.3*inch))
        return content

    def _included_services_section(self):
        content = []
        content.append(Paragraph("IM PREIS INBEGRIFFEN", self.styles['Heading2']))
        included_services = [
            "• Hin- und Rückfahrt mit dem Bus von Luxemburg",
            "• Unterkunft in gebuchter Kategorie",
            "• Panorama-Bustour am zweiten Tag",
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
            content.append(Paragraph(service, self.styles['BodyText']))
        content.append(Spacer(1, 0.2*inch))
        return content

    def _not_included_section(self):
        content = []
        content.append(Paragraph("NICHT IM PREIS INBEGRIFFEN", self.styles['Heading2']))
        content.append(Paragraph("• Ausflüge - Lokale Transfers - Persönliche Ausgaben - Reiseversicherung", self.styles['BodyText']))
        content.append(Spacer(1, 0.2*inch))
        return content

    def _cruise_description_section(self):
        content = []
        content.append(Paragraph(self.cruise.name, self.styles['FlyerHeading1']))
        content.append(Paragraph(self.cruise.description, self.styles['FlyerBodyText']))
        content.append(Spacer(1, 0.3*inch))
        return content

    def _ship_details_section(self):
        content = []
        content.append(Paragraph("SCHIFFSDATEN", self.styles['FlyerHeading1']))
        ship_data = [
            ["Passagiere", "152"],
            ["Crew", "36"],
            ["Aussenkabinen", "76"],
            ["Jungfernfahrt", "2005 - Renov. Winter 2022/23"],
            ["Länge x Breite", "110 m x 11 m"]
        ]
        ship_table = Table(ship_data, colWidths=[2.5*inch, 5*inch])
        ship_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Roboto-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Roboto'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        content.append(ship_table)
        content.append(Spacer(1, 0.3*inch))
        return content

#    def _destination_description_section(self):
#        content = []
#        content.append(Paragraph(self.cruise.destination, self.styles['FlyerHeading1']))
#        content.append(Paragraph(self.cruise.destination_description, self.styles['FlyerBodyText']))
#        content.append(Spacer(1, 0.2*inch))
#        return content

    def _footer_section(self):
        footer_text = """
        Wenden Sie sich an Travel In Style / Cruise Selection
        info@travelinstyle.lu | tel. (+352) 2877 55 31 | www.fluss.lu
        Die Preise verstehen sich in Euro bei Doppelbelegung. Hafengebühren, Mehrwertsteuer und Steuern sind inbegriffen.
        Routen und Preise sind freibleibend und können von der Reederei jederzeit ohne vorherige Ankündigung geändert oder zurückgezogen werden, solange eine Reservierung nicht endgültig ist. Es gelten die Geschäftsbedingungen der Reederei.
        """
        return [Paragraph(footer_text, self.styles['FlyerFooter'])]