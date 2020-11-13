import datetime
import os
import logging
import sentry_sdk

from .django_utils.common import DjangoJSONEncoder
from .validators import ValidationError
from .camelize import camelize_response, underscoreize

from lambda_decorators import (
    LambdaDecorator as OLambdaDecorator,
    json_http_resp,
    load_json_body,
    cors_headers,
)

logger = logging.getLogger(__name__)

CORS_DOMAIN = os.environ.get('CORS_DOMAIN', '*')
VALIDATION_EXCEPTIONS = (
    ValidationError,
)


def create_error_response(exception, event, context) -> dict:
    """Generate response from exception"""
    resp_data = {'timestamp': datetime.datetime.now().timestamp()}
    status_code = 500
    # TODO: Hanlde exception default message if present
    exc_data = exception.args[0] if len(exception.args) else None

    non_field_errors = ['Something unexpected happened']
    internal_non_field_errors = []

    # 400 response
    if exception.__class__ in VALIDATION_EXCEPTIONS:
        status_code = 400
        non_field_errors = []
        if isinstance(exc_data, dict):
            resp_data['errors'] = exc_data
        elif exc_data.__class__ in [list, tuple]:
            non_field_errors = exc_data
        elif isinstance(exc_data, str):
            non_field_errors = [exc_data]
    else:
        # LOG EXCEPTION HERE
        # with sentry_sdk.configure_scope() as scope:
        #     scope.user = {
        #         'id': request.user.id,
        #         'email': request.user.email,
        #     }
        sentry_sdk.capture_exception()
        logger.error(
            'ERROR: {}.{}'.format(type(exception).__module__, type(exception).__name__),
            exc_info=True,
            extra={'event': event, 'context': context},
        )
        if exc_data.__class__ in [list, tuple]:
            internal_non_field_errors = exc_data
        elif isinstance(exc_data, str):
            internal_non_field_errors = [exc_data]

    if 'errors' not in resp_data:
        resp_data['errors'] = {
            'non_field_errors': non_field_errors or ['Something went wrong. Please try later or contact admin.']
        }
    if internal_non_field_errors:
        resp_data['errors']['internal_non_field_errors'] = internal_non_field_errors
    resp_data['status_code'] = status_code
    return resp_data


# TODO: Write test
class LambdaDecorator(OLambdaDecorator):
    def __call__(self, event, context):
        self.event = event
        self.context = context
        return super().__call__(event, context)

    def before(self, event, context):
        response = load_json_body(lambda *args: args)(event, context)
        if type(response) == dict:  # not event, context
            raise ValidationError('Body parse error')
        if 'body' in event:
            event['body'] = underscoreize(event['body'] or {})
        return event, context

    @json_http_resp(cls=DjangoJSONEncoder)
    @cors_headers(origin=CORS_DOMAIN, credentials=True)
    @camelize_response
    def after(self, retval):
        return retval

    @json_http_resp(cls=DjangoJSONEncoder)
    @cors_headers(origin=CORS_DOMAIN, credentials=True)
    @camelize_response
    def on_exception(self, exception):
        return create_error_response(exception, self.event, self.context)
