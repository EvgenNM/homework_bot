class ErrorCheckTokens(Exception):
    """Исключение недоступности переменных окружения."""


class ErrorRequestGetApi(Exception):
    """Исключение ошибки запроса к API"""


class ErrorRequestGetApiHttpsStatus(Exception):
    """Исключение ошибки статус кода при запросе к API"""
