from .handler import extract

TEST_CASES = [
    {
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
    {
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
]


def test():
    for case in TEST_CASES:
        url = case['url']
        resp = extract(url)
        assert resp == case['response'], f'Response for {url} doesn\'t match'
