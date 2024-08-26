from reportlab.graphics.shapes import Drawing, Rect, String

def create_colored_box(text, width, height, bg_color, text_color):
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=bg_color, strokeColor=None))
    drawing.add(String(width/2, height/2, text, fontSize=14, fontName="Roboto-Bold", 
                       fillColor=text_color, textAnchor='middle'))
    return drawing