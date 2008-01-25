#!/usr/bin/env ruby
# -*- coding: utf-8 -*-
require 'webrick'
module WEBrick
  module HTTPServlet
    FileHandler.add_handler("rb", CGIHandler)
  end
end

rubybin = '/usr/bin/ruby'
document_root = './'

server = WEBrick::HTTPServer.new({
  :DocumentRoot => document_root, 
  :BindAddress => '127.0.0.1',
  :CGIInterpreter => rubybin,
  :Port => 10080
})

['INT', 'TERM'].each {|signal|
  Signal.trap(signal){ server.shutdown }
}

server.start
