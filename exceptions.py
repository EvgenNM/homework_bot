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


class ErrorResponseDictKey(ValueError):
    """Исключение отсутствия ожидаемого ключа homeworks в словаре response."""


class ErrorResponseNotList(TypeError):
    """Исключение отсутствия ожидаемого списка в словаре response """


class ErrorDictParseStatus(TypeError):
    """Исключение отсутствия ожидаемого аргумента - словаря в parse_status"""


class ErrorDictKeyParseStatus(ValueError):
    """Исключение отсутствия ключа в переданном словаре в parse_status"""


class ErrorDictKeyStatusInParseStatus(ValueError):
    """Исключение получения неожиданного статуча довашней работы"""


class ErrorDictKeyHomeworkNameInParseStatus(ValueError):
    """Исключение отсутствия ключа домашки"""
