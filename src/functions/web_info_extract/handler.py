from src.common.decorators import LambdaDecorator, ValidationError
from src.common.validators import validator
from .sources import get_web_info_extractor


def extract(url):
    # TODO: Use schema validator
    if not url or not validator.is_url(url):
        raise ValidationError({'url': 'Url must be present and valid'})

    extractor = get_web_info_extractor(url)
    return extractor.get_serialized_data()


@LambdaDecorator
def main(api_input, *args, **kwargs):
    params = api_input.get('queryStringParameters') or {}
    url = params.get('url') or ''
    return extract(url)
