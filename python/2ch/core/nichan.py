#! -*- coding: utf-8 -*-
import os, sys, datetime, time
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

class Board(list):
    # Dat URL: http://(host)/(board)/dat/(dat-id).dat
    # Char Code: Shift-jis
    # Line Format: Name<>Mail<>Date、ID<>Message<>Thread Title(exists in only first line.)
    Header = {'User-Agent': 'Monazilla/1.00 (Palloo/Dev)',
              'Accept-Encoding': 'gzip'}

    def __init__(self, board_url):
        hoge = self._get_threads_list(board_url)
        for x in hoge:
            self.append(x)
            
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

    def _get_threads_list(self, board_url):
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

class Thread:
    pass
