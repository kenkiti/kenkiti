#! -*- coding: utf-8 -*-
import sys, yaml, datetime, time
import httplib, urlparse, re, gzip, StringIO

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
    header = {'User-Agent': 'Monazilla/1.00',
              'Accept-Encoding': 'gzip'}
    thread = None
    
    def set_thread(self, path, last_modified, dat_range):
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

    def status_message(self, number):
        messages = {
            200:'スレ取得',
            206:'差分取得',
            302:'DAT落ち',
            304:'更新なし',
            404:'File Not Found',
            416:'なんかエラーだって(レスあぼーん)',
            }
        return messages[number]

    def get(self):
        return self.thread.get(None, self.header)
    

class Jbbs:
    Path = None
    Status = 0
    Title = None
    Last_Modified = None
    Range = 0

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
        # 行 番号<>名前<>メール<>日付(ID)<>メッセージ<>スレッドタイトル<>
        dat = unicode(dat, 'euc-jp').encode('utf-8')
        dat = dat.strip("\n").split("\n")[1:]
        res = []
        for line in dat:
            num, name, mail, date, message, title, null = line.split("<>")
            res.append({'name': name, 'mail': mail, 'date': date, 'message': message})
        return  res

    def _get_title(self, dat):
        dat = unicode(dat, 'euc-jp').encode('utf-8')
        line = dat.strip("\n").split("\n")[0]
        num, name, mail, date, message, title, null = line.split("<>")
        return title

    def _get_last_number(self, dat):
        dat = unicode(dat, 'euc-jp').encode('utf-8')
        dat = dat.strip("\n").split("\n")
        line = dat[-1:][0]
        num, name, mail, date, message, title, null = line.split("<>")
        return int(num)

    def set_request(self, Path, Last_Modified, Range):
        self.Path = Path
        self.Last_Modified = Last_Modified
        self.Range = Range

    def get(self, data, header):
        url = self.Path 
        if not url: return None
        try:
            url = self._convert_path_to_dat_from_url(url)
            if int(self.Range) > 0:
                url = "%s/%s-" % (url, self.Range)
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
            if last_number > self.Range:
                self.Range = last_number
                res = self._convert_dat(dat)
            else:
                self.Status = 304
                res = None
        except:
            print "Unexpected error:", sys.exc_info()[0]
            res = None

        return res
    
class Nichan:
    Path = None
    Status = 0
    Title = None
    Last_Modified = None
    Range = 0
    
    def _convert_path_to_dat_from_url(self, url):
        path = re.compile('http://(?P<host>[^\/]+)/([^\/]+)/([^\/]+)/(?P<board>[^\/]+)/(?P<thread>[^\/]+)/')
        m = path.search(url)
        return "http://%(host)s/%(board)s/dat/%(thread)s.dat" % {
            'host': m.group('host'),
            'board': m.group('board'),
            'thread': m.group('thread')}

    def _convert_dat(self, dat):
        # 文字コード Shift-jis
        # 行 名前<>メール欄<>日付、ID<>本文<>スレタイトル(1行目のみ存在する)\n
        dat = unicode(dat, 'shift-jis').encode('utf-8')
        dat = dat.strip("\n").split("\n")
        res = []
        for line in dat:
            name, mail, date, message, thread = line.split("<>")
            res.append({'name': name, 'mail': mail, 'date': date, 'message': message})
        return res

    def _get_title(self, dat):
        dat = unicode(dat, 'shift-jis').encode('utf-8')
        line = dat.strip("\n").split("\n")[0]
        name, mail, date, message, title = line.split("<>")
        return title

    def set_request(self, Path, Last_Modified, Range):
        self.Path = Path
        self.Last_Modified = Last_Modified
        self.Range = Range

    def get(self, data, header):
        url = self.Path
        if not url: return None
        url = self._convert_path_to_dat_from_url(url)
        try:
            if self.Last_Modified:
                header['If-Modified-Since'] = self.Last_Modified
                header['Range'] = "bytes=%d" % (self.Range-1)

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
            res = self._convert_dat(dat)
            if self.Range == 0: self.Title = self._get_title(dat)
            self.Range += len(dat)

        except:
            print "Unexpected error:", sys.exc_info()[0]

        return res

def autopilot():
    c = Config()
    urls = c.load()
    r = Reader()
    l = Logger()
    for url in urls:
        url.setdefault('Last-Modified', None)
        url.setdefault('Range', 0)
        url.setdefault('Title', None)
        url.setdefault('Name', None)

        r.set_thread(url['Path'], url['Last-Modified'], url['Range'])
        dat = r.get()
        if r.thread.Title:
            url['Title'] = r.thread.Title

        message = "%s:%s %s" % (r.status_message(r.thread.Status), url['Title'], r.thread.Path)
        l.info(message)
        if url['Name']: name = re.compile(url['Name'])
        if r.thread.Status == 200 or r.thread.Status == 206:
            url['Last-Modified'] = r.thread.Last_Modified
            url['Range'] = r.thread.Range
            for res in dat:
                if url['Name']:
                    m = name.search(res['name'])
                    if m: print res['date'], res['message']

    c.save(urls)

def _test():
    c = Config()
    c.save([
        {'Path': "http://ex23.2ch.net/test/read.cgi/net/1189088895/l50"},
        {'Path': "http://ex23.2ch.net/test/read.cgi/net/1189753620/"},
        {'Path': "http://jbbs.livedoor.jp/bbs/read.cgi/otaku/7775/1189723149/", 'Name': "たか子"},
        ])

if __name__ == '__main__':
#    _test()
    autopilot()

