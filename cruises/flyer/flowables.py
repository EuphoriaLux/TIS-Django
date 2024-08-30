#cruises/flyer/flowables.py
from reportlab.lib import colors

from reportlab.lib.units import inch
from reportlab.platypus import Flowable
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect,Group
from ..utils.image_utils import get_image_path
import os


class HeaderFlowable(Flowable):
    def __init__(self, cruise):
        Flowable.__init__(self)
        self.page_width, self.page_height = A4
        self.header_height = self.page_height * 0.45
        self.cruise = cruise
        self.main_color = colors.HexColor("#007a99")
        self.light_color = colors.HexColor("#e6f3f7")

    def wrap(self, *args):
        return self.page_width, self.header_height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        self._draw_background(canvas)
        self._draw_logos(canvas)
        self._draw_cruise_info(canvas)
        self._draw_pricing_circle(canvas)
        self._draw_qr_code(canvas)

    def _draw_background(self, canvas):
        bg_image_path = self.cruise.image.path if self.cruise.image else (self.cruise.image_url or get_image_path('hero-cruise.jpg'))
        
        try:
            canvas.drawImage(bg_image_path, 0, self.page_height - self.header_height, 
                             self.page_width, self.header_height, mask='auto')
        except:
            canvas.setFillColor(self.main_color)
            canvas.rect(0, self.page_height - self.header_height, self.page_width, self.header_height, fill=1, stroke=0)
        
        # Add overlay gradient
        canvas.saveState()
        p = canvas.beginPath()
        p.moveTo(0, self.page_height - self.header_height)
        p.lineTo(self.page_width, self.page_height - self.header_height)
        p.lineTo(self.page_width, self.page_height)
        p.lineTo(0, self.page_height)
        canvas.clipPath(p, stroke=0)
        canvas.setFillAlpha(0.7)
        
        # Create a list of colors for the gradient
        gradient_colors = [colors.Color(0,0,0,0), colors.Color(0,0,0,1)]
        canvas.linearGradient(0, self.page_height - self.header_height, self.page_width, self.page_height, 
                              gradient_colors)
        canvas.restoreState()

    def _draw_logos(self, canvas):
        # Draw FLUSS.LU logo
        fluss_logo_path = get_image_path('fluss_lu.png')
        if fluss_logo_path:
            canvas.drawImage(fluss_logo_path, 0.5*inch, self.page_height - 1*inch, width=1.5*inch, height=0.6*inch, mask='auto')
        else:
            canvas.setFont("Roboto-Bold", 24)
            canvas.setFillColor(colors.white)
            canvas.drawString(0.5*inch, self.page_height - 0.8*inch, "FLUSS.LU")
        
        canvas.setFont("Roboto-Bold", 12)
        canvas.setFillColor(colors.white)
        canvas.drawString(0.5*inch, self.page_height - 1.3*inch, "AUF ZU NEUEN HORIZONTEN")

        # Draw other logos (Luxemburger Wort, VIVA)
        wort_logo_path = get_image_path('leserreisen_luxemburger_wort.png')
        if wort_logo_path:
            canvas.drawImage(wort_logo_path, self.page_width - 4.5*inch, self.page_height - 1*inch, width=2*inch, height=0.8*inch, mask='auto')

        viva_logo_path = get_image_path(f'{self.cruise.company.name.lower()}_logo.png')
        if viva_logo_path:
            canvas.drawImage(viva_logo_path, self.page_width - 2*inch, self.page_height - 1*inch, width=1.5*inch, height=0.6*inch, mask='auto')

    def _draw_cruise_info(self, canvas):
        canvas.setFont("Roboto-Bold", 48)
        canvas.setFillColor(colors.white)
        canvas.drawString(0.5*inch, self.page_height - 3*inch, self.cruise.name.upper())
        
        canvas.setFont("Roboto", 24)
        first_session = self.cruise.sessions.first()
        if first_session:
            duration = (first_session.end_date - first_session.start_date).days + 1
            info_string = f"{self.cruise.company.name} | {duration} Tage | {self.cruise.cruise_type}"
        else:
            info_string = f"{self.cruise.company.name} | N/A | {self.cruise.cruise_type}"
        
        canvas.drawString(0.5*inch, self.page_height - 3.5*inch, info_string)

    def _draw_pricing_circle(self, canvas):
        circle_x, circle_y = self.page_width - 2*inch, self.page_height - 3.5*inch
        circle_radius = 1*inch
        
        # Draw outer circle
        canvas.setFillColor(self.main_color)
        canvas.circle(circle_x, circle_y, circle_radius, fill=1, stroke=0)
        
        # Draw inner circle
        canvas.setFillColor(colors.white)
        canvas.circle(circle_x, circle_y, circle_radius - 0.1*inch, fill=1, stroke=0)
        
        canvas.setFillColor(self.main_color)
        canvas.setFont("Roboto-Bold", 24)
        canvas.drawCentredString(circle_x, circle_y + 0.4*inch, "ab")
        canvas.setFont("Roboto-Bold", 28)
        canvas.drawCentredString(circle_x, circle_y, f"{self.cruise.min_price()} €")
        canvas.setFont("Roboto", 18)
        canvas.drawCentredString(circle_x, circle_y - 0.4*inch, "p.P.")

    def _draw_qr_code(self, canvas):
        qr_code = qr.QrCodeWidget('https://fluss.lu')
        qr_code.barWidth = 5
        qr_code.barHeight = 5
        qr_code.qrVersion = 5

        qr_size = 1.5 * inch
        x_position = self.page_width - qr_size - 0.3 * inch
        y_position = self.page_height - 1.8 * inch

        # Draw white background with black border
        canvas.setFillColor(colors.white)
        canvas.setStrokeColor(colors.black)
        canvas.rect(x_position, y_position, qr_size, qr_size, fill=1, stroke=1)

        # Create a drawing for the QR code
        bounds = qr_code.getBounds()
        qr_width = bounds[2] - bounds[0]
        qr_height = bounds[3] - bounds[1]
        
        d = Drawing(qr_size, qr_size)
        d.add(qr_code)
        
        # Scale the drawing to fit the desired size
        scale_factor = qr_size / max(qr_width, qr_height)
        d.scale(scale_factor, scale_factor)
        
        # Draw the QR code onto the canvas
        renderPDF.draw(d, canvas, x_position, y_position)
