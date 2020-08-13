import unittest

from src.common.tests import Timeout
from src.common.validators import ValidationError
from parameterized import parameterized

from .handler import check_duplicates


class TestParamsValidation(unittest.TestCase):
    @Timeout
    @parameterized.expand(['project', 'source_key'])
    def test_no_param(self, param_name):
        event = {
            'queryStringParameters': {
                'project': 1,
                'source_key': 'testkey'
            }
        }
        # Pop out the parameter that is to be tested as not present
        event['queryStringParameters'].pop(param_name)

        with self.assertRaises(ValidationError):
            check_duplicates(event)
