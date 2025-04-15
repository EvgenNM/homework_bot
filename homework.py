import logging
import os
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telebot import TeleBot, apihelper

import exceptions as EX


load_dotenv()


logger = logging.getLogger(__name__)

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
    errors = []
    for key, value in result.items():
        if not value:
            errors += [key]
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                f'{key}. Программа принудительно остановлена.'
            )
    if errors:
        raise EX.ErrorCheckTokens(
            f'Отсутствие переменных(-ой): {", ".join(result)}'
        )
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат, опр-й переменной окружения."""
    try:
        logger.debug('Начало отправки сообщения в Telegram')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('удачная отправка сообщения в Telegram')
        return True
    except (apihelper.ApiException, requests.RequestException) as error:
        logger.error(error, exc_info=True)
        return False


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        logger.debug('Начало запроса к эндпоинту API-сервиса')
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException as error:
        raise EX.ErrorRequestGetApi(
            'ошибка при запросе c from_date '
            '"{}" к эндпоинту: {}'.format(timestamp, error)
        )

    if homework_statuses.status_code == HTTPStatus.OK:
        return homework_statuses.json()
    raise EX.ErrorRequestGetApiHttpsStatus(
        'Ошибка статуса при запросе к эндпоинту API-сервиса'
    )


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока."""
    if not isinstance(response, dict):
        raise EX.ErrorResponseNotDict(f'В response находится {type(response)}')
    elif response.get('homeworks') is None:
        raise EX.ErrorResponseDictKey(
            'Словарь response не содержит ключ "homeworks"'
        )

    homeworks = response['homeworks']

    if not isinstance(homeworks, list):
        raise EX.ErrorResponseNotList(
            'Значение словаря response содержит ключ "homeworks"'
            ' значением которого не является list'
        )
    return homeworks


def parse_status(homework):
    """Извлекает из инф-ю о конкретной домашней работе статус этой работы."""
    if not homework:
        logger.debug('отсутствие в ответе новых статусов')
        return None
    elif not isinstance(homework, dict):
        logger.error('в списке значений "homework" нет ожидаемого словаря')
        raise EX.ErrorDictParseStatus
    elif 'status' not in homework:
        logger.error('в списке значений "homework" нет ожидаемого словаря')
        raise EX.ErrorDictKeyParseStatus
    elif homework['status'] not in HOMEWORK_VERDICTS:
        logger.error(
            'неожиданный статус домашней работы, '
            'обнаруженный в ответе API'
        )
        raise EX.ErrorDictKeyStatusInParseStatus
    elif 'homework_name' not in homework:
        logger.error('в ответе API домашки нет ключа "homework_name"')
        raise EX.ErrorDictKeyHomeworkNameInParseStatus
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return ('Изменился статус проверки работы '
            f'"{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_error = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                *_, timestamp = [
                    None, response.get('current_date', time.time())
                ][send_message(bot, message)]
            else:
                logger.debug('Пустое сообщение не отправлено')
        except Exception as error:
            message = f'Возникла ошибка {error}'
            logger.error(message)
            if message_error != message:
                send_message(bot, message)
                message_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler = RotatingFileHandler(
        'main.log',
        maxBytes=50000000,
        backupCount=5,
        encoding='utf-8'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    main()
