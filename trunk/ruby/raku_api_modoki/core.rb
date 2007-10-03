#-*- coding: utf-8 -*-
#
# core.rb
#

$KCODE='u'
require 'rubygems'
require 'mechanize'
require 'hpricot'
require 'kconv'
require 'date'

require 'open-uri'
require 'yaml'

class Logger
  def info(message)
    now = Time.now.strftime("%H:%M:%S")
    $stdout.puts "[#{now}] OK: #{message}"
  end

  def warn(message, file=nil, line=nil)
    now = Time.now.strftime("%H:%M:%S")
    if file.nil? 
      $stderr.puts "[#{now}] NG: #{message}"
    else
      $stderr.puts "[#{now}] NG: #{message} by line #{line} in #{file}."
    end
  end
end

class Rakuten
  attr_accessor :username, :password, :sex

  def initialize(username, password)
    @logger = Logger.new
    @agent = WWW::Mechanize.new
    @agent.user_agent_alias = 'Windows IE 6'
    @agent.redirect_ok = true
    @page = nil
    @wait = 2

    @username = username
    @password = password
  end 

  def _debug(fn=nil)
    if fn.nil?
      fn = Time.now.strftime("debug_%H%M%S.html")
    end
    open(fn, 'w').write(@page.body)
  end

  def login
    begin
      @page = @agent.get('https://member.id.rakuten.co.jp/rms/nid/menufwd')
      login_form = @page.forms.with.name('LoginForm').first
      login_form.u = @username
      login_form.p = @password
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = 'もう一度、正しく入力してください。'.toeuc
      status = (@page.body.toeuc =~ /#{check_string}/) == nil
    end

    if status
      @logger.info "#{@username} logined to my rakuten." 
    else
      @logger.warn "#{@username} is failed to login to my rakuten", __FILE__, __LINE__
    end
    sleep @wait
    return status
  end

  def logout
    begin
      @page = @agent.get('https://member.id.rakuten.co.jp/rms/nid/logout')
    rescue EOFError
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = 'ログアウトしました'.toeuc
      status = (@page.body.toeuc =~ /#{check_string}/) != nil
    end

    if status
      @logger.info "#{@username} is logout." 
    else
      @logger.warn "#{@username} is failed to logout.", __FILE__, __LINE__
    end
    sleep @wait
    return status
  end

  def login_plaza
    begin
      @page = @agent.get('http://plaza.rakuten.co.jp')
      login_form = @page.forms[0] # change from froms[1]
      login_form.u = @username
      login_form.p = @password
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check1 = 'このサービスをご利用になるには、ログインしてください。'.toeuc
      check2 = 'もう一度、正しく入力してください。'.toeuc
      status = (@page.body.toeuc =~ /(#{check1}|#{check2})/) == nil

      check_string = '大変申し訳ございませんが、システムエラーがおきました。'.toeuc
      error = @page.body.toeuc =~ /#{check_string}/
    end

    if error
      @logger.warn "#{@username} happend error.", __FILE__, __LINE__
      status = false
    else
      if status
        @logger.info "#{@username} logined to rakuten plaza." 
      else
        @logger.warn "#{@username} is failed to login to rakuten plaza", __FILE__, __LINE__
      end
    end
    sleep @wait
    return status
  end

  def logout_plaza
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=logout')
    rescue EOFError
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = 'ログアウトしました'.toeuc
      status = (@page.body.toeuc =~ /#{check_string}/) != nil
    end

    if status
      @logger.info "#{@username} is logout." 
    else
      @logger.warn "#{@username} is failed to logout.", __FILE__, __LINE__
    end
    sleep @wait
    return status
  end

  def post_entry(title, text, tags='')
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=diary&act=write')
      login_form = @page.forms.with.name('form1').first
      login_form.d_title = title.toeuc
      login_form.d_text = text.toeuc
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = '書き込みが完了しました'.toeuc
      status = (@page.body =~ /#{check_string}/) != nil
    end
    if status
      @logger.info "posted blog entry." 
    else
      @logger.warn "#{@username} is failed to post blog entry", __FILE__, __LINE__
      _debug
    end
    sleep @wait
    return status
  end

  def remove_entry
    begin
      page = @agent.get('http://my.plaza.rakuten.co.jp/?func=diary&act=view')
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      return false
    end

    # find delete button
    doc = Hpricot(page.body)
    urls = doc.search("//a[@href^='/?func=diary&act=view']")
    count = 0
    begin
      urls.each do |u|
        url = 'http://my.plaza.rakuten.co.jp' + u['href']

        # push delete button and confirm.
        page = @agent.get(url)
        login_form = page.forms[0]
        page = @agent.submit(login_form)
        count += 1
        sleep 1
      end
      sleep @wait
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      return false
    else
      @logger.info "deleted #{count} blog entry."
      return true
    end
  end

  def edit_nickname(name)
    # post nickname
    begin
      @page = @agent.get('https://member.id.rakuten.co.jp/rms/nid/muprofilefwd2')
      login_form = @page.forms.with.name('UProfileForm').first
      oldname = login_form.nickname
      login_form.nickname = name.toeuc
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      # if duplicate nickname, leave nickname as it is and click submit button.
      check_string = 'ニックネームに誤りがあります。'.toeuc
      if @page.body =~ /#{check_string}/
          login_form = @page.forms.with.name('UProfileForm').first
        @page = @agent.submit(login_form)
      end        
      status = true
    end

    if not status
      @logger.warn "#{username} is failed to config nickname.", __FILE__, __LINE__
      return status
    end
    sleep @wait

    # Confirm Form
    begin
      login_form = @page.forms.with.name('ConfirmForm').first
      login_form.p = @password
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      status = true
    end

    if status 
      @logger.info "#{username}'s nickname was configured."
    else
      @logger.warn "#{username} is failed to config nickname.", __FILE__, __LINE__
    end
    sleep @wait

    return status
  end

  def edit_blog_title(title)
    # post nickname
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=page&act=config')
      login_form = @page.forms.with.name('form').first
      login_form.site_name = title.toeuc
      login_form.radiobuttons.name('site_genre_id').each {|b| b.uncheck}
      login_form.radiobuttons.name('site_genre_id')[rand(19)].click
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      status = true
    end
    
    if status
      @logger.info "changed blog title and genre for #{@username}."
    else
      @logger.warn "failed to changed blog title and genre for #{@username}."
    end
    sleep @wait
    return status
  end

  def edit_diary_title(title)
    # post diary title
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=diary&act=config')
      login_form = @page.forms.with.name('form1').first
      login_form.diary_title = title.toeuc
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      status = true
    end
    
    if status
      @logger.info "changed diary title and genre for #{@username}."
    else
      @logger.warn "failed to changed diary title and genre for #{@username}."
    end
    sleep @wait
    return status
  end

  def edit_blog_design(category_num)
    @page = @agent.get("http://my.plaza.rakuten.co.jp/index.phtml?func=config&act=design&sub_act=step2&key=theme&cate=#{category_num}")

    urls = Array.new
    doc = Hpricot(@page.body)
    (doc/:html/:body/:input).each{|input|
      urls << $1 if input["onclick"] =~ /location.href='(.*?)'/
    }
    @page = @agent.get(urls[rand(urls.length)])
    login_form = @page.forms[0]
    @page = @agent.submit(login_form)

    @logger.info "changed blog design for #{@username}."
    sleep @wait
    return true
  end

  def edit_blog_top_page(string)
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=page&act=top_edit')
      login_form = @page.forms.with.name('page_content').first
      login_form.page_text = string
      @page = @agent.submit(login_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = '登録が完了しました'.toeuc
      status = (not (@page.body =~ /#{check_string}/).nil?)
    end
    if status 
      @logger.info "set top page contents for #{@username}."
    else
      @logger.warn "failed to top page contents for #{@username}."
    end
    sleep @wait
    return status
  end

  def _random_choice(a)
    return a[rand(a.length)]
  end

  def search(keyword)
    # search keyword
    get_query = "http://esearch.rakuten.co.jp/rms/sd/esearch/vc?e=0&sv=11&v=2&oid=000&g=0&p=0&sitem=#{keyword.toeuc}"
    @page = @agent.get(get_query)

    check_string = 'ご指定の検索キーワードでは該当商品が多すぎます'.toeuc
    unless (@page.body =~ /#{check_string}/).nil?
      @logger.warn "There are many item searching for '#{keyword}'."
      return false 
    end

    # sort search result pages.
    link = @page.links.text("買い物可能".toeuc)
    @page = @agent.get(link.href)
    link = @page.links.text("新着順".toeuc)
    @page = @agent.get(link.href)

    # get search result page.
    pages = []
    begin 
      item_forms = @page.forms.with.name("itemForm")
      item_form = _random_choice(item_forms)
      @page = @agent.submit(item_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      return false
    else
      @logger.info "search and getting affiliate pages..."
    end

    # HTML Parseing and Get Affiliate code.
    doc = Hpricot(@page.body)
    title = doc.search("//font[@color='#CC3300']").first.inner_text
    code = (doc/:html/:body/:textarea).first.inner_html
    code[code.length-5, 5] = '<br>' + title + '</a>'
    item = { :title => title, :text => code }
    sleep @wait
    return item
  end

  def delete_plaza_account
    begin
      @page = @agent.get('http://my.plaza.rakuten.co.jp/?func=etc&act=user_del')
      delete_form = @page.forms[0]
      delete_form.radiobuttons.name('kaiyaku')[1].click
      @page = @agent.submit(delete_form)
    rescue => description
      @logger.warn description.inspect, __FILE__, __LINE__
      status = false
    else
      check_string = '楽天ブログから登録を削除しました。'.toeuc
      status = (@page.body =~ /#{check_string}/) != nil
    end

    if status
      @logger.info "delete #{@username}'s blog account." 
    else
      @logger.warn "#{@username} is failed to delete account.", __FILE__, __LINE__
      _debug
    end
    sleep @wait
    return status
  end

  def get_new_feeds
    urls = Array.new
    agent = WWW::Mechanize.new
    agent.user_agent_alias = 'Windows IE 6'
    agent.redirect_ok = true
    page = agent.get('http://plaza.rakuten.co.jp/gnr/')

    while page != []
      doc = Hpricot(page.body)
      # urls << doc/"a[@href*='/diary/']"
      f = open("hoge.txt","a")
      (doc/"a[@href*='/diary/']").each {|u| f.puts u['href']}
      # (doc/"a[@href*='/diary/']").each {|u| puts u['href']}
      f.close

      next_link = page.links.text("次へ>>".toeuc)
      puts next_link.href
      page = agent.get(next_link.href)
    end
    sleep @wait
  end
end


if $0 == __FILE__
  # pass

end
