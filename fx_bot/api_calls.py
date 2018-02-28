import requests as r
import json


def get(call_type, params=None):
    with open('config.json') as config:
        config = json.load(config)

    header = config.get('header', None)
    url = config.get('url', None)
    endpoint_type = config.get('mapping', None)[call_type]

    if endpoint_type == 'accounts':
        url_id = config.get('account_id', None)
    elif endpoint_type == 'instruments':
        url_id = params.get('instrument', None)
        params.pop('instrument')
    else:
        raise Exception('Endpoint type not recognised! Use [accounts] or [instruments]')

    url = '%s/%s/%s/%s' % (url, endpoint_type, url_id, call_type)

    # Make get call using header and input, if params exits then use them.
    result = r.get(url, headers=header, params=params).json()

    return result


def post(call_type, params=None):
    with open('config.json') as config:
        config = json.load(config)

    header = config.get('header', None)
    url = config.get('url', None)
    endpoint_type = config.get('mapping', None)[call_type]

    url_id = config.get('account_id', None)

    url = '%s/%s/%s/%s' % (url, endpoint_type, url_id, call_type)

    order_params = {'order': params}

    # Make get call using header and input, if params exits then use them.
    result = r.post(url, headers=header, json=order_params).json()

    return result['orderCreateTransaction']


def stream(call_type, params):
    with open('config.json') as config:
        config = json.load(config)

    header = config.get('header', None)
    url = config.get('stream_url', None)

    result = r.get(url + call_type, headers=header, params=params, stream=True)

    return result
