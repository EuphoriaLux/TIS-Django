from reportlab.platypus import Flowable
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing
from ..utils.image_utils import get_image_path
import os

class HeaderFlowable(Flowable):
    def __init__(self, cruise):
        Flowable.__init__(self)
        self.page_width, self.page_height = A4
        self.header_height = self.page_height / 3  # Set header height to 1/3 of the page height
        self.cruise = cruise

    def wrap(self, *args):
        return self.page_width, self.header_height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        # Debug: Fill the header with a solid color to ensure visibility
        canvas.setFillColor(colors.HexColor("#CCCCCC"))  # Light gray for visibility
        canvas.rect(0, self.page_height - self.header_height, self.page_width, self.header_height, fill=1, stroke=0)

        self._draw_background(canvas)
        self._draw_logos(canvas)
        self._draw_qr_code(canvas)
        self._draw_pricing_circle(canvas)
        self._draw_zubringerdienst(canvas)
        
        canvas.restoreState()

    def _draw_background(self, canvas):
        bg_image_path = get_image_path('hero-cruise.jpg')
        if bg_image_path and os.path.exists(bg_image_path):
            canvas.drawImage(bg_image_path, 0, self.page_height - self.header_height, self.page_width, self.header_height, mask='auto')
        else:
            # Set a solid color background if image is not available
            canvas.setFillColor(colors.HexColor("#007a99"))
            canvas.rect(0, self.page_height - self.header_height, self.page_width, self.header_height, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#007a99"))
        canvas.setFillAlpha(0.3)
        canvas.rect(0, self.page_height - self.header_height, self.page_width, self.header_height, fill=1, stroke=0)
        canvas.setFillAlpha(1)

    def _draw_logos(self, canvas):
        fluss_logo_path = get_image_path('fluss_lu.png')
        if fluss_logo_path:
            canvas.drawImage(fluss_logo_path, 0.5*inch, self.page_height - 1.2*inch, width=1.5*inch, height=0.6*inch, mask='auto')
        else:
            canvas.setFont("Roboto-Bold", 24)
            canvas.setFillColor(colors.white)
            canvas.drawString(0.5*inch, self.page_height - 1*inch, "FLUSS.LU")
        
        canvas.setFont("Roboto-Bold", 12)
        canvas.setFillColor(colors.white)
        canvas.drawString(0.5*inch, self.page_height - 1.5*inch, "AUF ZU NEUEN HORIZONTEN")

        wort_logo_path = get_image_path('leserreisen_luxemburger_wort.png')
        if wort_logo_path:
            canvas.drawImage(wort_logo_path, 2.5*inch, self.page_height - 1.2*inch, width=2.0*inch, height=0.6*inch, mask='auto')

        viva_logo_path = get_image_path('viva_logo.jpg')
        if viva_logo_path:
            canvas.drawImage(viva_logo_path, 4*inch, self.page_height - 1.2*inch, width=2*inch, height=0.6*inch, mask='auto')

    def _draw_qr_code(self, canvas):
        # Create the QR code
        qr_code = qr.QrCodeWidget('https://fluss.lu')
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]

        # Set the size of the QR code
        size = 50  # Size in points

        # Set the position of the QR code
        x_position = self.page_width - 1.75 * inch
        y_position = self.page_height - 1.35 * inch

        # Draw the QR code with proper scaling
        d = Drawing(size, size, transform=[size/width, 0, 0, size/height, 0, 0])
        d.add(qr_code)  # Add the QR code widget to the drawing
        renderPDF.draw(d, canvas, x_position, y_position)

    def _draw_pricing_circle(self, canvas):
        circle_x, circle_y = 2*inch, self.page_height - (self.header_height - 0.8*inch)
        circle_radius = 0.7*inch
        canvas.setFillColor(colors.HexColor("#007a99"))
        canvas.circle(circle_x, circle_y, circle_radius, fill=1, stroke=0)
        
        canvas.setFillColor(colors.white)
        canvas.setFont("Roboto-Bold", 20)
        canvas.drawCentredString(circle_x, circle_y + 0.2*inch, "ab")
        canvas.setFont("Roboto-Bold", 24)
        canvas.drawCentredString(circle_x, circle_y - 0.1*inch, f"{self.cruise.min_price()} €")
        canvas.setFont("Roboto", 14)
        canvas.drawCentredString(circle_x, circle_y - 0.3*inch, "p.P.")

    def _draw_zubringerdienst(self, canvas):
        canvas.setFont("Roboto-Bold", 12)
        canvas.setFillColor(colors.white)
        
        # Adjusted positions for better alignment
        x_position = 3.25 * inch
        y_start = self.page_height - (self.header_height - 1.3 * inch)
        line_spacing = 0.2 * inch  # Space between lines
        
        canvas.drawString(x_position, y_start, "GRATIS")
        canvas.drawString(x_position, y_start - line_spacing, "ZUBRINGERDIENST*")
        
        canvas.setFont("Roboto", 10)
        canvas.drawString(x_position, y_start - 2 * line_spacing, "AB/BIS WOHNORT FÜR")
        canvas.drawString(x_position, y_start - 3 * line_spacing, "LUXEMBURGER-WORT-")
        canvas.drawString(x_position, y_start - 4 * line_spacing, "ABONNENTEN")
