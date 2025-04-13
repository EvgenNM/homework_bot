import time
import os
import requests
import logging

from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s'
)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    result = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for key, value in result.items():
        if not value:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: '
                f'{key}. Программа принудительно остановлена.'
            )
            break
    return all([value for value in result.values()])


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат, опр-й переменной окружения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error(error, exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    homework_statuses = None
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework_statuses.status_code == 200:
            result = homework_statuses.json()
            return result
    except Exception as error:
        logging.error(f'ошибка при запросе к эндпоинту: {error}')

    if homework_statuses is not None and homework_statuses.status_code != 200:
        logging.error('Ошибка статус кода')
        raise Exception


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока."""
    if not response:
        logging.error('response пуст')
        return None
    elif not isinstance(response, dict):
        logging.error('response не является dict')
        raise TypeError
    elif response.get('homeworks') is None:
        logging.error('Словарь response не содержит ключ "homeworks"')
        raise ValueError
    elif not isinstance(response['homeworks'], list):
        logging.error(
            'Значение словаря response содержит ключ "homeworks"'
            ' значением которого не является list'
        )
        raise TypeError
    elif not response['homeworks']:
        return response['homeworks']
    else:
        return response['homeworks'][0]


def parse_status(homework):
    """Извлекает из инф-ю о конкретной домашней работе статус этой работы."""
    if not homework:
        logging.debug('отсутствие в ответе новых статусов')
        return None
    elif not isinstance(homework, dict):
        logging.debug('в списке значений "homework" нет ожидаемого словаря')
        raise TypeError
    elif HOMEWORK_VERDICTS.get(homework['status']) is None:
        logging.error(
            'неожиданный статус домашней работы, '
            'обнаруженный в ответе API'
        )
        raise ValueError
    elif homework.get('homework_name') is None:
        logging.error('в ответе API домашки нет ключа "homework_name"')
        raise ValueError
    else:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        message = (f'Изменился статус проверки работы '
                   f'"{homework_name}". {verdict}')
        return message


def main():
    """Основная логика работы бота."""
    work = False
    if check_tokens():
        bot = TeleBot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())
        message_telegram = ''
        work = True
    while work:
        response = get_api_answer(timestamp)
        homework = check_response(response)
        message = parse_status(homework)
        if message and message_telegram != message:
            send_message(bot, message)
            message_telegram = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
