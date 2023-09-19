## Встречайте! Встречайте! Встречайте! 
### Гадание по книге через телеграм бот!
---

You can find bot here: [Bibliomancer](https://t.me/bookdivbot)

### Installation:

1. clone repo to your local machine:\
`git clone git@github.com:ggeorg0/divination-tg-bot.git`

2. Dive into repository folder :\
`cd divitaion-tg-bot`

3. In order to not accidentally change version of your python libraries **use virtual environments**\
windows: `python -m venv ./.venv && ./.venv/Scripts/activate`\
linux: `python3 -m venv ./.venv && source ./.venv/bin/activate`

4. Now you need to [install MySQL](https://dev.mysql.com/doc/refman/8.0/en/installing.html) database (ver. >= 8.0) on your local machine. If you are familiar with docker, you can use it.

5. Get two tokens from [BotFather](https://t.me/botfather): one for ordinary bot and one for admin bot.

6. Update file `config.py` with your MySQL credentials and bot tokens you get from BotFater.

7. Run your ordinary bot with\
`python ./runbot.py` (windows)\
`python3 ./runbot.py` (linux)

8. Run your admin bot with\
`python ./adminbot.py` (windows)\
`python3 ./adminbot.py` (linux)

