from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class StyleSheet:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='FlyerTitle', fontName='Roboto-Bold', fontSize=28, leading=34, alignment=TA_CENTER, textColor=colors.white))
        self.styles.add(ParagraphStyle(name='FlyerSubtitle', fontName='Roboto', fontSize=16, leading=20, alignment=TA_CENTER, textColor=colors.white))
        self.styles.add(ParagraphStyle(name='CruiseTitle', fontName='Roboto-Bold', fontSize=24, leading=28, alignment=TA_LEFT, textColor=colors.HexColor("#007a99")))
        self.styles.add(ParagraphStyle(name='CruiseSubtitle', fontName='Roboto', fontSize=14, leading=18, alignment=TA_LEFT, textColor=colors.HexColor("#007a99")))
        self.styles.add(ParagraphStyle(name='FlyerHeading', fontName='Roboto-Bold', fontSize=16, leading=20, textColor=colors.HexColor("#007a99")))
        self.styles.add(ParagraphStyle(name='FlyerBody', fontName='Roboto', fontSize=11, leading=14))
        self.styles.add(ParagraphStyle(name='FlyerSmall', fontName='Roboto', fontSize=9, leading=11))
        self.styles.add(ParagraphStyle(name='FlyerHighlight', fontName='Roboto-Bold', fontSize=14, leading=18, textColor=colors.white))