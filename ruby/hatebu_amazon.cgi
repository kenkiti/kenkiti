#!/usr/bin/env ruby
# -*- coding: utf-8 -*-

require 'open-uri'
require 'date'
require 'rss/maker'
require 'cgi'
require 'kconv'

cgi = CGI.new
id = cgi['id']
uri = "http://b.hatena.ne.jp/#{id}/?word=www.amazon.co.jp"
begin
  dat = open(uri).read
rescue => OpenURI::HTTPError
  puts "Content-type: text/html\n\n"
  puts "指定した id が見つかりません。id を確認してください。"
  exit
end

items_amazon = dat.scan(/<dt class="bookmark"><a href="http:\/\/www.amazon.co.jp\/gp\/product\/(.+?)" class="bookmark">(.+?)<\/a><\/dt>/)
items_date = dat.scan(/<dd class="timestamp">(.+?)年(.+?)月(.+?)日<\/dd>/).map do |y, m, d|
  Time.parse("#{y}#{m}#{d} 00:00:00")
end

rss = RSS::Maker.make("2.0") do |maker|
  maker.channel.title = "recommended".to_s.toutf8
  maker.channel.link = "http://d.hatena.ne.jp/kenkitii/"
  maker.channel.description = "hatena diary for years"
  maker.items.do_sort = true
  
  items_amazon.each_with_index do |ama, i|
    t = ama[1].to_s.sub('Amazon.co.jp： ', '').to_s.toutf8
    l = "http://www.amazon.co.jp/exec/obidos/ASIN/#{ama[0]}/progrmustgoon-22/ref=nosim"

    item = maker.items.new_item
    item.title = t
    item.link = l
    item.dc_subject = t
    item.date = items_date[i]
  end
end

puts "Content-type: application/xml\n\n"
puts rss.to_s
