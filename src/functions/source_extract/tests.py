import json
from parameterized import parameterized
from src.common.tests import Timeout

from .handler import web_info_extract

TEST_CASES = {
    'redhum': {
        'url': 'https://redhum.org/documento/123212',
        'response': {
            'sourceRaw': 'redhum',
            'authorsRaw': ['United Nations Commission on Human Rights'],
            'title': (
                'Six Rapporteurs address Human Rights Commission '
                'under debate on civil and political rights'
            ),
            'date': '2003-04-08',
            'country': 'Afghanistan',
            'website': 'redhum.org',
            'pdfUrls': [],
        },
    },
    'reliefweb-working-pdf': {
        'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/ReliefWeb%20Vision%20and%20Strategy.pdf',
        'response': {
            'authorsRaw': [],
            'country': None,
            'date': None,
            'sourceRaw': 'reliefweb',
            'title': 'ReliefWeb Vision and Strategy',
            'website': 'reliefweb.int',
            'pdfUrls': [],
        },
    },
    'reliefweb-working-url': {
        'url': 'https://reliefweb.int/report/bangladesh/millions-bangladesh-impacted-one-worst-floodings-ever-seen',
        'response': {
            'authorsRaw': ['IFRC'],
            'country': 'Bangladesh',
            'date': '2022-06-28',
            'sourceRaw': 'reliefweb',
            'title': 'Millions in Bangladesh impacted by one of the worst floodings ever seen',
            'website': 'reliefweb.int',
            'pdfUrls': [],
        },
    },
    'reliefweb-working-url-with-pdf': {
        'url': 'https://reliefweb.int/report/south-sudan/south-sudan-nutrition-service-delivery-covid-19-context-frequently-asked-question-and-suggested-measures',  # noqa:E501
        'response': {
            'authorsRaw': ['Nutrition Cluster', 'UNICEF'],
            'country': 'South Sudan',
            'date': '2020-05-28',
            'sourceRaw': 'reliefweb',
            'title': 'South Sudan: Nutrition Service Delivery In COVID-19 Context - Frequently asked question and suggested measures',  # noqa:E501
            'website': 'reliefweb.int',
            'pdfUrls': [
                'https://reliefweb.int//attachments/9fc61749-e380-460d-9809-bfcf3be77722/nutrition_covid_19_-_faq_and_recommendations_-_updated_29.05.2020_1.pdf'  # noqa:E501
            ],
        },
    },
    # TODO: Support for timeout requests
    # 'reliefweb-timeout': {
    #     'url': 'https://reliefweb.int/sites/reliefweb.int/files/resources/65947.pdf',
    #     'response': {
    #         'authors_raw': [],
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
    mock_event = {
        'queryStringParameters': {'url': url},
    }
    resp = web_info_extract(mock_event, context={})
    assert json.loads(resp['body']) == response, f'Response for {url} doesn\'t match'
