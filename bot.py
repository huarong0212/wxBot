#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import ConfigParser
import json
from urllib import unquote
from urllib import quote
from urllib import urlencode
import urllib
import time
from audio import tts, mp3topcm
import os.path
import sys
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


class TulingWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

        self.tuling_key = ""
        self.robot_switch = True

        try:
            cf = ConfigParser.ConfigParser()
            cf.read('conf.ini')
            self.tuling_key = cf.get('main', 'key')
        except Exception:
            pass
        print 'tuling_key:', self.tuling_key

    def tuling_auto_reply(self, uid, msg):
        if self.tuling_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', '')[:30]
            body = {'key': self.tuling_key, 'info': msg.encode('utf8'), 'userid': user_id}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')

            # print '    ROBOT:', result
            return result
        else:
            return u"知道啦"

    def auto_switch(self, msg):
        user_id = msg['user']['id']
        msg_data = msg['content']['data']
        stop_cmd = [u'退下', u'走开', u'关闭', u'关掉', u'休息', u'滚开']
        start_cmd = [u'出来', u'启动', u'工作']
        if self.robot_switch:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch = False
                    self.send_msg_by_uid(u'机器人已关闭！', user_id)
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    self.send_msg_by_uid(u'机器人已开启！', user_id)

    def reply_msg_by_content_type(self, msg):
        # print msg
        user_id = msg['user']['id']
        content_type = msg['content']['type']
        msg_type_id = msg['msg_type_id']
        msg_id = msg['msg_id']

        data = ''
        scr_name = ''

        if msg_type_id == 0 and content_type == 11:
            return

        try:
            scr_name = msg['content']['user']['name']
        except Exception:
            try:
                scr_name = msg['user']['name']
            except Exception:
                pass

        if content_type == 0 and scr_name == 'self':
            return

        has_scr_name = False
        if scr_name != 'unknown' and scr_name != '':
            scr_name = '@' + scr_name + "\n"
            has_scr_name = True

        is_at_me = True
        if msg_type_id == 3:
            is_at_me = False
            if 'detail' in msg['content']:
                my_names = self.get_group_member_name(msg['user']['id'], self.my_account['UserName'])
                if my_names is None:
                    my_names = {}
                if 'NickName' in self.my_account and self.my_account['NickName']:
                    my_names['nickname2'] = self.my_account['NickName']
                if 'RemarkName' in self.my_account and self.my_account['RemarkName']:
                    my_names['remark_name2'] = self.my_account['RemarkName']

                is_at_me = False

                for detail in msg['content']['detail']:
                    if detail['type'] == 'at':
                        for k in my_names:
                            # print detail['value']
                            if my_names[k] and my_names[k] == detail['value']:
                                is_at_me = True
                                break


        try:
            data = msg['content']['desc']
        except Exception:
            data = msg['content']['data']


        if content_type == 0:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return


            videos_key = [u'视频', u'mp4']
            for key in videos_key:
                if key in data:
                    self.send_file(user_id)
                    return

            girls_key = [u'美女', u'girl', u'来张', u'来个']
            for key in girls_key:
                if key in data:
                    self.send_girl(user_id)
                    return

            songs_key = [u'音乐', u'mp3', u'歌曲']
            for key in songs_key:
                if key in data:
                    data = data.replace(key, '')
                    self.send_song(data, user_id)
                    return

            apks_key = [u'app', u'apk', u'下载']
            for key in apks_key:
                if key in data:
                    data = data.replace(key, '')
                    self.send_apk(data, user_id)
                    return

            films_key = [u'电影', u'种子', u'迅雷', u'磁力']
            for key in films_key:
                if key in data:
                    data = data.replace(key, '')
                    self.send_film(data, user_id)
                    return

            if is_at_me:
                # print data
                reply = self.tuling_auto_reply(user_id, data)
                if has_scr_name:
                    reply = scr_name + reply
                self.send_msg_by_uid(reply.encode('utf-8'), user_id)

        elif content_type == 4:
            return
            pcm = mp3topcm(os.path.join(self.temp_pwd, self.get_voice(msg_id)))
            tts_data = tts('1d2678900f734aa0a23734ace8aec5b1', pcm)
            try:
                msg['content']['data'] = tts_data
            except Exception:
                tts_data = u"无法识别"
            # print u'[语音识别:]'+ tts_data
            self.auto_switch(msg)
            if self.robot_switch != True:
                return
            if scr_name == 'unknown' or scr_name != '':
                scr_name = ''

            reply = u'语音识别:' + tts_data + '\n\n' + scr_name
            reply += self.tuling_auto_reply(user_id, tts_data)
            # print reply
            self.send_msg_by_uid(reply, user_id);
        elif content_type == 3:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return
            self.send_img(user_id)
        elif content_type == 11 or content_type == 6:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return
            self.send_img(user_id)
        elif content_type == 7:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return
            self.send_msg_by_uid(self.tuling_auto_reply(user_id, u'已经转帐给你'), user_id);
        elif content_type == 13:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return
            self.send_file(user_id)
        else:
            self.auto_switch(msg)
            if self.robot_switch != True:
                return

    def handle_msg_all(self, msg):
        self.reply_msg_by_content_type(msg)

    def send_img(self, user_id):
        try:
            page = (int)(10 *  random.random())
            url = 'http://61.160.36.100/doutu/apiDoutu.php?funcName=GetHotBiaoQing&page='+str(page)+'&os=Android&version=2.5.0f'
            r = requests.post(url)
            respond = json.loads(r.text)
            datas = respond['data']['list']
            fthumb = datas[(int)(len(datas) *  random.random())]['fthumb']
            fpath = os.path.join('img', str(time.time())+".jpg")
            if os.path.isfile(fpath) == False:
                urllib.urlretrieve(fthumb, fpath)
            self.send_img_msg_by_uid(fpath, user_id)
        except Exception as e:
            print e
            pass

    def send_girl(self, user_id):
        try:
            page = (int)(10 *  random.random())
            url = 'http://119.134.255.170:8086/tuijian_bankuai'
            json_data = {
	                "cmd": "100",
	                "qudao": "13",
	                "page": "1"
            }
            r = requests.post(url, json = json_data)
            respond = json.loads(r.text)
            datas = respond['data']
            fthumb = datas[(int)(len(datas) *  random.random())]['picture_addr']
            fpath = os.path.join('img', str(time.time())+".jpg")
            if os.path.isfile(fpath) == False:
                urllib.urlretrieve(fthumb, fpath)
            urllib.urlretrieve(fthumb, fpath)
            self.send_img_msg_by_uid(fpath, user_id)
        except Exception as e:
            print e
            pass

    def send_file(self, user_id):
        try:
            url = 'http://d.api.budejie.com/topic/list/chuanyue/41/budejie-android-6.6.4/0-8.json?market=c-oppo&ver=6.6.4&visiting=&os=5.1&appname=baisibudejie&client=android&udid=863062030230011&mac=6c%3A5c%3A14%3A46%3A71%3A0a'
            r = requests.post(url)
            respond = json.loads(r.text)
            datas = respond['list']
            dobj = datas[(int)(len(datas) *  random.random())]
            fthumb = dobj['video']['video'][0]
            fname = dobj['text']
            fid = dobj['id']
            fpath = os.path.join('mp4', fid+".mp4")

            if os.path.isfile(fpath) == False:
                urllib.urlretrieve(fthumb, fpath)

            self.send_file_msg_by_uid(fpath, user_id)
            reply = u'为您推荐爆笑视频:' + "\n" + "    " + fname
            self.send_msg_by_uid(reply, user_id);
        except Exception as e:
            print e
            pass

    def send_song(self, data, user_id):
        try:
            keyword = data.encode('utf-8').strip()
            url = 'https://music-api.9ku.com/search'
            form_data = {
                "start": '0',
                "num": "10",
                "q": keyword,
                "app": "jQZnyNaE7Q"
            }
            r = requests.post(url,verify=False, data = form_data, headers = {'Accept-Encoding':	'gzip', 'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1; OPPO R9m Build/LMY47I)', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
            # print r.text
            respond = json.loads(r.text)
            dobj = respond['data'][0]
            tid = dobj['tid']
            _type = dobj['class']
            self.send_song2(tid, _type, user_id)
        except Exception as e:
            print e
            self.send_msg_by_uid(u'抱歉,没有找到该音乐', user_id);
            pass

    def send_song2(self, tid, type, user_id):
        try:
            url = 'https://music-api.9ku.com/player/play'
            form_data = {
                "class": type,
                "tid": tid,
                "bot": 1,
                "app": "jQZnyNaE7Q"
            }
            r = requests.post(url, verify=False, data = form_data, headers = {'Accept-Encoding':	'gzip', 'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1; OPPO R9m Build/LMY47I)', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
            # print r.text
            respond = json.loads(r.text)
            dobj = respond['data'][0];
            fthumb = dobj['mp3']
            fname = dobj['title']
            artname = dobj['artname']
            fid = dobj['sonid']
            fpath = os.path.join('mp3', fid + ".mp3")
            if os.path.isfile(fpath) == False:
                urllib.urlretrieve(fthumb, fpath)
            self.send_file_msg_by_uid(fpath, user_id)
            reply = u'为您找到原生音乐:' + "\n" + u"    歌曲：" + fname + "\n" + u"    演唱者：" + artname
            self.send_msg_by_uid(reply, user_id);
            # print reply


        except Exception as e:
            print e
            self.send_msg_by_uid(u'抱歉,没有找到该音乐' + e, user_id);
            pass
    def send_apk(self, data, user_id):
        try:
            keyword = urllib.quote(data.encode('utf-8').strip())
            # print keyword
            url = 'http://zhushou.360.cn/search/index/?kw=' + keyword
            t = (int)(time.time())
            r = requests.get(url, headers = {'Content-Type': 'text/html;charset=utf-8'})
            parsed_html = BeautifulSoup(r.text, "html.parser");
            fthumb = parsed_html.body.find('div', attrs={'class':'SeaCon'}).find("ul").find("li").find('div', attrs={'class':'seaDown'}).find("a").get("href")
            fname = parsed_html.body.find('div', attrs={'class':'SeaCon'}).find("ul").find("li").find("dd").find('a').text
            fpath = os.path.join('apk', fname+".apk")
            self.send_msg_by_uid(fname + fthumb, user_id);
        except Exception as e:
            self.send_msg_by_uid(e, user_id);
            print e
            pass
    def send_film(self, data, user_id):
        try:
            keyword = urllib.quote(data.encode('utf-8').strip())
            # print keyword
            url = 'http://www.diaosisou.com/list/' + keyword + '/1'
            r = requests.get(url, headers = {'Content-Type': 'text/html;charset=utf-8', 'Referer': 'http://www.diaosisou.com/'})
            parsed_html = BeautifulSoup(r.text, "html.parser");
            fthumbs = parsed_html.body.find('div', attrs={'class':'main'}).find("ul", attrs={'class': 'mlist'}).find("li").find('div', attrs={'class':'dInfo'}).find_all("a")
            reply = ''
            for link in fthumbs:
                reply += link.text + link.get('href') + "\n"
            # print reply
            self.send_msg_by_uid(reply, user_id);
        except Exception as e:
            print e
            self.send_msg_by_uid(e+u"没有找到该种子", user_id);
            pass

def main():
    bot = TulingWXBot()
    bot.DEBUG = False
    bot.conf['qr'] = 'png'

    bot.run()


if __name__ == '__main__':
    main()
    #send_song(u'忘情水', 1)
