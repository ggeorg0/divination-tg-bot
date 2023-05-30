import pytest

import bookparse
from bookparse import Book

class TestBook:

    # LLM generated text:
    story = """Медведи живут в тайге. Они едят ягоды, грибы и орехи. У них есть медведица и медвежата. 
    Медведя зовут Миша. Он самый сильный медведь в лесу. 
    Миша любит свою семью и защищает их от других зверей. А медвежата любят играть с мамой-медведем. 
    Она их кормит, защищает и учит охотиться. 
    Однажды Миша увидел, что на поляну вышел большой медведь. Миша испугался и спрятался за деревом. 
    Но медведь его не заметил. Медведь наелся ягод и решил уйти. Он пошел в другую сторону.
    Как-то раз в далекой-далекой стране жил-был юный принц. Он был очень умным, талантливым и добрым. 
    У него было много друзей, но однажды он решил отправиться в путешествие, чтобы найти себя. 
    И вот он отправился в путь, и ему казалось, что он идет уже целую вечность. 
    Но, пройдя множество стран, он понял, что путешествует всего лишь два года. 
    Вначале он думал, что это какой-то другой мир, но потом понял, что просто не может вернуться домой.
    """

    def test_init_00(self):
        book = Book()
        assert book.title == "NULL"
        assert book.author == "NULL"
        assert book.info == "NULL"
        assert book.pages == None

    def test_init_01(self):
        book = Book(author="Author",
                    title="The Title",
                    info="The Info",
                    text=self.story)
        assert book.author == "Author"
        assert book.title == "The Title"
        assert book.info == "The Info"
        assert isinstance(book.pages, list)
        assert len(book.pages) >= 1
        # print("Pages of story:", len(book.pages))

    def test_str_00(self):
        book = Book(author="Author",
                    title="The Title",
                    info="The Info",
                    text=None)
        
        desired = f"'{book.title}', '{book.author}', '{book.info}'"
        assert book.__str__() == desired

    def test_pages_from_text_00(self, monkeypatch):
        monkeypatch.setattr("bookparse.LINE_SYMBOLS", 20)
        monkeypatch.setattr("bookparse.PAGE_SYMBOLS", 6)

        book = Book(author="Author",
                    title="The Title",
                    info="The Info",
                    text=self.story)
        desired_page = "Медведи живут в\nтайге. Они едят\nягоды, грибы и\nорехи. У них есть\nмедведица и\nмедвежата."
        
        assert book.pages[0] == desired_page
    
    def test_add_lines_00(self, monkeypatch):
        monkeypatch.setattr("bookparse.LINE_SYMBOLS", 13)

        book = Book(author="Author",
                    title="The Title",
                    info="The Info",
                    text=self.story)
        words = ["abra", "cadabra,", "rumble", "table,", "brown!", "spoon..."]
        desired_lines = ["abra cadabra,", "rumble table,", "brown!", "spoon...", ""]

        lines = [""]
        book._add_lines(lines, words)
        
        assert lines == desired_lines
        

