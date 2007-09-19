#! -*- coding: utf-8 -*-
import sys, yaml, datetime, time
import httplib, urlparse, re, gzip, StringIO

import smtplib
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import formatdate

_VERSION = "0.1"

class Logger:
    def _now(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def info(self, message):
        m = "[%s] %s" % (self._now(), str(message))
        sys.stdout.write(m + "\n")
        sys.stdout.flush()

class Config:
    path_to_config = 'config.yaml'
    def save(self, dat):
        dat = yaml.dump(dat, default_flow_style=False)
        open(self.path_to_config,'w').write(dat)

    def load(self):
        return yaml.load(open(self.path_to_config))

class Reader:
    thread = None
    
    def set_thread(self, path, last_modified, dat_range, line):
        search_2ch = re.compile('2ch.net')
        search_jbbs = re.compile('jbbs.livedoor.jp')

        if search_2ch.search(path):
            self.thread = Nichan()
        elif search_jbbs.search(path):
            self.thread = Jbbs()
        else:
            raise

        self.thread.Path = path
        self.thread.Last_Modified = last_modified
        self.thread.Range = dat_range
        self.thread.Line = line

    def status_message(self, number):
        messages = {
            200:'スレ取得',
            206:'差分取得',
            302:'DAT落ち',
            304:'更新なし',
            404:'File Not Found',
            416:'なんかエラーだって(レスあぼーん?)',
            }
        return messages[number]

    def get(self):
        header = {'User-Agent': 'Monazilla/1.00',
                  'Accept-Encoding': 'gzip'}
        return self.thread.get(None, header)

class Jbbs:
    Path = None
    Status = 0
    Title = None
    Last_Modified = None
    Range = 0
    Line = 0

    def _convert_path_to_dat_from_url(self, url):
        "http://jbbs.livedoor.jp/bbs/rawmode.cgi/カテゴリ/板番号/DAT-ID/"
        "http://jbbs.livedoor.jp/bbs/read.cgi/otaku/7775/1189723149/"
        path = re.compile('http://(?P<host>[^\/]+)/([^\/]+)/([^\/]+)/(?P<category>[^\/]+)/(?P<board>[^\/]+)/(?P<datid>[^\/]+)/')
        m = path.search(url)
        return "http://%(host)s/bbs/rawmode.cgi/%(category)s/%(board)s/%(datid)s" % {
            'host': m.group('host'),
            'category': m.group('category'),
            'board': m.group('board'),
            'datid': m.group('datid')}

    def _convert_dat(self, dat):
        # 取得 URL http://jbbs.livedoor.jp/bbs/rawmode.cgi/カテゴリ/板番号/DAT-ID/
        # 文字コード EUC-JP
        # 行フォーマット 番号<>名前<>メール<>日付(ID)<>メッセージ<>スレッドタイトル<>
        dat = unicode(dat, 'euc-jp', 'ignore').encode('utf-8')
        dat = dat.strip("\n").split("\n")[1:]
        res = []
        for line in dat:
            num, name, mail, date, message, title, null = line.split("<>")
            res.append({'number':int(num), 'name': name, 'mail': mail, 'date': date, 'message': self._convert_message(message)})
        return  res


    def _convert_message(self, message):
        br = re.compile("<br>")
        del_tag = re.compile("<.+?>")
        message = br.sub('\n', message)
        message = del_tag.sub('', message)
        message = message.replace("&amp;","&"); # &
        message = message.replace("&lt;","<"); # <
        message = message.replace("&gt;",">"); # >
        message = message.replace("&nbsp;"," "); # 半角空白
        return message

    def _get_title(self, dat):
        dat = unicode(dat, 'euc-jp', 'ignore').encode('utf-8')
        line = dat.strip("\n").split("\n")[0]
        num, name, mail, date, message, title, null = line.split("<>")
        return title

    def _get_last_number(self, dat):
        #dat = unicode(dat, 'euc-jp').encode('utf-8')
        dat = unicode(dat, 'euc_jp','ignore').encode('utf-8')
        dat = dat.strip("\n").split("\n")
        line = dat[-1:][0]
        num, name, mail, date, message, title, null = line.split("<>")
        return int(num)

    def get(self, data, header):
        url = self.Path 
        if not url: return None

        url = self._convert_path_to_dat_from_url(url)
        if int(self.Line) > 0:
            url = "%s/%s-" % (url, self.Line)
        (scheme, location, objpath, param, query, fid) = \
                 urlparse.urlparse(url, 'http')
        con = httplib.HTTPConnection(location)
        con.request('GET', objpath, data, header)

        response = con.getresponse()
        self.Status = response.status
        self.Last_Modified =  response.getheader('Last-Modified', None)

        if response.status != 200 and response.status != 206:
            return None

        dat = response.read()
        if response.getheader('Content-Encoding', None)=='gzip':
            gzfile = StringIO.StringIO(dat)
            gzstream = gzip.GzipFile(fileobj=gzfile)
            dat = gzstream.read()

        last_number = self._get_last_number(dat)
        if self.Range == 0: self.Title = self._get_title(dat)
        if last_number > self.Line:
            self.Line = last_number
            res = self._convert_dat(dat)
        else:
            self.Status = 304
            res = None

        return res
    
class Nichan:
    Path = None
    Status = 0
    Title = None
    Last_Modified = None
    Range = 0
    Line = 0
    
    def _convert_path_to_dat_from_url(self, url):
        path = re.compile('http://(?P<host>[^\/]+)/([^\/]+)/([^\/]+)/(?P<board>[^\/]+)/(?P<thread>[^\/]+)/')
        m = path.search(url)
        return "http://%(host)s/%(board)s/dat/%(thread)s.dat" % {
            'host': m.group('host'),
            'board': m.group('board'),
            'thread': m.group('thread')}

    def _convert_dat(self, dat):
        # 文字コード Shift-jis
        # 行フォーマット 名前<>メール欄<>日付、ID<>本文<>スレタイトル(1行目のみ存在する)\n
        dat = unicode(dat, 'cp932').encode('utf-8')
        dat = dat.strip("\n").split("\n")
        res = []
        number = self.Line - len(dat)
        for line in dat:
            name, mail, date, message, thread = line.split("<>")
            number += 1
            res.append({'number': number, 'name': name, 'mail': mail, 'date': date, 'message': self._convert_message(message)})
        return res

    def _convert_message(self, message):
        br = re.compile("<br>")
        del_tag = re.compile("<.+?>")
        message = br.sub('\n', message)
        message = del_tag.sub('', message)
        message = message.replace("&amp;","&"); # &
        message = message.replace("&lt;","<"); # <
        message = message.replace("&gt;",">"); # >
        message = message.replace("&nbsp;"," "); # 半角空白
        return message

    def _get_title(self, dat):
        dat = unicode(dat, 'cp932').encode('utf-8')
        line = dat.strip("\n").split("\n")[0]
        name, mail, date, message, title = line.split("<>")
        return title

    def get(self, data, header):
        url = self.Path
        if not url: return None
        url = self._convert_path_to_dat_from_url(url)

        if self.Last_Modified:
            header['If-Modified-Since'] = self.Last_Modified
            header['Range'] = "bytes=%d-" % self.Range
            # If specified 'Last-Modified' header exist, remove 'Accept-Encoding: gzip' from Header.
            del header['Accept-Encoding']

        (scheme, location, objpath, param, query, fid) = \
                 urlparse.urlparse(url, 'http')
        con = httplib.HTTPConnection(location)
        con.request('GET', objpath, data, header)
        response = con.getresponse()
        self.Status = response.status
        self.Last_Modified = response.getheader('Last-Modified', None)

        if response.status != 200 and response.status != 206:
            return None

        dat = response.read()
        if response.getheader('Content-Encoding', None)=='gzip':
            gzfile = StringIO.StringIO(dat)
            gzstream = gzip.GzipFile(fileobj=gzfile)
            dat = gzstream.read()
        length = len(dat)
        self.Line += dat.count("\n")
        res = self._convert_dat(dat)
        if self.Range == 0: self.Title = self._get_title(dat)
        self.Range += length#len(dat)

        return res

class Gmail:
    address = None
    password = None
    
    def send_mail(self, to_addr, subject, body):
        encoding = 'ISO-2022-JP'
        msg = MIMEText(body, 'plain', encoding)
        msg['Subject'] = Header(subject, encoding)
        msg['From'] = self.address
        msg['To'] = to_addr
        msg['Date'] = formatdate()

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self.address, self.password)
        s.sendmail(self.address, [to_addr], msg.as_string())
        s.close()

def autopilot():
    c = Config()
    config = c.load()
    reader = Reader()
    logger = Logger()

    messages = ""
    for t in config['thread']:
        t.setdefault('Last-Modified', None)
        t.setdefault('Range', 0)
        t.setdefault('Line', 0)
        t.setdefault('Title', None)
        t.setdefault('Name', None)

        flg_init_thread = False
        flg_get_dat = False
        message = ""

        reader.set_thread(t['Path'], t['Last-Modified'], t['Range'], t['Line'])
        dat = reader.get()
        if reader.thread.Title:
            flg_init_thread = True
            t['Title'] = reader.thread.Title

        if reader.thread.Status == 200 or reader.thread.Status == 206:
            flg_get_dat = True
            t['Last-Modified'] = reader.thread.Last_Modified
            t['Range'] = reader.thread.Range
            t['Line'] = reader.thread.Line

        if reader.thread.Status == 416:
            t['Range'] = 0

        # The log message is displayed.
        msg = "%s:%s" % (
            reader.status_message(reader.thread.Status), t['Title'])
        logger.info(msg)

        if flg_init_thread == True or flg_get_dat == False:
            continue

        # Create message
        if t['Name']:
            name = re.compile(t['Name'])
            for d in dat:
                if not name.search(d['name']):
                    continue
                message += create_message(d['number'], d['message'])
        else:
            for d in dat:
                message += create_message(d['number'], d['message'])
        logger.info('最終書込:%s レス取得数:%d' % (dat[-1]['date'], len(dat)))
        messages += create_messages(t['Title'], message)

    c.save(config)

    if messages:
        mail = Gmail()
        mail.address = config['gmail_address']
        mail.password = config['password']
        subject = u'新着レスがあります'.encode('ISO-2022-JP', 'ignore')
        message = unicode(messages, 'utf-8').encode('ISO-2022-JP', 'ignore')
        mail.send_mail(config['to_address'], subject, message)
        logger.info("メールを送信しました。")

    logger.info("%d秒待機" % config['wait'])
    time.sleep(config['wait'])

def create_message(number, message):
    msg = """
%d %s
""" % (number, message)
    return msg

def create_messages(title, message):
    if message == "": return ""
    msg = """
-------------------
%s
-------------------
%s
""" % (title, message)
    return msg

if __name__ == '__main__':
    while True:
        msg = autopilot()
