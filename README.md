# zjuGradeMonitor
A little script to monitor your grade on http://jwbinfosys.zju.edu.cn

### requirement
 - python3
 - requests
 - Pillow


Before you deploy this script on your server, make sure you created a file 'secret.py' at current directory.

One Example of secret.py
```
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Secret App Key, student id, password and so on"""

"""Required if you use option --send-by-sms"""
APP_KEY = '12345678'
APP_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
URL_SMS_REQUEST = 'https://eco.taobao.com/router/rest'
SMS_REC_NUM = '13712345678'
SMS_TEMPLATE_CODE = 'SMS_12345678'
SMS_SIGN_NAME = 'XXXX'
SMS_TYPE = 'normal'
SMS_EXTEND = ''

"""Required if you use option --send-by-email"""
MAIL_SERVER = 'localhost'
MAIL_SENDER = 'sender@example.com'
MAIL_RECVER = 'recver@example.com'

"""Your Personal Information"""
STUDENT_ID = '31xxxxxxxx'
PASSWORD = 'xxxxxx'

```

### Usage
`python3 monitor.py [--options]`
 - --debug : debug mode
 - --send-by-email : Send notification email to you by your smtp server
 - --send-by-sms : Send notification sms to you by alidayu api, you will need a SMS_TEMPLATE that contains 4 variables (${name}, ${grade}, ${credit}, ${point}), Example: "New Grade! 课程:${name}, 成绩:${grade}, 学分:${credit}, 绩点:${point}"