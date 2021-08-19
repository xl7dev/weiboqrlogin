import requests
import time
import re
import json
import datetime
from io import BytesIO
from PIL import Image
import logging


class weibo:
    def __init__(self):
        self.qr_check_res = ''
        self.regex = re.compile('\((.*)\)')

    def get_qrcode_url(self):
        """
        获取二维码
        :return:
        """
        stamp = self.get_time_stamp()
        qrcode_url = 'https://login.sina.com.cn/sso/qrcode/image?entry=weibo&size=180&callback=STK_{0}'.format(stamp)
        req = requests.get(qrcode_url).text
        res = json.loads(self.regex.findall(req)[0])
        if res['msg'] == 'succ':
            logging.info("获取二维码成功!")
            image = 'https:{0}'.format(res['data']['image'])
            qrid = res['data']['qrid']
            return image, qrid

    def get_qrcode_echo(self, image, qrid):
        """
        显示二维码图片
        :return:
        """
        echo = BytesIO(requests.get(image).content)
        Image.open(echo).show()
        stamp = self.get_time_stamp()
        while '50114002' not in self.qr_check_res:
            qr_check_url = 'https://login.sina.com.cn/sso/qrcode/check?entry=sso&qrid={}&callback=STK_{}'.format(
                qrid,
                stamp)
            self.qr_check_res = requests.get(qr_check_url).text
            time.sleep(2)
        logging.info("显示二维码成功!")
        return True

    def get_qrcode_alt(self, qrid):
        """
        获取扫描成功返回的
        :return:
        """
        stamp = self.get_time_stamp()
        url = "https://login.sina.com.cn/sso/qrcode/check?entry=weibo&qrid={}&callback=STK_{}".format(qrid, stamp)
        req = requests.get(url).text
        res = json.loads(self.regex.findall(req)[0])
        if res['msg'] == 'succ':
            logging.info("二维码扫描成功!")
            alt = res['data']['alt']
            return alt

    def get_sso_cookie(self, alt):
        """
        获取Set-cookie
        :param alt:
        :return:
        """
        stamp = self.get_time_stamp()
        url = "https://login.sina.com.cn/sso/login.php?entry=weibo&returntype=TEXT&crossdomain=1&cdult=3&domain=weibo.com&alt={}&savestate=30&callback=STK_{}".format(
            alt, stamp)
        req = requests.get(url)
        res = self.regex.findall(req.text)
        if 'uid' in res:
            cookies = req.headers['Set-Cookie']
            logging.info("登录成功,cookie：{}".format(cookies))
            return cookies

    def get_time_stamp(self):
        datetime_now = datetime.datetime.now()
        date_stamp = str(int(time.mktime(datetime_now.timetuple())))
        data_microsecond = str("%06d" % datetime_now.microsecond)
        date_stamp = date_stamp + data_microsecond
        return int(date_stamp)

    def login(self):
        """
        登录
        :return:
        """
        image, qrid = self.get_qrcode_url()
        r = self.get_qrcode_echo(image, qrid)
        if r:
            alt = self.get_qrcode_alt(qrid)
            cookies = self.get_sso_cookie(alt)
            return cookies


if __name__ == "__main__":
    demo = weibo()
    print(demo.login())
