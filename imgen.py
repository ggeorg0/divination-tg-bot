from typing import Union
import textwrap
import functools

from PIL import Image, ImageDraw, ImageFont


colorT = Union[tuple[int, int, int], str, None]

class QuoteImage:
    _width: int = 1280
    _height: int = 720
    _border_ratio: int
    _logo: Image
    _author_font: ImageFont.FreeTypeFont
    _title_font: ImageFont.FreeTypeFont
    _quote_font: ImageFont.FreeTypeFont
    _background_color: colorT = "white"
    _border_color: colorT = (199, 163, 143)
    _quote_color: colorT = "black"
    _author_color: colorT = "black"
    _title_color: colorT = "black"

    def __init__(self, 
                 color_theme: colorT=(199, 163, 143),
                 logo_path: str="images/logo4.png",
                 author_font_path: str="fonts/Ubuntu-Bold.ttf",
                 title_font_path: str="fonts/Ubuntu-Bold.ttf",
                 quote_font_path: str="georgiai.ttf",
                 border_ratio: int=22):
        self._logo = Image.open(logo_path)
        self._author_font = ImageFont.truetype(author_font_path, 42)
        self._title_font = ImageFont.truetype(title_font_path, 28)
        self._quote_font = ImageFont.truetype(quote_font_path, 42)
        self._border_ratio = border_ratio
        self._border_color = color_theme
    
    @functools.cached_property
    def _q_margin(self):
        """margin between lines of quote"""
        return self._quote_font.size / 2
    
    @functools.cached_property
    def _q_line_h(self):
        """height of line of quote in pixels"""
        _, top, _, bottom = self._quote_font.getbbox('AbcАбв')
        return bottom - top
    
    def _draw_wrapped_quote(self, 
                           text: str,
                           image_draw: ImageDraw.ImageDraw) -> None:
        lines = []
        for l in text.splitlines():
            lines += textwrap.wrap(l, width=45)

        if len(lines) > 5:
            lines = lines[:5]
            lines[-1] = lines[-1] + '...'

        # line with margin:
        wide_line = self._q_line_h + self._q_margin
        
        quote_height = wide_line * len(lines)
        quote_pos = (self._height - quote_height) / 2
        
        for i, line in enumerate(lines):
            line_w = image_draw.textlength(line, self._quote_font)
            pos = ( (self._width - line_w) / 2, quote_pos + wide_line * i )
            image_draw.text(
                xy=pos,
                text=line,
                font=self._quote_font,
                fill=self._quote_color)
            
    def _draw_author(self, text: str, image_draw: ImageDraw.ImageDraw):
        im_w, im_h, k = self._width, self._height, self._border_ratio
        text = textwrap.shorten(text, width=40, placeholder="...")
        author_w = image_draw.textlength(text, self._author_font)
        image_draw.text(
            ( (im_w - author_w) / 2, 2.5 * im_h / k ), 
            text=text, 
            fill='black',
            font=self._author_font, 
            align='center')
        
    def _draw_title(self, text: str, image_draw: ImageDraw.ImageDraw):
        im_w, im_h, k = self._width, self._height, self._border_ratio
        text = textwrap.shorten(text, width=72, placeholder="...")
        title_w = image_draw.textlength(text, self._title_font)
        image_draw.text(
            ((im_w - title_w) / 2, 5 * im_h / k ),
            text=text,
            fill='black',
            font=self._title_font,
            align='center')

    def _draw_borders(self, image_draw: ImageDraw.ImageDraw):
        im_w, im_h, k = self._width, self._height, self._border_ratio
        image_draw.rectangle(xy=(0, 0, im_w, im_h / k),
                             fill=self._border_color)
        image_draw.rectangle(xy=(0, (k - 1) * im_h / k, im_w, im_h),
                             fill=self._border_color)
        
    def _paste_logo(self, image: Image.Image):
        im_w, im_h, k = self._width, self._height, self._border_ratio
        image.paste(im=self._logo, 
            box=( (im_w - self._logo.width) // 2, 
            (k - 2) * im_h // k - self._logo.height ), 
            mask=self._logo
        )

    def make(self, author: str, title: str, quote: str):
        """Generate new picture of given quote"""
        image = Image.new(mode='RGB', 
                          size=(self._width, self._height), 
                          color=self._background_color)
        drawing = ImageDraw.Draw(image)
        self._draw_author(author, drawing)
        self._draw_title(title, drawing)
        self._draw_wrapped_quote(quote, drawing)
        self._draw_borders(drawing)
        self._paste_logo(image)
        return image
        

def test():
    image_gen = QuoteImage()

    message = "А Балда над морем опять шумит\nДа чертям веревкой грозит. А Балда над морем опять шумит\nДа чертям веревкой грозит\nА Балда над морем опять шумит Да чертям веревкой грозитА Балда над морем опять шумит\nДа чертям веревкой грозит"
    # message = "А Балда над морем опять шумит Да чертям веревкой грозит."
    author = "А. С. Пушкин А. С. Пушкин А. С. Пушкин Пушкин"
    title = "Сказка о попе и работнике его Балде Сказка о попе и работнике его Балде Балде"

    print(len(title))
    print(len(author))

    image = image_gen.make(author, title, message)
    image.show()
    image.save("test-image.png")

if __name__ == '__main__':
    test()


    
# width = 1280
# height = 720

# message = "А Балда над морем опять шумит\nДа чертям веревкой грозит."
# author = "Пушкин А. С."
# title = "Сказка о попе и работнике его Балде"
# fill_color = (199, 163, 143)

# k = 24

# img = Image.new('RGB', (width, height), color='white')
# _logo = Image.open('images/fake_logo.png')

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

# img.paste(_logo, ((width - _logo.width) // 2, (k - 2) * height // k - _logo.height), _logo)

# img.show()