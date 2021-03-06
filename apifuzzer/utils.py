import argparse
import json
import logging
import os
from base64 import b64encode
from binascii import Error
from io import BytesIO
from logging import Formatter
from logging.handlers import SysLogHandler
from random import SystemRandom
from typing import Optional

import pycurl
from bitstring import Bits


def secure_randint(minimum, maximum):
    """
    Provides solution for B311 "Standard pseudo-random generators are not suitable for security/cryptographic purposes."
    :param minimum: minimum value
    :type minimum: int
    :param maximum: maximum value
    :type maximum: int
    :return: random integer value between min and maximum
    """
    rand = SystemRandom()
    return rand.randrange(start=minimum, stop=maximum)


def set_logger(level='warning', basic_output=False):
    fmt = '%(process)d [%(levelname)s] %(name)s: %(message)s'
    if basic_output:
        logging.basicConfig(format=fmt)
        logger = logging.getLogger()
    else:
        logger = logging.getLogger()
        if not len(logger.handlers):
            handler = logging.StreamHandler()
            if os.path.exists('/dev/log'):
                handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL2)
            handler.setFormatter(Formatter('%(process)d [%(levelname)s] %(name)s: %(message)s'))
            logger.addHandler(handler)
    logger.setLevel(level=level.upper())
    return logger


def transform_data_to_bytes(data_in):
    if isinstance(data_in, float):
        return bytes(int(data_in))
    elif isinstance(data_in, str):
        return bytes(data_in, 'utf-16')
    elif isinstance(data_in, Bits):
        return data_in.tobytes()
    else:
        return bytes(data_in)


def set_class_logger(class_name):
    class_name.logger = logging.getLogger(class_name.__class__.__name__)
    class_name.logger.getChild(class_name.__class__.__name__)
    return class_name


def try_b64encode(data_in):
    try:
        return b64encode(data_in)
    except (TypeError, Error):
        return data_in


def container_name_to_param(container_name):
    return container_name.split('|')[-1]


def init_pycurl(debug=False):
    """
    Provides an instances of pycurl with basic configuration
    :return: pycurl instance
    """
    _curl = pycurl.Curl()
    _curl.setopt(pycurl.SSL_OPTIONS, pycurl.SSLVERSION_TLSv1_2)
    _curl.setopt(pycurl.SSL_VERIFYPEER, False)
    _curl.setopt(pycurl.SSL_VERIFYHOST, False)
    _curl.setopt(pycurl.VERBOSE, debug)
    _curl.setopt(pycurl.TIMEOUT, 10)
    _curl.setopt(pycurl.COOKIEFILE, "")
    _curl.setopt(pycurl.USERAGENT, 'APIFuzzer')
    return _curl


def download_file(url, dst_file):
    _curl = init_pycurl()
    buffer = BytesIO()
    _curl = pycurl.Curl()
    _curl.setopt(_curl.URL, url)
    _curl.setopt(_curl.WRITEDATA, buffer)
    _curl.perform()
    _curl.close()
    buffer.seek(0)
    with open(dst_file, 'wb') as tmp_file:
        tmp_file.write(buffer.getvalue())
    buffer.close()


def get_item(json_dict, json_path):
    """
    Get JSON item defined by path
    :param json_dict: JSON dict contains the item we are looking for
    :type json_dict: dict
    :param json_path: defines the place of the object
    :type json_path: list
    :return: dict
    """
    for item in json_path:
        json_dict = json_dict.get(item, {})
    return json_dict


def pretty_print(printable, limit=200):
    if isinstance(printable, dict):
        return json.dumps(printable, indent=2, sort_keys=True)[0:limit]
    else:
        return printable


def json_data(arg_string: Optional[str]) -> dict:
    """
    Transforms input string to JSON. Input must be dict or list of dicts like string
    :type arg_string: str
    :rtype dict
    """
    if isinstance(arg_string, dict) or isinstance(arg_string, list):  # support testing
        arg_string = json.dumps(arg_string)
    try:
        _return = json.loads(arg_string)
        if hasattr(_return, 'append') or hasattr(_return, 'keys'):
            return _return
        else:
            raise TypeError('not list or dict')
    except (TypeError, json.decoder.JSONDecodeError):
        msg = '%s is not JSON', arg_string
        print('Debugging: %s', arg_string.replace(' ', '_'))
        raise argparse.ArgumentTypeError(msg)
