from typing import Union
import textwrap
import functools

from PIL import Image, ImageDraw, ImageFont

QUOTE_LINES = 6
QUOTE_WIDTH = 60

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
                 color_theme: colorT=(143, 143, 143),
                 logo_path: str="images/logo_qr.png",
                 author_font_path: str="fonts/Ubuntu-Bold.ttf",
                 title_font_path: str="fonts/Ubuntu-Bold.ttf",
                 quote_font_path: str="fonts/georgiai.ttf",
                 border_ratio: int=22):
        self._logo = Image.open(logo_path)
        self._author_font = ImageFont.truetype(author_font_path, 42)
        self._title_font = ImageFont.truetype(title_font_path, 28)
        self._quote_font = ImageFont.truetype(quote_font_path, 32)
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
            lines += textwrap.wrap(l, width=QUOTE_WIDTH)

        if len(lines) > QUOTE_LINES:
            lines = lines[:QUOTE_LINES]
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
        text = textwrap.shorten(text, width=QUOTE_WIDTH, placeholder="...")
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
            (k - 2) * im_h // k - self._logo.height), 
            mask=self._logo
        )

    def make(self, author: str, title: str, quote: str) -> Image.Image:
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
        