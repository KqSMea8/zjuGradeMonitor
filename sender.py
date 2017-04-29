#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Alidayu sms SDK
'''

from hashlib import md5
from time import time
from exceptions import ApiParamsException, ApiRecvException, ApiSendException
import requests

class Sender(object):
    """Short message sender based on alidayu api"""
    def __init__(self, key, secret, url='https://gw.api.tbsandbox.com/router/rest'):
        self.key = key
        self.secret = secret
        self.url = url

    def sign(self, params):
        """Calculate the signature of params"""
        if isinstance(params, dict):
            params = ''.join([''.join([k, v]) for k, v in sorted(params.items())])
            params = ''.join([self.secret, params, self.secret])
        return md5(params.encode('utf-8')).hexdigest().upper()

    def get_api_params(self):
        """Get all the params for api call"""
        params = {}
        for param in self.get_basic_params():
            if hasattr(self, param):
                params.__setitem__(param, getattr(self, param))
            else:
                raise ApiParamsException('Parameter {0} is needed for this api call'.format(param))
        for param in self.get_optional_params():
            if hasattr(self, param):
                params.__setitem__(param, getattr(self, param))
        return params

    def send(self):
        """Send the short message and return the response json"""
        sys_params = {
            'method': self.get_api_name(),
            'app_key': self.key,
            'timestamp': str(int(time() * 1000)),
            'format': 'json',
            'v': '2.0',
            'partner_id': '',
            'sign_method': 'md5'
        }
        params = self.get_api_params()
        sign_params = sys_params.copy()
        sign_params.update(params)
        sys_params['sign'] = self.sign(sign_params)
        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive'
        }
        sys_params.update(params)
        resp = requests.post(self.url, params=sys_params, headers=headers)
        if resp.status_code != 200:
            raise ApiRecvException('HTTP status code: {0} '.format(resp.status_code))
        rst = resp.json()
        if 'error_response' in rst:
            err_code = rst['error_response']['sub_code']
            raise ApiSendException('Message send error: {0} '.format(err_code))
        return rst

    def get_api_name(self):
        """Return the api name"""
        return 'alibaba.aliqin.fc.sms.num.send'

    def get_basic_params(self):
        """Basic params for sms send, not optional"""
        return ['sms_type', 'sms_free_sign_name', 'rec_num', 'sms_template_code']

    def get_optional_params(self):
        """Get optional params name"""
        return ['extend', 'sms_param']
