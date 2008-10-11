#!/usr/bin/env ruby
# -*- coding: utf-8 -*-
require 'hebo'
require 'kconv'

if RUBY_VERSION < '1.9.0'
  class Array
    def choice
      at(rand(size))
    end
  end
end

class Hebopy < Hebo::Application
  def index
    if request['id'] and request['title'] != '' and request['body'] !=''
      id = request['id']
      @db[id] = { 
        :title => request['title'].toutf8,
        :body => request['body'].toutf8,
      }
    end

    id ||= @db.keys.choice
    return create unless @db.exist?(id)
    @title = html_escape(@db[id][:title])
    @body = html_escape(@db[id][:body]).gsub(/\n/, "<br>")
    render("templates/page")
  end

  def create
    @id = create_id
    render("templates/create")
  end

  #private
  def initialize
    @db = Hebo::Database.new('db/hebopy.pstore')
    @charset = "utf-8"
  end

  def create_id
    s = "0123456789abcdef"
    (1..s.length).inject(""){|r, x| r << s[rand(s.length)] }
  end
end

# Hebo.start Hebopy, :adapter => :webrick
Hebo.start Hebopy, :adapter => :cgi

# h = Hebopy.new
# p h.create_id
