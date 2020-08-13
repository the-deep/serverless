import os
import logging

from deep_utils.deduplication.elasticsearch import search_similar, create_knn_vector_index_if_not_exists
from deep_utils.deduplication.vector_generator import create_trigram_vector
from deep_utils.deduplication.utils import remove_puncs_and_extra_spaces, es_wrapper

from src.common.decorators import LambdaDecorator, ValidationError, validate_mandatory_query_params
from src.common.models import Source

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.8
NEAREST_COUNT = 20
VECTOR_SIZE = 10000


@LambdaDecorator
@validate_mandatory_query_params('project', 'source_key')
def check_duplicates(event, *args, **kwargs):
    params = event.get('queryStringParameters') or {}
    project = params['project']
    source_key = params['source_key']
    source = Source.get(source_key)
    if source is None:
        raise ValidationError(f'Could not find source with key "{source_key}"')

    extract = source.extract.simplified_text
    similar_leads = []
    if extract:
        # TODO: language detect
        lang = 'en'
        processed = remove_puncs_and_extra_spaces(extract)
        vector = create_trigram_vector(lang, processed)
        # Prepare connection variables
        endpoint = os.environ['ES_ENDPOINT']
        region = os.environ.get('AWS_REGION', 'us-east-1')
        # Now the elasticsearch instance
        es = es_wrapper(endpoint, region)

        index_name = f'{project}-{lang}-index'
        # Create vector if not exists
        create_knn_vector_index_if_not_exists(index_name, VECTOR_SIZE, es)

        similarity_response = search_similar(NEAREST_COUNT, ('vector1', vector), index_name, es)
        hits = similarity_response['hits']
        max_score = hits['max_score']
        if max_score is not None and max_score > SIMILARITY_THRESHOLD:
            similar_leads = [
                dict(lead_id=x['_id'], similarity_score=x['_score'])
                for x in hits['hits']
                if x['_score'] > SIMILARITY_THRESHOLD
            ]

    return {
        'results': similar_leads,
        'max_score': max_score
    }
