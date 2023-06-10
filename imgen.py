from typing import Union

from PIL import Image, ImageDraw, ImageFont


colorT = Union[tuple[int, int, int], str, None]

class QuoteImage:
    _width: int = 1280
    _height: int = 720
    border_color: colorT = (199, 163, 143)
    background_color: colorT = "white"
    ratio: int = 22
    logo_path: str = "images/fake_logo.png"
    logo: Image
    _author_font: ImageFont
    _title_font: ImageFont
    _quote_font: ImageFont

    def __init__(self, 
                 color_theme: colorT=(199, 163, 143),
                 logo_path: str="images/logo.png",
                 ratio: int=24):
        # TODO: self attributes assignment
        self.logo = Image.open(self.logo_path)
        self._author_font = ImageFont.truetype('fonts/Ubuntu-Bold.ttf', 42)
        self._title_font = ImageFont.truetype('fonts/Ubuntu-Bold.ttf', 28)
        self._quote_font = ImageFont.truetype('georgiai.ttf', 48)

    def _text_size(self, image_draw: ImageDraw, text: str, font: ImageFont):
        _, _, text_width, text_height = image_draw.textbbox(
            xy=(0, 0),
            text=text,
            font=font
        )
        return text_width, text_height

    def make(self, author: str, title: str, quote: str):
        k = self.ratio
        im_w = self._width
        im_h = self._height
        image = Image.new(mode='RGB', 
                          size=(im_w, im_h), 
                          color=self.background_color)
        
        drawing = ImageDraw.Draw(image)
        author_w, author_h = self._text_size(drawing, author, self._author_font)
        title_w, title_h = self._text_size(drawing, title, self._title_font)
        quote_w, quote_h = self._text_size(drawing, quote, self._quote_font)
        drawing.text(((im_w - author_w) / 2, 2.5 * im_h / k), 
                     text=author, 
                     fill='black',
                     font=self._author_font, 
                     align='center')
        drawing.text(((im_w - title_w) / 2, 5 * im_h / k),
                     text=title,
                     fill='black',
                     font=self._title_font,
                     align='center')
        drawing.text(((im_w - quote_w) / 2, (im_h - quote_h) / 2), 
                     text=quote,
                     fill='black',
                     font=self._quote_font, 
                     align='center')
        drawing.rectangle(xy=(0, 0, im_w, im_h / k),
                          fill=self.border_color)
        drawing.rectangle(xy=(0, (k - 1) * im_h / k, im_w, im_h),
                          fill=self.border_color)
        image.paste(im=self.logo, 
                    box=( (im_w - self.logo.width) // 2, 
                          (k - 2) * im_h // k - self.logo.height ), 
                    mask=self.logo)
        return image
        
        
image_gen = QuoteImage()

message = "А Балда над морем опять шумит\nДа чертям веревкой грозит."
author = "А. С. Пушкин"
title = "Сказка о попе и работнике его Балде"

image = image_gen.make(author, title, message)
image.show()
image.save("test-image.png")



    






# width = 1280
# height = 720

# message = "А Балда над морем опять шумит\nДа чертям веревкой грозит."
# author = "Пушкин А. С."
# title = "Сказка о попе и работнике его Балде"
# fill_color = (199, 163, 143)

# k = 24

# img = Image.new('RGB', (width, height), color='white')
# logo = Image.open('images/fake_logo.png')

# imgDraw = ImageDraw.drawing(img)

# # font = ImageFont.truetype(font='Ubuntu-Bold.ttf')
# _author_font = ImageFont.truetype(font='fonts/Ubuntu-Bold.ttf', size=42)
# _title_font = ImageFont.truetype(font='fonts/Ubuntu-Bold.ttf', size=26)
# _quote_font = ImageFont.truetype(font='georgiai.ttf', size=48)

# # ImageFont.FreeTypeFont(font='georgia.ttf', size=48)

# _, _, quote_w, quote_h = imgDraw.textbbox((0, 0), text=message, font=_quote_font)
# _, _, author_w, author_h = imgDraw.textbbox((0, 0), text=author, font=_author_font)
# _, _, title_w, title_h = imgDraw.textbbox((0, 0), text=title, font=_title_font)

# imgDraw.text(((width - author_w) / 2, 3 * height / k), 
#              text=author, 
#              fill='black',
#              font=_author_font, 
#              align='center')

# imgDraw.text(((width - quote_w) / 2, (height - quote_h) / 2), 
#              text=message,
#              fill='black',
#              font=_quote_font, 
#              align='center')

# imgDraw.text(((width - title_w) / 2, 5 * height / k),
#              text=title,
#              fill='black',
#              font=_title_font,
#              align='center')



# imgDraw.rectangle(xy=(0, 0, width, height / k),
#                   fill=fill_color)
# imgDraw.rectangle(xy=(0, (k - 1) * height / k, width, height),
#                   fill=fill_color)

# img.paste(logo, ((width - logo.width) // 2, (k - 2) * height // k - logo.height), logo)

# img.show()