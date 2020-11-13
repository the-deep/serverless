import os
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


# not using utils.common.setting instead of os.environ as this module shouldn't be used in deep core.
sentry_config = {
    'dsn': os.environ['SENTRY_DNS'],
    'environment': os.environ['STAGE'],
    'send_default_pii': True,
}

sentry_sdk.init(
    **sentry_config,
    integrations=[AwsLambdaIntegration()]
)
