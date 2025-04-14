class ErrorCheckTokens(Exception):
    """Исключение недоступности переменных окружения."""


class ErrorRequestGetApi(Exception):
    """Исключение ошибки запроса к API"""


class ErrorRequestGetApiHttpsStatus(Exception):
    """Исключение ошибки статус кода при запросе к API"""


class ErrorResponseNone(Exception):
    """Исключение при пустом response"""


class ErrorResponseNotDict(TypeError):
    """Исключение ошибки при отсутствии словаря в response"""
