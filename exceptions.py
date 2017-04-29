#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Exceptions"""

class ApiBaseException(Exception):
    """Base Exception of api call"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ApiParamsException(ApiBaseException):
    """Raised when one or more required params is not given"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ApiRecvException(ApiBaseException):
    """Raised when http response status code is not 200"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class ApiSendException(ApiBaseException):
    """Raised when the error code of response is not 0"""
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
