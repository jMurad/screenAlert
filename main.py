from __future__ import print_function
from desktopmagic.screengrab_win32 import (getDisplayRects, saveScreenToBmp, saveRectToBmp,
                                           getScreenAsImage, getRectAsImage, getDisplaysAsImages)
from time import strftime, localtime, sleep
from requests import post, get, Session
from PIL import Image
from PIL import ImageFile
import os
import json
from bs4 import BeautifulSoup


ImageFile.MAXBLOCK = 2**20


def convertBMP2JPG(dir, file):
    oldFile = os.path.join(dir, file)
    assert(oldFile.endswith('.bmp'))
    newFile = oldFile[0:len(oldFile)-3] + 'jpg'
    print("%s to %s" % (oldFile, newFile))
    I = Image.open(oldFile)
    I.save(newFile, "JPEG", quality=80, optimize=True, progressive=True)
    os.remove(oldFile)


def screen_shoter():
    new_im = Image.new('RGB', (1920, 3240))
    for i, dr in enumerate(getDisplayRects()):
        if i > 0:
            saveRectToBmp(f'screen_{i}.bmp', rect=dr)
            # convertBMP2JPG('', f'screen_{i}.bmp')
            im = Image.open(f'screen_{i}.bmp')
            new_im.paste(im, (0, (i - 1) * 1080))
    new_im.save('out.jpg', 'JPEG', quality=30, optimize=True, progressive=True)
    return 'out.jpg'


class Zabbix:
    url_auth = 'http://10.83.0.73/zabbix/index.php'
    target = 'http://10.83.0.73/zabbix/overview.php?fullscreen=0&groupid=0&hostid=10214&show_triggers=2&ack_status=1&' \
             'show_severity=0&txt_select=&application=&inventory%5B0%5D%5Bfield%5D=type&inventory%5B0%5D%5Bvalue%5D=&' \
             'show_maintenance=1&filter_set=1'
    payload = "name=murad&password=murad&autologin=1&enter=Sign+in"
    headers1 = {'content-type': 'application/x-www-form-urlencoded',
                       'cookie': 'PHPSESSID=ssvifq8rfec4bef9vf9d816rr1',
                       'referer': 'http://10.83.0.73/zabbix/index.php'
            }
    headers2 = {'Accept-Encoding': 'gzip, deflate',
                       'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8',
                       'Connection': 'keep-alive',
                       'cookie': 'PHPSESSID=ssvifq8rfec4bef9vf9d816rr1; zbx_sessionid=7973ff8b56fc525c1c115d4f7fe786e1',
                       'Referer': 'http://10.83.0.73/zabbix/overview.php?fullscreen=0&groupid=0&hostid=10214&'
                                  'show_triggers=2&ack_status=1&show_severity=0&txt_select=&application=&'
                                  'inventory%5B0%5D%5Bfield%5D=type&inventory%5B0%5D%5Bvalue%5D=&'
                                  'show_maintenance=1&filter_set=1'
            }
    hor_h = []
    ver_h = []

    def __init__(self):
        self.session = Session()
        self.session.post(self.url_auth, data=self.payload, headers=self.headers1, allow_redirects=False)
        page = self.session.get(self.target, headers=self.headers2, allow_redirects=False)
        html_string = page.content
        soup = BeautifulSoup(html_string, 'lxml')
        table = soup.find_all('table')[1]

        row = table.find_all('tr')[0]
        columns = row.find_all('th')

        for column in columns[1:]:
            con = column.get_text()
            self.hor_h.append(con)

        for row in table.find_all('tr')[1:]:
            columns = row.find_all('td')
            con = columns[0].get_text()
            self.ver_h.append(con)

    def update_zabbix(self):
        page = self.session.get(self.target, headers=self.headers2, allow_redirects=False)
        html_string = page.content
        soup = BeautifulSoup(html_string, 'lxml')
        table = soup.find_all('table')[1]

        alarms = []
        r_iter = 0
        for rowz in table.find_all('tr')[1:]:
            c_iter = 0
            columns = rowz.find_all('td')
            for colz in columns[1:]:
                if colz.get('class') != None and 'blink' in colz.get('class'):
                    if 'normal-bg' in colz.get('class'):
                        alarms.append(['Отлично', self.hor_h[c_iter], self.ver_h[r_iter], 'green'])
                    if 'disaster-bg' in colz.get('class'):
                        alarms.append(['Плохо', self.hor_h[c_iter], self.ver_h[r_iter], 'red'])
                    if 'average-bg' in colz.get('class'):
                        alarms.append(['Средне', self.hor_h[c_iter], self.ver_h[r_iter], 'yellow'])
                c_iter += 1
            r_iter += 1
        return alarms


class BotHandler:
    def __init__(self, token, tproxi):
        self.token = token
        self.tproxi = tproxi
        self.api_url = f'https://api.telegram.org/bot{token}/'

    def get_updates(self, offset, timeout=60):
        method = 'getUpdates'
        if offset is None:
            params = {'timeout': timeout}
        else:
            params = {'offset': offset, 'timeout': timeout}
        resp = get(self.api_url + method, params, proxies=self.tproxi)
        print('\nResponse:\n', resp.text, '\n----------------------\n')
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        keyboard = [['Скриншот'], ['Zabbix']]
        reply_markup = {}
        reply_markup['keyboard'] = keyboard
        reply_markup['resize_keyboard'] = True
        # reply_markup['one_time_keyboard'] = True
        rm = json.dumps(reply_markup)
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': rm}
        method = 'sendMessage'
        resp = post(self.api_url + method, params, proxies=self.tproxi)
        return resp

    def send_photo(self, chat_id, photo, caption=''):
        data = {'chat_id': chat_id, 'caption': caption}
        files = {'photo': open(photo, 'rb')}
        method = 'sendPhoto'
        resp = post(self.api_url + method, data=data, files=files, proxies=self.tproxi)
        return resp

    def send_document(self, chat_id, doc, caption=''):
        data = {'chat_id': chat_id, 'caption': caption}
        files = {'document': open(doc, 'rb')}
        method = 'sendDocument'
        resp = post(self.api_url + method, data=data, files=files, proxies=self.tproxi)
        return resp

    def get_last_update(self):
        while 1:
            get_result = self.get_updates(None)
            print('\nLastUpdate:\n', get_result, '\n----------------------\n')
            if len(get_result) > 0:
                return get_result[-1]
            else:
                sleep(2)


# tproxi = {'https': 'https://1B1N4b:9DmEJD@212.81.37.69:9729'}
tproxi = {'https': 'https://0YdVuG:PBTMPFRS6V@188.130.128.150:1050'}
token = '526052115:AAHllTvUDLDeGyYDxIvRZsPYwXklLXSu7zk'
teleBot = BotHandler(token, tproxi)
zabbix = Zabbix()


def main():
    new_offset = None
    while 1:
        teleBot.send_message('422322499', '')
        teleBot.get_updates(new_offset)

        last_update = teleBot.get_last_update()

        last_update_id = last_update['update_id']
        last_chat_text = last_update['message']['text']
        last_chat_id = last_update['message']['chat']['id']
        last_chat_name = last_update['message']['chat']['first_name']

        if last_chat_text.lower() == 'скриншот':
            now = strftime('\n%d.%m.%Y  %H:%M:%S:\n', localtime())
            teleBot.send_document(last_chat_id, screen_shoter(), 'Время: ' + now)
        elif last_chat_text.lower() == 'zabbix':
            data = zabbix.update_zabbix()
            text = ''
            for dt in data:
                text += dt[2] + ': [' + dt[1] + ' --> ' + dt[0] + ']\n'
            print(zabbix.update_zabbix())
            now = strftime('\n%d.%m.%Y  %H:%M:%S:\n', localtime())
            teleBot.send_message(last_chat_id, 'Время: ' + now + '\n' + text)

        print('\nMessage:\n' + last_chat_text.lower() + '\n----------------------\n')
        new_offset = last_update_id + 1
        print('\n======\nla:', last_update_id, '\nno:', new_offset, '\n======\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
