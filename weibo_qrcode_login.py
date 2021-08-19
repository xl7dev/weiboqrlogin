import requests
import time
import re
import json
import datetime
from io import BytesIO
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class weibo:
    def __init__(self):
        self.qr_check_res = ''
        self.source = ''
        self.cookies = ''
        self.regex = re.compile('\((.*)\)')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/69.0.3497.105 Mobile/15E148 Safari/605.1"}

    def get_qrcode_url(self):
        """
        获取二维码
        :return:
        """
        stamp = self.get_time_stamp16()
        qrcode_url = 'https://login.sina.com.cn/sso/qrcode/image?entry=weibo&size=180&callback=STK_{0}'.format(stamp)
        req = requests.get(qrcode_url, headers=self.headers).text
        res = json.loads(self.regex.findall(req)[0])
        if res['msg'] == 'succ':
            logger.info("获取二维码成功!")
            image = 'https:{0}'.format(res['data']['image'])
            qrid = res['data']['qrid']
            return image, qrid

    def get_qrcode_echo(self, image, qrid):
        """
        显示二维码图片
        :return:
        """
        echo = BytesIO(requests.get(image, headers=self.headers).content)
        Image.open(echo).show()
        stamp = self.get_time_stamp16()
        while '50114002' not in self.qr_check_res:
            qr_check_url = 'https://login.sina.com.cn/sso/qrcode/check?entry=sso&qrid={}&callback=STK_{}'.format(
                qrid,
                stamp)
            self.qr_check_res = requests.get(qr_check_url, headers=self.headers).text
            time.sleep(2)
        logger.info("显示二维码成功!")
        return True

    def get_qrcode_alt(self, qrid):
        """
        获取扫描成功返回的
        :return:
        """
        stamp = self.get_time_stamp16()
        url = "https://login.sina.com.cn/sso/qrcode/check?entry=weibo&qrid={}&callback=STK_{}".format(qrid, stamp)
        req = requests.get(url, headers=self.headers).text
        res = json.loads(self.regex.findall(req)[0])
        if res['msg'] == 'succ':
            logger.info("二维码扫描成功!")
            alt = res['data']['alt']
            return alt

    def get_sso_cookie(self, alt):
        """
        获取Set-cookie
        :param alt:
        :return:
        """
        stamp = self.get_time_stamp16()
        url = "https://login.sina.com.cn/sso/login.php?entry=weibo&returntype=TEXT&crossdomain=1&cdult=3&domain=weibo.com&alt={}&savestate=30&callback=STK_{}".format(
            alt, stamp)
        req = requests.get(url, headers=self.headers)
        res = self.regex.findall(req.text)
        if len(res) > 0:
            _res = json.loads(res[0])
            self.source = _res['uid']
            self.cookies = req.headers['Set-Cookie']
            logger.info("登录成功,cookie：{}".format(self.cookies))
            return self.cookies

    def get_time_stamp16(self):
        """
        16位时间戳
        :return:
        """
        datetime_now = datetime.datetime.now()
        date_stamp = str(int(time.mktime(datetime_now.timetuple())))
        data_microsecond = str("%06d" % datetime_now.microsecond)
        date_stamp = int(date_stamp + data_microsecond)
        return date_stamp

    def get_time_stamp13(self):
        """
        13位时间戳
        :return:
        """
        date_stamp = int(round(time.time() * 1000))
        return date_stamp

    def send_message(self, text, uid):
        """
        :param text: 消息内容
        :param uid: 对方uid
        :param clientid:
        :return:
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/69.0.3497.105 Mobile/15E148 Safari/605.1",
            "Referer": "https://api.weibo.com/chat/", "cookie": self.cookies,
            "Content-Type": "application/x-www-form-urlencoded"}
        send_url = 'https://api.weibo.com/webim/2/direct_messages/new.json'

        data = {'text': text, 'uid': uid, 'is_encoded': 0, 'decodetime': 1, 'source': self.source}
        logger.info("发送消息内容：{}".format(text))
        send_message_text = requests.post(send_url, headers=headers, data=data).json()
        date_stamp = self.get_time_stamp13()
        while True:
            url = 'https://api.weibo.com/webim/2/direct_messages/conversation.json?convert_emoji=1&count=15&max_id=0&is_include_group=0&t={}&uid={}&source={}'.format(
                date_stamp, uid,
                self.source)
            res = requests.get(url, headers=headers).json()
            get_message = res['direct_messages'][0]['text']
            if send_message_text['text'] == get_message:
                logger.info("等待回复中...")
                time.sleep(3)
            else:
                return send_message_text

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

    def test(self, text, uid):
        self.login()
        print(self.send_message(text, uid))


if __name__ == "__main__":
    demo = weibo()
    demo.test()
