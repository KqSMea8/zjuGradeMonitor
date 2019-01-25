#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  A small script to monitor my grade.
"""


import sys
import os
import time
import re
import json
import smtplib
from email.mime.text import MIMEText
from exceptions import ApiParamsException, ApiSendException
#from sender import Sender
from aliyunsms.services import AliyunSMSClient as Sender
import requests
from PIL import Image
from config import URL_BASE, URL_CAPTCHA, PATH_CAPTCHA_GIF, PATH_CAPTCHA_BMP, URL_LOGIN_FIRST, \
                   URL_LOGIN_SECOND, URL_QUERY, URL_MAIN_PAGE, URL_QUERY_PAGE, LIST_RECO
try:
    from secret import APP_KEY, APP_SECRET, SMS_TYPE, URL_SMS_REQUEST, SMS_EXTEND, SMS_SIGN_NAME,\
                       SMS_TEMPLATE_CODE, STUDENT_ID, PASSWORD
except ImportError as err:
    print(err)


class Monitor:
    """
      The class that monitor grade.
      :params sid: <str> your student id
      :params pwd: <str> your password
      :params debug: <bool> debug mode
      :params mail: <bool> send notification mail to your mailbox
      :params sms: <bool> send notification by sms
    """
    def __init__(self, sid, pwd, debug=False, mail=True, sms=False):
        """
          Constructor of Monitor
        """
        self.debug = debug
        self.sms_test = True
        self.session = requests.Session()
        self.get = self.session.get
        self.post = self.session.post
        self.check_code = ''
        self.grades = []
        self.sid = sid
        self.password = pwd
        self.interval = 60
        self.state = ''
        self.flag = False
        self.mail = mail
        self.sms = sms
        self.html = ''
        self.smtp_server = None
        if self.sms:
            self.sms_sender = Sender(APP_KEY, APP_SECRET)
            #self.sms_sender.extend = SMS_EXTEND
            #self.sms_sender.sms_type = SMS_TYPE
            #self.sms_sender.sms_free_sign_name = SMS_SIGN_NAME
            #self.sms_sender.sms_template_code = SMS_TEMPLATE_CODE
        self.pattern_html = re.compile(r'<table cellspacing.+?</table>', re.S)
        self.pattern_state = re.compile(r'name="__VIEWSTATE" value="(.{45,})"')
        self.pattern_grade = re.compile(r'<td>(\(\d{4}-\d{4}-\d\)-[0-9A-Z]{8}(-\d{7}-\d)?)'
                                        r'</td><td>(.+?)</td><td>(.+?)</td><td>(\d\.\d)'
                                        r'</td><td>([.0-9]{1,5})</td><td>(.*?)</td>')
        self.data_login_fist = {
            'strXh': self.sid,
            'strMm': self.password,
            'strLx': '学生'
        }
        self.data_login_second = {
            '__EVENTTARGET': 'Button1',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            'TextBox1': self.sid,
            'TextBox2': self.password,
            'TextBox3': '',
            'RadioButtonList1': '学生',
            'Text1': ''
        }
        self.data_query = {
            '__VIEWSTATE': '',
            'ddlXN': '',
            'ddlXQ': '',
            'txtQSCJ': '',
            'txtZZCJ': '',
            'Button2': '在校学习成绩查询'
        }


    def send_grade(self):
        """
          send grade to my mailbox
        """
        if self.mail:
            mail = MIMEText(self.html, 'html', 'utf-8')
            mail['Subject'] = '出新成绩啦！！！'
            try:
                from secret import MAIL_SERVER, MAIL_SENDER, MAIL_RECVER
            except ImportError as err:
                print(err)
                MAIL_SERVER = 'localhost'
                MAIL_SENDER = ''
                MAIL_RECVER = ''
            self.smtp_server = smtplib.SMTP(MAIL_SERVER)
            mail['From'] = MAIL_SENDER
            mail['To'] = MAIL_RECVER
            try:
                self.smtp_server.sendmail(MAIL_SENDER, [MAIL_RECVER], mail.as_string())
                self.smtp_server.close()
            except smtplib.SMTPException as err:
                print(err)


    def run(self):
        """
          run monitor
        """
        while True:
            self.get_grade()
            time.sleep(self.interval)


    def _get_state(self, response):
        rst = re.search(self.pattern_state, response.text)
        return None if rst is None else rst.group(1)


    def open(self, url):
        """
          Open a new page, maintain the state string.
        """
        try:
            res = self.get(url)
            self.state = self._get_state(res)
        except requests.exceptions.TooManyRedirects as err:
            print(err)
            self.state = ''
            self.login()
        except requests.exceptions.ReadTimeout as err:
            print(err)
            self.state = ''
            self.login()


    def login(self):
        """
          log in
        """
        self.open(URL_BASE + URL_LOGIN_SECOND)
        self.data_login_second['__VIEWSTATE'] = self.state
        self.check_code = self.captcha()
        self.data_login_second['TextBox3'] = self.check_code
        self.post(URL_BASE + URL_LOGIN_FIRST, data=self.data_login_fist)
        login_page = self.post(URL_BASE + URL_LOGIN_SECOND, data=self.data_login_second)
        if login_page.url is not URL_BASE + URL_MAIN_PAGE:
            self.open(login_page.url)
        self.open(URL_BASE + URL_MAIN_PAGE)
        self.grades = []
        temp = self.sms
        self.sms = False
        self.get_grade()
        self.test_sms()
        self.sms = temp


    def get_grade_html(self, response):
        """
          get the html string
        """
        return re.search(self.pattern_html, response.text).group(0)


    def parser_grade(self, response):
        """
          parser grade from the response
        """
        for rst in re.findall(self.pattern_grade, response.text):
            grade = {
                'id': rst[0],
                'name': rst[2],
                'grade': rst[3],
                'credit': rst[4],
                'point': rst[5],
                'referral': rst[6]
            }
            if grade not in self.grades:
                if self.sms:
                    self.send(grade)
                    '''try:
                        from secret import SMS_REC_NUM
                    except ImportError as err:
                        print(err)
                        SMS_REC_NUM = '13208022131'
                    self.sms_sender.rec_num = SMS_REC_NUM
                    self.sms_sender.sms_param = json.dumps({
                        'name': grade['name'],
                        'grade': grade['grade'],
                        'credit': grade['credit'],
                        'point': grade['point']
                    })
                    try:
                        resp = self.sms_sender.send()
                        print(resp)
                    except ApiParamsException as err:
                        #self.sms_test = True
                        print(err)
                    except ApiSendException as err:
                        #self.sms_test = True
                        print(err)
                        #time.sleep(60)
                    #else:
                        #self.sms_test = False
                    time.sleep(1)'''
                self.grades.append(grade)
                self.flag = True


    def test_sms(self):
        self.send(self.grades[-1])


    def send(self, grade):
        try:
            from secret import SMS_REC_NUM
        except ImportError as err:
            print(err)
            SMS_REC_NUM = '13276719789'
        param = {'name':grade['name'],'grade':grade['grade'],'credit':grade['credit'],'point':grade['point']}
        self.sms_sender.send_sms(SMS_REC_NUM, SMS_SIGN_NAME, SMS_TEMPLATE_CODE, param)


    def get_grade(self):
        """
          query grade
        """
        self.open(URL_BASE + URL_QUERY_PAGE)
        self.data_query['__VIEWSTATE'] = self.state
        response = self.post(URL_BASE + URL_QUERY.format(self.sid), data=self.data_query)
        self.parser_grade(response)
        if self.flag:
            self.html = self.get_grade_html(response)
            #self.send_grade()
            self.flag = False


    def captcha(self):
        """
          get the captcha string
        """
        num_captcha = []
        img_page = self.get(URL_BASE + URL_CAPTCHA)
        self._save_img(img_page)
        img_captcha = Image.open(PATH_CAPTCHA_BMP)
        for i in range(0, 5):
            distance = [0 for j in range(0, 9)]
            img_part = img_captcha.crop((5 + i * 9, 5, 13 + i * 9, 17))
            pixels = img_part.load()
            lst_pixles = [0 if pixels[j, i] is 0 else 1 for i in range(0, 12) for j in range(0, 8)]
            for j in range(0, 9):
                for index, value in enumerate(lst_pixles):
                    distance[j] += abs(value - LIST_RECO[j][index])
            min_index = 0
            min_value = distance[0]
            for dindex, value in enumerate(distance):
                if min_value > value:
                    min_index = dindex
                    min_value = value
            num_captcha.append(str(min_index))
        img_captcha.close()
        self._del_img()
        if self.debug:
            print(''.join(num_captcha))
        return ''.join(num_captcha)


    def _save_img(self, response):
        """
          save captcha image
        """
        if os.path.exists(PATH_CAPTCHA_GIF):
            os.remove(PATH_CAPTCHA_GIF)
        with open(PATH_CAPTCHA_GIF, 'wb') as _fp:
            for chunk in response.iter_content(chunk_size=1024*16):
                if chunk:
                    _fp.write(chunk)
        _fp.close()
        img = Image.open(PATH_CAPTCHA_GIF)
        img = img.convert('1')
        img.save(PATH_CAPTCHA_BMP)
        img.close()


    def _del_img(self):
        """
          delete captcha image
        """
        if os.path.exists(PATH_CAPTCHA_BMP):
            os.remove(PATH_CAPTCHA_BMP)
        if os.path.exists(PATH_CAPTCHA_GIF):
            os.remove(PATH_CAPTCHA_GIF)


    def set_interval(self, interval):
        """
          Set the interval for monitor
        """
        self.interval = interval


def main():
    """
      main function, the main purpose of this function is to stop pylint from complain
    """
    _debug = True if '--debug' in sys.argv else False
    _mail = True if '--send-by-email' in sys.argv else False
    _sms = True if '--send-by-sms' in sys.argv else False
    grade_monitor = Monitor(STUDENT_ID, PASSWORD, debug=_debug, mail=_mail, sms=_sms)
    grade_monitor.login()
    grade_monitor.run()


if __name__ == '__main__':
    main()
