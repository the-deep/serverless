# https://github.com/vbabiy/djangorestframework-camel-case
import re
from functools import wraps
from collections import OrderedDict


camelize_re = re.compile(r"[a-z0-9]?_[a-z0-9]")


def underscore_to_camel(match):
    group = match.group()
    if len(group) == 3:
        return group[0] + group[2].upper()
    else:
        return group[1].upper()


def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True


def camelize(data):
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            if isinstance(key, str) and "_" in key:
                new_key = re.sub(camelize_re, underscore_to_camel, key)
            else:
                new_key = key
            new_dict[new_key] = camelize(value)
        return new_dict
    if is_iterable(data) and not isinstance(data, str):
        return [camelize(item) for item in data]
    return data


def camelize_response(handler_or_none=None):
    """
    Automatically camelize return value to the body of a successfull HTTP response.
    """
    if handler_or_none is None:
        def wrapper_wrapper(handler):
            @wraps(handler)
            def wrapper(event, context):
                try:
                    return camelize(handler(event, context))
                except Exception as exception:
                    if hasattr(context, "serverless_sdk"):
                        context.serverless_sdk.capture_exception(exception)
                    return {"statusCode": 500, "body": str(exception)}
            return wrapper
        return wrapper_wrapper
    else:
        return camelize_response()(handler_or_none)
