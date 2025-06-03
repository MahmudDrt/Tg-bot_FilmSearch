import telebot
import requests
import sqlite3
from logger import logger  # Импортируем настроенный логгер из logger.py

# Токен вашего Telegram бота
YOUR_TELEGRAM_BOT_TOKEN = '6959496680:AAH0VoNkJMDY4bUnkA2bqdkTtZ8wtXUxlYI'

# URL и ключ API Kinopoisk
KINOPOISK_API_URL = 'https://kinopoiskapiunofficial.tech'
YOUR_KINOPOISK_API_KEY = 'f5571529-5153-4c8a-8f82-5d8527437341'

# Создание объекта бота
bot = telebot.TeleBot(YOUR_TELEGRAM_BOT_TOKEN)

# Подключение к базе данных SQLite
conn = sqlite3.connect('films.db')
cursor = conn.cursor()


# Функция для выполнения GET-запроса к Kinopoisk API для поиска фильмов по актеру
def search_movies_by_actor(actor_name):
    try:
        url = f"{KINOPOISK_API_URL}/api/v2.1/films/search-by-keyword"
        headers = {
            'X-API-KEY': YOUR_KINOPOISK_API_KEY,
            'Content-Type': 'application/json',
        }
        params = {
            'keyword': actor_name,
            'page': 1,
            'pageSize': 10,
            'fields': 'filmId,nameRu,nameEn,year,rating',  # Добавляем рейтинг (rating) в список полей
            'order': 'yearAsc',  # Сортировка по полю year в порядке возрастания
        }
        logger.info(f"Запрос к Kinopoisk API: {url}")  # Логируем URL для отладки

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        logger.info(f"Ответ от Kinopoisk API: {data}")  # Логируем ответ для отладки

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка соединения с Kinopoisk API: {e}")
        return None
    except ValueError as e:
        logger.error(f"Ошибка при разборе JSON от Kinopoisk API: {e}")
        return None


# Функция для обработки команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я бот для поиска информации о фильмах. Просто отправь мне имя актера, чтобы найти фильмы, в которых он снимался.")


# Функция для обработки текстовых сообщений (поиск фильмов по актеру)
@bot.message_handler(func=lambda message: True)
def search_movies_by_actor_handler(message):
    if message.text.startswith('/start'):
        return  # Просто игнорируем сообщения с командой /start здесь

    actor_name = message.text.strip()
    logger.info(f"Получен запрос с именем актера: {actor_name}")  # Логируем имя актера для отладки

    movies_data = search_movies_by_actor(actor_name)

    if movies_data and 'films' in movies_data:
        films = movies_data['films']
        if films:
            # Сортировка фильмов по году в порядке возрастания
            films_sorted = sorted(films, key=lambda x: x.get('year', 0))

            # Формирование текстового сообщения для ответа
            response_text = ""
            for film in films_sorted:
                name = film.get('nameRu', film.get('nameEn', 'Название не указано'))
                year = film.get('year', 'Год не указан')
                rating = film.get('rating', 'Рейтинг не указан')

                response_text += f"Название: {name}\n"
                response_text += f"Год: {year}\n"
                response_text += f"Рейтинг: {rating}\n"
                response_text += "\n"  # Добавляем пустую строку между фильмами
        else:
            response_text = f"Фильмы с участием актера {actor_name} не найдены."
    else:
        response_text = f"Ошибка поиска по актеру {actor_name}."

    bot.reply_to(message, response_text)


# Запуск бота
if __name__ == "__main__":
    bot.polling()
