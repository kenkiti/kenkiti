#! -*- coding: utf-8 -*-
from core.nichan import *
import yaml

_encoding = "utf-8"

class Config(list):
    def __init__(self, path_to_config='config.yaml'):
        self.path_to_config = path_to_config
        for x in yaml.load(open(self.path_to_config))['boards']:
            self.append(Storage(x))

    def save(self, dat):
        dat = yaml.dump(dat, default_flow_style=False)
        open(self.path_to_config,'w').write(dat)

def thread_search(board_url, keyword=""):
    """ The thread which is include keyword and
    the most power in the bulliten board is returned."""
    threads = Board(board_url)
    key = re.compile(keyword.encode(_encoding))
    lst = [(th.title, th.power) for th in threads if th.count != 1001 and key.search(th.title)]
    return lst and sorted(lst, key=lambda x: x[1], reverse=True)[:20] or None

def run():
    config = Config()
    for c in config:
        ret = thread_search(c.board, c.keyword)
        if not ret: continue

        for title, power in ret:
            print title, power
        
if __name__ == '__main__':
    run()
