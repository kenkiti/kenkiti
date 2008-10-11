#!/usr/bin/env ruby
# -*- coding: utf-8 -*-
# Created: February 16,2008 Saturday 01:38:38
# Author: kenkiti (INOUE Tadashi)
# $Id$
# description: A simple web framework - Hebo.rb

require 'erb'
require 'rubygems'
require 'rack'
require 'pstore'

module Hebo

  class << self
    def start(k, options)
      unless defined? @@instance
        f = caller.first[/^(.*?):\d+/, 1]
        $LOADED_FEATURES << f unless $LOADED_FEATURES.include?(f)
        @@instance = k.new 
        app = Rack::Builder.new { 
          use Rack::CommonLogger
          use Rack::ShowExceptions
          use Rack::Lint
          use Rack::Session::Cookie
          use Rack::Reloader, 10
          run @@instance
        }.to_app

        case options[:adapter]
        when :cgi
          Rack::Handler::CGI.run app
        when :webrick
          Rack::Handler::WEBrick.run app, :Port => 10080
        else
          raise AdapterError
        end
      end
    end
  end

  class Application
    include ERB::Util
    attr_reader :request
    attr_accessor :session

    def render(path_to_file)
      erb = ERB.new(open(path_to_file).read)
      erb.result(binding)
    end

    def main(env)
      req = Rack::Request.new(env)
      @request = req.params 
      @session = env["rack.session"]

      body = handle(req)
      if body
        http_response(body)
      else
        [404, {"Content-Type" => "text/plain"}, ["404 File Not Found"]]
      end

    end
    alias :call :main

    private
    def handle(req)
      cmd, *args = parse_request(req)
      return nil unless self.methods.include?(cmd)

      n = method(cmd.to_sym).arity
      case n
      when 0
        __send__(cmd)
      else
        args = args + [nil] * (n - args.length) if n > args.length 
        __send__(cmd, *args[0..n-1]) 
      end
    end

    def parse_request(req)
      @debug = Dir.pwd
      # @debug = req.inspect
      r = req.path_info.split("/")
      r = r.select {|x| x != File.basename(__FILE__) }
      return ['index'] if r.empty?
      r[1, r.length]
    end

    def http_response(body)
      out = Rack::Response.new
      out.write body
      out.finish
    end
  end

  class Database
    def initialize(path)
      @pstore = PStore.new(path)
    end
    
    def exist?(id)
      @pstore.transaction(true) {|ps| ps.root?(id) }
    end
    
    def keys
      @pstore.transaction(true) {|ps| ps.roots }
    end
    
    def [](id)
      @pstore.transaction(true) do |store|
        store[id]
      end
    end
    
    def []=(id, data)
      @pstore.transaction do |store|
        store[id.to_s] = data
      end
    end
    
    def delete(id)
      @pstore.delete(id)
    end
  end

end
