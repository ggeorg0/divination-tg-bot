import pytest

import bookparse
from bookparse import Book, BookReader

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

class TestBookReader:

    # LLM generated text:
    book_corp = """Name Surname-Surname
The Very Long Title of this Interesting Book
    
This book was written by myself, by Name Surname-Surname and so on...
    
Chapter 1. Childhood
    
I was an amazing kid growing up. Everything was interesting to me. I especially liked programming. 
Sometimes it took whole evenings to write to the programs I was making. 
So, one day, I developed a timer in the console that printed the words "It's time to eat! Time to sleep!". 
That's what I called it - "Time to Eat."
I didn't even think that it could be dangerous. 
I thought it would all be for my purposes only. 
Then I decided that time could be killed. And I started killing time. I don't know why I decided that. 
Just at one point I wanted to see how much time was left before leaving. 
But I couldn't get distracted by anything, or even sleep, because I didn't have enough time."""

    def test_read_book_00(self, tmp_path):
        path = tmp_path / 'book_file'
        with open(path, 'w') as f:
            f.write(self.book_corp)
        
        desired_book = Book(
            author="Name Surname-Surname",
            title="The Very Long Title of this Interesting Book",
            info="This book was written by myself, by Name Surname-Surname and so on...",
            text="")

        book = BookReader.read_book(path)

        assert desired_book.author == book.author
        assert desired_book.title == book.title
        assert desired_book.info == book.info

