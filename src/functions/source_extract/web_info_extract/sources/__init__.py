from urllib.parse import urlparse

from .default import DefaultWebInfoExtractor, HTML
from .document import DocumentWebInfoExtractor
from .redhum import RedhumWebInfoExtractor


# TODO: USE pattern instead of domain
EXTRACTORS = {
    'redhum.org': RedhumWebInfoExtractor,
}


def get_web_info_extractor(url, document_type=None):
    # NOTE: FOR NON HTML
    if document_type and document_type != HTML:
        return DocumentWebInfoExtractor(url, document_type)
    website = urlparse(url).netloc
    return EXTRACTORS.get(website, DefaultWebInfoExtractor)(url)
