import logging

# Настройка корневого логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание форматтера с желаемым форматом логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создание обработчика для записи логов в файл с кодировкой utf-8
file_handler = logging.FileHandler('bot.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Добавление обработчика файлового логгера к логгеру
logger.addHandler(file_handler)
