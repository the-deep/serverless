import time

from .common import get_file_name_from_url
from .validators import validator
from .camelize import camelize


class Timeout:
    def __init__(self, timeout=30):
        self.timeout = timeout

    def __call__(self, func_to_be_tracked):
        def wrapper(*args, **kwargs):
            start = time.time()
            ret = func_to_be_tracked(*args, **kwargs)
            total_time = time.time() - start
            assert self.timeout >= total_time, f'Total time should be <= 30 instead of {total_time}'
            return ret
        wrapper.__name__ = func_to_be_tracked.__name__
        wrapper.__module__ = func_to_be_tracked.__module__
        return wrapper


def test_get_file_name_from_url():
    url = 'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb%20Vision%20and%20Strategy.pdf'
    filename = get_file_name_from_url(url)
    assert 'ReliefWeb Vision and Strategy' == filename


def test_validator():
    valid_urls = (
        'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb%20Vision%20and%20Strategy.pdf',
    )
    invalid_urls = (
        'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb Vision and Strategy.pdf',
    )
    for url in valid_urls:
        assert validator.is_url(url) is True
    for url in invalid_urls:
        assert validator.is_url(url) is False


def test_camelize():
    res = camelize({
        'test_1': 'value 1',
        'test_2': 'value 1',
        'nested_test': {
            'nested_key_one': 'value',
            'nested_key_2': 'value',
            'nested_key_three': 'value',
        },
    })
    assert res == {
        'test1': 'value 1',
        'test2': 'value 1',
        'nestedTest': {
            'nestedKeyOne': 'value',
            'nestedKey2': 'value',
            'nestedKeyThree': 'value',
        },
    }
