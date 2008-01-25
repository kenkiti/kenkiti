#!/usr/bin/env ruby
# -*- coding: utf-8 -*-

require 'open-uri'
require 'date'
require 'rss/maker'
require 'cgi'
require 'kconv'

cgi = CGI.new
id = cgi['id']
uri = "http://d.hatena.ne.jp/#{id}/#{Date.today.strftime("____%m%d")}"
begin
  dat = open(uri).read
rescue => OpenURI::HTTPError
  puts "Content-type: text/html\n\n"
  puts "指定した id が見つかりません。id を確認してください。"
  exit
end

dat.gsub!(/\n|\r/,"")
title = dat.scan(/<title>(.+?)<\/title>/)
dat = dat.scan(/<!--(<rdf:RDF.+?rdf:RDF>)-->/)[1].to_s
items_title = dat.scan(/dc:title="(.+?)"/)
items_about = dat.scan(/rdf:about="(.+?)"/)
items_link  = dat.scan(/dc:identifier="(.+?)"/)
items_date = items_link.map do |item|
  item.to_s.scan(/\/#{id}\/([0-9]{4})([0-9]{2})([0-9]{2})\//).join("/") + " 00:00:00"
end

rss = RSS::Maker.make("2.0") do |maker|
  maker.channel.title = title.to_s.toutf8
  maker.channel.link = "http://b.hatena.ne.jp/#{id}/"
  maker.channel.description = "rss for amazon affiliate"
  maker.items.do_sort = true
  
  items_title.zip(items_about, items_link, items_date).each do |t,a,l,d|
    item = maker.items.new_item
    item.title = t.to_s.toutf8
    item.link = l.to_s
    item.dc_subject = t.to_s.toutf8
    item.date = Time.parse(d)
  end
end

puts "Content-type: application/xml\n\n"
puts rss.to_s



