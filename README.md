### Встречайте! Встречайте! Встречайте! 
# Гадание по книге через телеграм бот [Bibliomancer](https://t.me/bookdivbot)!

## Описание

Этот телеграм бот позволяет получить предсказание по книге. Прямо как в реальной жизни. Выберите одну из доступных книг (/book), напишите страницу и желаемую строчку. Вы получите цитату и её сгенерированное изображение — это и будет вашим предсказанием.

В этом репозитории также содержится код [админ-бота](./adminbot.py), через которого можно загружать новые книги, смотреть количество пользователей, добавлять новых админов и банить пользователей в случае необходимости. Книги загружаются как файлы в формате .txt и автоматически делятся на страницы и предложения.

Для взаимодействия с API телеграма используется фреймворк [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot), в качестве СУБД я использую [MySQL](https://www.mysql.com/), для генерации картинок — [Pillow](https://pillow.readthedocs.io/en/stable/).

### Описание базы данных

В файле [`database.sql`](./database.sql) содержатся SQL-запросы создания базы данных: 
- Таблица `book` хранит метаданные о книгах: название, авторы и т.д. 
- Страницы книг хранятся в `page`.
- Таблица `chat` содрежит id всех чатов, которые взаимодействуют с ботом, а также id книги из `book`, которую выбрал пользователь.

С помощью таблиц: `role`, `chat_role` и представления `chat_role_view` реализована __система ролей__.\
На данный момент используются роли _user_, _admin_ и _banned_, которые отвечают за обычного пользователя, администратора и забанненого пользователя соответсвенно. Роль _admin_ дает возможность пользоваться админ-ботом. Один и тот же пользователь может иметь несколько ролей (например _user_ и _admin_).

Каждая выданная роль может иметь временные рамки в теченнии которых она действует (`grant_date` и `expire_date`).\
Событие `role_expiration` ежедневно в 3 часа ночи проверяет срок дейтсвия роли, и, в случае истечения, забирает её у пользователя.

### Генерация изображений

Класс `QuoteImage` из файла [`imgen.py`](./imgen.py) отвечает за генерацию изображения цитаты.\
Чтобы избежать задержек в работе бота, для генерации изображений используется временная память `io.BytesIO`, а не диск.

Пример сгенерированной цитаты:

<img src="https://github.com/ggeorg0/divination-tg-bot/assets/89857543/c784abdf-d554-41e6-b7b3-0a29ca0bffe3)" alt="sreenshot" width="720"/>



## Установка:

1. Клонируйте репозиторий на ваш компьютер:\
`git clone git@github.com:ggeorg0/divination-tg-bot.git`

2. Перейдите в папку репозитория:\
`cd divitaion-tg-bot`

3. Чтобы случайно не перезаписать ваши библиотеки Python другими версиями, используйте [виртуальные окружения](https://docs.python.org/3/library/venv.html)
    
    | os      | command                                                  |
    |---------|----------------------------------------------------------|
    | linux   | `python3 -m venv ./.venv && source ./.venv/bin/activate` |
    | windows | `python -m venv ./.venv && ./.venv/Scripts/activate`     |

4. Установите зависимости из файла [`requirements.txt`](./requirements.txt)
   
    | os      | command                              |
    |---------|--------------------------------------|
    | linux   | `pip3 install -r ./requirements.txt` |
    | windows | `pip install  -r ./requirements.txt` |

5. Наверняка у меня нет прав на распространение чужих шрифтов, поэтому вам придется самостоятельно найти шрифт Ubuntu Bold и поместить его файл `Ubuntu-Bold.ttf` в директорию `fonts/`.

6. Теперь вам нужно установить систему управления базами данных [MySQL](https://dev.mysql.com/doc/refman/8.0/en/installing.html) (версия >= 8.0) на вашем компьютере. Если вы знакомы с Docker, вы можете использовать его.

7. Получите токены доступа к ботам от [BotFather](https://t.me/botfather) — один для обычного бота и один для админ-бота

8. Обновите файл [`config.py`](./config.py) с вашими учетными данными для MySQL и токенами ботов, которые вы получили от BotFather. Если вы не хотите хранить учетные данные в файле, используйте переменные окружения. 

9. Запустите файл `db_setup.py` который инициирует базу данных. Вам будет предложено ввести id начального администратора (остальных админов можно будет добавлять через сам админ-бот).

    | os      | command                 |
    |---------|-------------------------|
    | linux   | `python3 ./db_setup.py` |
    | windows | `python ./db_setup.py`  |

10. Запустите __обычного бота__ с помощью команды:

    | os      | command                 |
    |---------|-------------------------|
    | linux   | `python3 ./runbot.py`   |
    | windows | `python ./runbot.py`    |

11. Запустите __админ-бота__ с помощью команды:

    | os      | command                 |
    |---------|-------------------------|
    | linux   | `python3 ./adminbot.py` |
    | windows | `python ./adminbot.py`  |
