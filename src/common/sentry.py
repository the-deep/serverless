import os
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


sentry_config = {
    'dsn': os.environ['SENTRY_DNS'],
    'environment': os.environ['STAGE'],
    'send_default_pii': True,
}

sentry_sdk.init(
    **sentry_config,
    integrations=[AwsLambdaIntegration()]
)
