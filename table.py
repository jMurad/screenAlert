from bs4 import BeautifulSoup
from requests import post, get, Session


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
        session = Session()
        session.post(self.url_auth, data=self.payload, headers=self.headers1, allow_redirects=False)
        page = session.get(self.target, headers=self.headers2, allow_redirects=False)
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
                        alarms.append(['[Отлично]', self.hor_h[c_iter], self.ver_h[r_iter], 'green'])
                    if 'disaster-bg' in colz.get('class'):
                        alarms.append(['[Плохо  ]', self.hor_h[c_iter], self.ver_h[r_iter], 'red'])
                    if 'average-bg' in colz.get('class'):
                        alarms.append(['[Средне ]', self.hor_h[c_iter], self.ver_h[r_iter], 'yellow'])
                c_iter += 1
            r_iter += 1
        return alarms
