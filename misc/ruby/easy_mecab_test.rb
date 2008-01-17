#!/bin/ruby -Ks
# -*- coding: euc-jp -*-
require 'easymecab'
puts open("test.txt").read

m = MeCab.new("-O wakati")
p m.parse_file("test.txt")
m = MeCab.new("")
p m.parse_file("test.txt")
