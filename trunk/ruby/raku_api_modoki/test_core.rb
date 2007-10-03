#-*- coding: utf-8 -*-

require 'test/unit'
require 'core'

class TestRakuten < Test::Unit::TestCase
  attr_accessor :username, :password

  def setup
    @username = "あなたのユーザーID"
    @password = "あなたのパスワード"
  end

  def test_login
    agent = Rakuten.new(@username, @password)
    result = agent.login
    assert_equal(result, true)
  end

  def test_login_plaza
    agent1 = Rakuten.new(@username, @password)
    result_ok = agent1.login_plaza
    assert_equal(result_ok, true)

    agent2 = Rakuten.new('dummy', 'dummy')
    result_ng = agent2.login_plaza
    assert_equal(result_ng, false)
  end

  def test_logout_plaza
    agent = Rakuten.new(@username, @password)
    result = agent.login_plaza
    assert_equal(result, true)

    result = agent.logout_plaza
    assert_equal(result, true)

    result = agent.login_plaza
    assert_equal(result, true)
  end

  def test_post_entry
    agent = Rakuten.new(@username, @password)
    login = agent.login_plaza
    assert_equal(login, true)

    result = agent.post_entry('日記の投稿テスト','あーあー、本日は晴天なり、本日は晴天なり、ただいまスクリプトのテスト中。。。')
    assert_equal(result, true)
  end

  def test_remove_entry
    agent = Rakuten.new(@username, @password)
    login = agent.login_plaza
    assert_equal(login, true)

    result = agent.remove_entry
    assert_equal(result, true)
  end

  def test_edit_top_page
    agent = Rakuten.new(@username, @password)
    login = agent.login_plaza
    assert_equal(login, true)

    result = agent.edit_plaza_top_page('トップページの書き込みテスト')
    assert_equal(result, true)
  end

  def test_search
    agent = Rakuten.new(@username, @password)
    login = agent.login_plaza
    assert_equal(login, true)

    results = agent.search('椎名林檎')
    puts results[:title].toutf8
    puts results[:text].toutf8
  end

  def test_delete_account
    agent = Rakuten.new(@username, @password)
    login = agent.login_plaza
    assert_equal(login, true)

    agent.delete_plaza_account
  end

end

