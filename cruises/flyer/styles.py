from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class StyleSheet:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='FlyerHeading1',
            fontName='Roboto-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#007a99"),
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='FlyerHeading2',
            fontName='Roboto-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#007a99"),
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='FlyerBodyText',
            fontName='Roboto',
            fontSize=11,
            leading=14,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='FlyerFooter',
            fontName='Roboto',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='FlyerTitle',
            fontName='Roboto-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#007a99"),
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='FlyerSubtitle',
            fontName='Roboto',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#007a99"),
            spaceAfter=10
        ))