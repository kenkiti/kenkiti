#! -*- coding: utf-8 -*-

import os, sys, yaml, datetime, time
import httplib, urlparse, re, gzip, StringIO
from urlparse import urljoin

__version__ = "0.01" 
_encoding = "utf-8"

class Storage(dict):
    def __getattr__(self, key): 
        if self.has_key(key): 
            return self[key]
        raise AttributeError, repr(key)
    def __setattr__(self, key, value): 
        self[key] = value
    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'

class Logger:
    def _now(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def info(self, message):
        m = "[%s] %s" % (self._now(), str(message))
        sys.stdout.write(m + "\n")
        sys.stdout.flush()

class Config(dict):
    def __init__(self, path_to_config='config.yaml'):
        self.path_to_config = path_to_config
        self['boards'] = []
        self['threads'] = []
        for x in  yaml.load(open(self.path_to_config))['boards']:
            self['boards'].append(x['board'])
            self['threads'].append(x['thread'])

    def __getattr__(self, key): 
        if self.has_key(key): 
            return self[key]
        raise AttributeError, repr(key)

    def __setattr__(self, key, value): 
        self[key] = value
    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'

    def save(self, dat):
        dat = yaml.dump(dat, default_flow_style=False)
        open(self.path_to_config,'w').write(dat)

class Nichan:
    # Dat URL: http://(host)/(board)/dat/(dat-id).dat
    # Char Code: Shift-jis
    # Line Format: Name<>Mail<>Date、ID<>Message<>Thread Title(exists in only first line.)
    Title = None
    Header = {'User-Agent': 'Monazilla/1.00 (Palloo/Dev)',
              'Accept-Encoding': 'gzip'}

    Path = None
    Last_Modified = None
    Range = 0
    Line = 0
    ETag = None
    Live = True

    def _dat2html(self, dat):
        br = re.compile("<br>")
        del_tag = re.compile("<.+?>")
        dat = br.sub('\n', dat)
        dat = del_tag.sub('', dat)
        dat = dat.replace("&amp;","&"); # &
        dat = dat.replace("&lt;","<"); # <
        dat = dat.replace("&gt;",">"); # >
        dat = dat.replace("&nbsp;"," "); # half-width space
        return dat

    def _dat2time(self, filename):
        posix_timestamp = int(filename[:-4])
        return datetime.datetime.fromtimestamp(posix_timestamp)

    def _timedelta(self, now, date):
        delta = now - date
        return delta.days + float(delta.seconds) / (24 * 60 * 60)

    def get_threads_list(self, board_url):
        data = None
        header = self.Header.copy()
        url = urljoin(board_url, "subject.txt")

        (scheme, location, objpath, param, query, fid) = \
                 urlparse.urlparse(url, 'http')
        con = httplib.HTTPConnection(location)
        con.request('GET', objpath, data, header)
        response = con.getresponse()

        dat = response.read()
        if response.getheader('Content-Encoding', None)=='gzip':
            gzfile = StringIO.StringIO(dat)
            gzstream = gzip.GzipFile(fileobj=gzfile)
            dat = gzstream.read()

        num = re.compile("\((\d+?)\)$")
        now = datetime.datetime.now()
        thread_list = []
        for line in dat.strip("\n").split("\n"):
            line = line.split("<>")
            title = unicode(line[1], "cp932", "ignore").encode(_encoding)
            create_date = self._dat2time(line[0])
            count = int(num.search(title).group(1))
            power = float(count) / self._timedelta(now, create_date)
            thread_list.append(Storage({'title': title, 'date': create_date, 'count': count, 'dat': line[0], 'power': power}))

        return thread_list

def thread_search(board_url, keyword=""):
    """ The thread which is include keyword and
    the most power in the bulliten board is returned."""
    bbs = Nichan()
    threads = bbs.get_threads_list(board_url)

    key = re.compile(keyword.encode(_encoding))
    power_list = [(th.title, th.power) for th in threads if not th.count == 1001 and key.search(th.title)]
    if not power_list:
        return None

    power_list.sort(lambda x,y: cmp(y[1],x[1]))
    return power_list[:20]

def run():
    # initialize
    config = Config()

    # main routine
    for board, keyword in zip(config.boards, config.keyword):
        for title, power in thread_search(borad, keyword):
            print title, power
        
if __name__ == '__main__':
    run()
