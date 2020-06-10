from .utils import get_file_name_from_url
from .validators import validator
from .camelize import camelize


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
