from parameterized import parameterized
from src.common.tests import Timeout

from .handler import extract

TEST_CASES = {
    'redhum': {
        'url': 'https://redhum.org/documento/123212',
        'response': {
            "source_raw": "redhum",
            "author_raw": "United Nations Commission on Human Rights",
            "title": "Six Rapporteurs address Human Rights Commission under debate on civil and political rights",
            "date": "2003-04-08",
            "country": "Afghanistan",
            "website": "redhum.org",
            "url": "https://redhum.org/documento/123212",
        },
    },
    'reliefweb-working': {
        'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb%20Vision%20and%20Strategy.pdf',
        'response': {
            'author_raw': None,
            'country': None,
            'date': None,
            'source_raw': 'reliefweb',
            'title': 'ReliefWeb Vision and Strategy',
            'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb%20Vision%20and%20Strategy.pdf',
            'website': 'reliefweb.int',
        },
    },
    # TODO: Support for timeout requests
    # 'reliefweb-timeout': {
    #     'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/65947.pdf',
    #     'response': {
    #         'author_raw': None,
    #         'country': None,
    #         'date': None,
    #         'source_raw': 'reliefweb',
    #         'title': '65947',
    #         'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/65947.pdf',
    #         'website': 'reliefweb.int',
    #     },
    # },
}


@Timeout
@parameterized.expand(TEST_CASES.keys())
def test_web_info_extract(test):
    case = TEST_CASES[test]
    url = case['url']
    response = case['response']
    resp = extract(url)
    assert resp == response, f'Response for {url} doesn\'t match'
