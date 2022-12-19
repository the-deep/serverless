from urllib.parse import urlparse

from .default import DefaultWebInfoExtractor
from .redhum import RedhumWebInfoExtractor
from .relief_web import ReliefwebExtractor


# TODO: USE pattern instead of domain
EXTRACTORS = {
    'redhum.org': RedhumWebInfoExtractor,
    'reliefweb.int': ReliefwebExtractor,
}


def get_web_info_extractor(url, **kwargs):
    website = urlparse(url).netloc
    return EXTRACTORS.get(website, DefaultWebInfoExtractor)(url, **kwargs)
