import time
import os
import requests
import logging

from telebot import TeleBot, types
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
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
    # print('Переменные окружения работают') ###############################
    return all([value for value in result.values()])


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram-чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error(f'сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        # print('go homework_statuses')########################################
        if homework_statuses.status_code == 200:
            result = homework_statuses.json()
            # print('status normal')##########################################
            # print(result) ###############################################
            return result
        else:
            logging.error('Ошибка статус кода')
    except Exception as error:
        logging.error(f'ошибка при запросе к эндпоинту: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока."""
    if not response:
        return None
    elif not isinstance(response, dict):
        raise TypeError
    response_result = response.get('homeworks')
    if not response_result:
        raise ValueError
    elif not isinstance(response_result, list):
        raise TypeError
    else:
        try:
            return response_result
        except Exception as error:
            logging.error(f'отсутствие ожидаемых ключей в ответе API: {error}')


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе
    статус этой работы.
    """
    if homework:
        try:
            homework_name = homework[0].get('status')
            if homework_name in HOMEWORK_VERDICTS:
                verdict = HOMEWORK_VERDICTS[homework[0]['status']]
                return (f'Изменился статус проверки работы '
                        f'"{homework_name}". {verdict}')
            else:
                logging.error(
                    'неожиданный статус домашней работы, '
                    'обнаруженный в ответе API'
                    )
                raise ValueError
        except Exception as error:
            logging.error(f'отсутствие ожидаемых ключей в ответе API: {error}')
    else:
        logging.debug('отсутствие в ответе новых статусов')
        return None


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_telegram = ''
    while True:
        if not check_tokens():
            break

        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message and message_telegram != message:
                send_message(bot, message)
                message_telegram = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message_telegram != message:
                send_message(bot, message)
                message_telegram = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
