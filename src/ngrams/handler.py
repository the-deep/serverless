import json
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer, SpanishStemmer
from nltk.util import ngrams
from collections import Counter, OrderedDict

from textblob import TextBlob

"""
Sample request body payload
{
    "entries": ["entry1", "entry2"],
    "ngrams": {
        "unigrams": true,
        "bigrams": true,
        "trigrams": true
    },
    "enable_stopwords": false,
    "enable_stemming": true,
    "enable_case_sensitive": false
    "max_ngrams_items": 10
}
"""

MAX_NGRAMS_ITEMS = 10

stemmer_en = nltk.stem.PorterStemmer()
stemmer_fr = FrenchStemmer()
stemmer_es = SpanishStemmer()

stopwords_en = stopwords.words('english')
stopwords_fr = stopwords.words('french')
stopwords_es = stopwords.words('spanish')


def language_detect(entry):
    b = TextBlob(entry)
    return b.detect_language()


def clean_entry(
    entry,
    enable_stopwords,
    enable_stemming,
    enable_case_sensitive,
    language='en'
):
    entry = entry.strip()
    entry = "".join([w for w in entry if w not in string.punctuation])
    entry_tokens = re.split(r'\W+', entry)
    if enable_stemming:
        if language == 'fr':
            entry_tokens = [stemmer_fr.stem(w) for w in entry_tokens]
        elif language == 'es':
            entry_tokens = [stemmer_es.stem(w) for w in entry_tokens]
        else:
            entry_tokens = [stemmer_en.stem(w) for w in entry_tokens]
    if enable_stopwords:
        if language == 'fr':
            entry_tokens = [w for w in entry_tokens if w not in stopwords_fr]
        elif language == 'es':
            entry_tokens = [w for w in entry_tokens if w not in stopwords_es]
        else:
            entry_tokens = [w for w in entry_tokens if w not in stopwords_en]
    if not enable_case_sensitive:
        entry_tokens = [w.lower() for w in entry_tokens]

    entry = " ".join(entry_tokens)
    return entry


def get_ngrams(entries, max_ngrams_items, n=1):
    ngrams_output = [ngrams(entry.split(), n) for entry in entries]

    ngrams_lst = [list(x) for x in ngrams_output]
    # Flatten the list of list
    flat_list = [item for sublist in ngrams_lst for item in sublist]
    return Counter(flat_list).most_common(max_ngrams_items)


def process(
    entries,
    max_ngrams_items,
    process_unigrams=True,
    process_bigrams=True,
    process_trigrams=True,
    enable_stopwords=True,
    enable_stemming=True,
    enable_case_sensitive=True
):
    ngrams = dict()

    processed_entries = list()
    for entry in entries:
        detected_lang = language_detect(entry)
        processed_entries.append(
            clean_entry(
                entry,
                enable_stopwords,
                enable_stemming,
                enable_case_sensitive,
                language=detected_lang
            )
        )

    if process_unigrams:
        one_grams = get_ngrams(processed_entries, max_ngrams_items, n=1)
        ngrams["unigrams"] = OrderedDict({
            " ".join(k): v for k, v in dict(one_grams).items()
        })

    if process_bigrams:
        two_grams = get_ngrams(processed_entries, max_ngrams_items, n=2)
        ngrams["bigrams"] = OrderedDict({
            " ".join(k): v for k, v in dict(two_grams).items()
        })

    if process_trigrams:
        three_grams = get_ngrams(processed_entries, max_ngrams_items, n=3)
        ngrams["trigrams"] = OrderedDict({
            " ".join(k): v for k, v in dict(three_grams).items()
        })

    return ngrams


def handle_entries(event, context):
    try:
        request_body = json.loads(event["body"])
        entries = request_body["entries"]
        process_unigrams = request_body["ngrams"]["unigrams"]
        process_bigrams = request_body["ngrams"]["bigrams"]
        process_trigrams = request_body["ngrams"]["trigrams"]
        enable_stopwords = request_body.get("enable_stopwords", False)
        enable_stemming = request_body.get("enable_stemming", False)
        enable_case_sensitive = request_body.get(
            "enable_case_sensitive", False
        )
        max_ngrams_items = request_body.get(
            "max_ngrams_items", MAX_NGRAMS_ITEMS
        )

        ngram_outputs = process(
            entries,
            max_ngrams_items,
            process_unigrams=process_unigrams,
            process_bigrams=process_bigrams,
            process_trigrams=process_trigrams,
            enable_stopwords=enable_stopwords,
            enable_stemming=enable_stemming,
            enable_case_sensitive=enable_case_sensitive
        )

        response = {
            "statusCode": 200,
            "body": json.dumps(ngram_outputs)
        }
    except IndexError as e:
        response = {
            "statusCode": 500,
            "body": json.dumps(e)
        }

    return response
