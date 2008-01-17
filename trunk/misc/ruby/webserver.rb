require 'webrick'

rubybin = '/opt/local/bin/ruby'
document_root = Dir::pwd + "/"
cgi_files = Dir::glob("#{Dir::pwd}/*.rb").map {|f| "/#{File::basename(f)}"}

server = WEBrick::HTTPServer.new({
  :DocumentRoot => document_root,
  :BindAddress => '0.0.0.0',
  :CGIInterpreter => rubybin,
  :Port => 10083
})

p document_root
p cgi_files

cgi_files.each {|cgi_file|
  server.mount(cgi_file, WEBrick::HTTPServlet::CGIHandler, document_root + cgi_file)
}

['INT', 'TERM'].each {|signal|
  Signal.trap(signal){ server.shutdown }
}

server.start


# require 'webrick'

# document_root = '/Users/tadashi/work/hatena/'
# rubybin = '/opt/local/bin/ruby'

# server = WEBrick::HTTPServer.new({
#   :DocumentRoot => document_root,
#   :BindAddress => '0.0.0.0',
#   :CGIInterpreter => rubybin,
#   :Port => 10080
# })

# ['/rss.rb'].each {|cgi_file|
#   server.mount(cgi_file, WEBrick::HTTPServlet::CGIHandler, document_root + cgi_file)
# }

# ['INT', 'TERM'].each {|signal|
#   Signal.trap(signal){ server.shutdown }
# }

# server.start
