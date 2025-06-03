import telebot
from telebot import types
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

# Инициализация базы данных и создание таблицы, если её нет
def init_db():
    conn = sqlite3.connect('films.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filmid INTEGER,
            name_ru TEXT,
            name_en TEXT,
            year INTEGER,
            rating FLOAT
        )
    ''')
    conn.commit()
    conn.close()

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
            'fields': 'filmId,nameRu,nameEn,year,rating',
            'order': 'yearAsc',
        }
        logger.info(f"Запрос к Kinopoisk API: {url}")

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        logger.info(f"Ответ от Kinopoisk API: {data}")

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка соединения с Kinopoisk API: {e}")
        return None
    except ValueError as e:
        logger.error(f"Ошибка при разборе JSON от Kinopoisk API: {e}")
        return None

# Функция для записи фильма в базу данных
def insert_movie_to_db(movie):
    try:
        conn = sqlite3.connect('films.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO films (filmid, name_ru, name_en, year, rating) 
            VALUES (?, ?, ?, ?, ?)
        ''', (movie.get('filmId', None), movie.get('nameRu', ''), movie.get('nameEn', ''),
              movie.get('year', None), movie.get('rating', None)))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Ошибка при записи фильма в базу данных: {e}")

# Функция для обработки команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я бот для поиска информации о фильмах. Выберите действие:",
                 reply_markup=generate_start_buttons())

# Обработчик для кнопки "Популярные актеры"
@bot.message_handler(func=lambda message: message.text == "Популярные актеры")
def popular_actors_handler(message):
    global popular_actors  # Добавляем доступ к глобальной переменной
    bot.reply_to(message, "Выберите актера:", reply_markup=generate_popular_actors_buttons())

# Обработчик нажатий на инлайн-кнопки (актеры)
@bot.callback_query_handler(func=lambda call: call.data.startswith('actor:'))
def callback_inline(call):
    _, actor_name = call.data.split(':')
    logger.info(f"Выбран актер: {actor_name}")

    movies_data = search_movies_by_actor(actor_name)

    if movies_data and 'films' in movies_data:
        films = movies_data['films']
        if films:
            films_sorted = sorted(films, key=lambda x: x.get('year', 0))
            for film in films_sorted:
                insert_movie_to_db(film)  # Записываем каждый фильм в базу данных
            response_text = generate_movie_response(films_sorted)
        else:
            response_text = f"Фильмы с участием актера {actor_name} не найдены."
    else:
        response_text = f"Ошибка поиска по актеру {actor_name}."

    bot.send_message(call.message.chat.id, response_text)

# Генерация ответа с информацией о фильмах
def generate_movie_response(films):
    response_text = ""
    for film in films:
        name = film.get('nameRu', film.get('nameEn', 'Название не указано'))
        year = film.get('year', 'Год не указан')
        rating = film.get('rating', 'Рейтинг не указан')
        film_id = film.get('filmId')

        response_text += f"Название: {name}\n"
        response_text += f"Год: {year}\n"
        response_text += f"Рейтинг: {rating}\n"
        if film_id:
            response_text += f"Ссылка на Kinopoisk: https://www.kinopoisk.ru/film/{film_id}\n"
        response_text += "\n"

    return response_text

# Функция для генерации кнопок старта
def generate_start_buttons():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Ввести имя актера"))
    keyboard.add(types.KeyboardButton("Случайный фильм"))
    keyboard.add(types.KeyboardButton("Популярные актеры"))
    return keyboard

# Функция для генерации кнопок с популярными актерами
def generate_popular_actors_buttons():
    keyboard = types.InlineKeyboardMarkup()
    popular_actors = {
        "Райан Гослинг": "Райан Гослинг",
        "Джим Керри": "Джим Керри",
        "Джаред Лето": "Джаред Лето"
    }
    for name in popular_actors.values():
        keyboard.add(types.InlineKeyboardButton(name, callback_data=f"actor:{name}"))
    return keyboard

# Обработчик для кнопки "Случайный фильм"
@bot.message_handler(func=lambda message: message.text == "Случайный фильм")
def random_movie_handler(message):
    with sqlite3.connect('films.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT filmid, name_ru, name_en, year, rating FROM films ORDER BY RANDOM() LIMIT 1')
        movie = cursor.fetchone()

        if movie:
            film_id, name_ru, name_en, year, rating = movie
            response_text = f"Название: {name_ru if name_ru else name_en}\n"
            response_text += f"Год: {year}\n"
            response_text += f"Рейтинг: {rating if rating else 'Рейтинг не указан'}\n"
            if film_id:
                response_text += f"Ссылка на Kinopoisk: https://www.kinopoisk.ru/film/{film_id}"
        else:
            response_text = "В базе данных нет фильмов."

    bot.reply_to(message, response_text)

# Обработчик для кнопки "Ввести имя актера"
@bot.message_handler(func=lambda message: message.text == "Ввести имя актера")
def ask_actor_name_handler(message):
    bot.reply_to(message, "Введите имя актера:")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    actor_name = message.text
    movies_data = search_movies_by_actor(actor_name)

    if movies_data and 'films' in movies_data:
        films = movies_data['films']
        if films:
            films_sorted = sorted(films, key=lambda x: x.get('year', 0))
            for film in films_sorted:
                insert_movie_to_db(film)  # Записываем каждый фильм в базу данных
            response_text = generate_movie_response(films_sorted)
        else:
            response_text = f"Фильмы с участием актера {actor_name} не найдены."
    else:
        response_text = f"Ошибка поиска по актеру {actor_name}."

    bot.send_message(message.chat.id, response_text)

# Запуск бота
if __name__ == "__main__":
    init_db()  # Инициализация базы данных
    bot.polling()
