import re


class ValidationError(Exception):
    pass


class Validator():
    VALID_URL_REGEX = re.compile(
        # http:// or https://
        r'^(?:http)s?://'
        # domain...
        r'(?:(?:[A-Z0-9]'
        r'(?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        # localhost...
        r'localhost|'
        # ...or ip
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        # optional port
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    @classmethod
    def is_url(cls, url: str) -> bool:
        if cls.VALID_URL_REGEX.match(url):
            return True
        return False


validator = Validator()
