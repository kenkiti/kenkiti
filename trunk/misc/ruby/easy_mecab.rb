# -*- coding: euc-jp -*-

class MeCab
  def initialize(option)
    @path = "/cygdrive/c/MeCab/bin/mecab.exe" # mecabへのパス
    @option = "-O wakati" mecabへの引数
  end
  def Tagger(option)
    @option = option
  end
  def parse_file(s)
    cmd_string = [@path, @option, s].join(" ")
    word_list = []
    io = IO.popen(cmd_string, "r")
    until io.eof?
      word_list.concat io.gets.split(' ')
    end
    return word_list
  end
end

# m = MeCab.new("-O wakati")
# p m.parse_file("test.txt")
