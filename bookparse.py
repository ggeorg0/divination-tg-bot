import logging
from typing import List, Optional

LINE_SYMBOLS = 55
PAGE_SYMBOLS = 50

INSERT_PAGES_QUERY = """INSERT INTO page (book_id, num, content)
VALUES (%s, %s, %s)
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Book:
    author: str
    title: str
    info: str
    pages: Optional[List[str]]

    def __init__(self, 
                 author: str = "",
                 title: str = "", 
                 info: str = "", 
                 text: Optional[str] = None):
        self.title = title or "NULL"
        self.author = author or "NULL"
        self.info = info or "NULL"
        if text:
            self.pages = self.pages_from_text(text)
        else:
            self.pages = text       # None

    def __str__(self) -> str:
        return f"'{self.title}', '{self.author}', '{self.info}'"

    def pages_from_text(self, raw_text: str) -> List[str]:
        """Split text by pages with `LINE_SYMBOLS` on a line
        and `PAGE_SYMBOLS` lines on a page"""
        paragraphs = [p for p in raw_text.split('\n') if p]
        lines = [""]
        for p in paragraphs:
            words = p.split()
            self._add_lines(lines, words)
        pages =[[]]
        for index, line in enumerate(lines):
            pages[-1].append(line)
            if (index + 1) % PAGE_SYMBOLS == 0:
                pages.append([])
         # list of lines to one string object for each page
        pages = ["\n".join(p) for p in pages]
        return pages

    def _add_lines(self, lines: List[str], words: List[str]) -> None:
        """Adds words to last line if it's length < `LINE_SYMBOLS`, 
        otherwise, moves the words to a new line.\n 
        Мodifies `lines` argument"""
        for w in words:
            if len(lines[-1]) + len(w) < LINE_SYMBOLS:
                if lines[-1]:
                    lines[-1] = lines[-1] + " "
                lines[-1] = lines[-1] + w 
            else:
                lines.append(w)
        lines.append("") # new line at the end of the paragraph


class BookReader:

    @staticmethod
    def read_book(file_path: str) -> Book:
        """Reads book from `file_path`. 
        First 4 lines must be formatted as follows:\n
        ```
        Author.
        The Title.
        \n
        Some information about the book.
        ```
        """
        logging.info(f'reading book {file_path}')
        with open(file_path, "r", encoding='utf-8') as file:
            raw_text = file.readlines()
        book = Book(author=raw_text[0].strip(),
                          title=raw_text[1].strip(),
                          info=raw_text[3].strip(),
                          text="".join(raw_text[4:]))
        return book
