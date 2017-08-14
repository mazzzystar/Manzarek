# coding:utf-8
import requests
import json
import time
import logging
from lxml import etree
import re
import config
import fanfou
import random
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(filename='log.txt',level=logging.ERROR)
logging.info('Starting……')


class Timeline:
    def __init__(self):
        # 通过api抓取数据
        self.public_timeline_url = 'http://api.fanfou.com/statuses/public_timeline.json'
        self.followers_url = 'http://api.fanfou.com/users/followers.json'
        self.direct_message_url = 'http://api.fanfou.com/direct_messages/conversation_list.json'
        self.username = config.client_key
        self.password = config.client_passwd
        self.client = fanfou.XAuth(config.consumer, config.client_key, config.client_passwd)

        black_list, black_uname, word_list, seq_list, contain_list = self.init_dict()
        self.black_list = black_list
        self.black_uname = black_uname
        self.word_list = word_list
        self.seq_list = seq_list
        self.contain_list = contain_list
        self.my_unique_id = config.my_unique_id

    def init_dict(self):
        # black_uid
        black_list = ['IAVAofofcEY', '9Msmu_J_t3s']
        black_uname = [u"糗百"]

        # key_match dict
        key_words_zy = [u"征友：", u"征友:", u"发一个征友", u"一条征友",u"征友启事"]
        key_words_xq = [u"要相亲", u"去相亲", u"我相亲"]
        key_words_npy = [u"没有男朋友", u"假装有男朋友", u"没有女朋友", u"假装有女朋友",u"单身狗", u"求男朋友", u"求一个男朋友", u"找个男朋友", u"求男友", u"求一个女朋友", u"找个女朋友",u"想谈恋爱", u"想有个男朋友", u"想有个男票"]

        key_words_zy.extend(key_words_xq)
        key_words_zy.extend(key_words_npy)

        # sequence_match dict
        male_seq_words = [u"本人男(.*?)岁(.*?)单身", u"本人男(.*?[0-9]+)岁(.*?)年薪", u"本人男(.*?[0-9]+)年(.*?)房", u"本人男(.*?[0-9]+)后(.*?)房", u"男(.*?[0-9]+)(.*?)车"]
        female_seq_words = [u"(.*?[0-9]+)年妹子(.*?)征男朋友", u"女(.*?[0-9]+)岁(.*?)希望(.*?)", u"(.*?[0-9]+)后妹子(.*?)征友"]
        male_seq_words.extend(female_seq_words)

        # contain_match dict
        contain_list = [(u"男", u"求", u"女", u"坐标"), (u"另一半", u"求", u"女", u"结婚"), (u"单身", u"前女友"), (u"单身", u"前男友"), (u"单身", u"个妹子"), (u"我", u"单身", u"年")]

        return black_list, black_uname, key_words_zy, male_seq_words, contain_list

    def in_black_list(self, uid, uname):
        '''
        uid或uname其中任一个在黑名单内，均不转发。
        '''
        if uid in self.black_list:
            return 1
        if uname in self.black_uname:
            return 1
        return 0

    def save_followers(self, followers_set):
        '''
        将followers的id保存成文件
        '''
        f = open('followers.txt', 'w')
        for item in followers_set:
            f.write(item)
            f.write('\n')
        f.close()

    def get_followers_from_local(self, ff):
        '''
        从本地dump followers
        '''
        followers = set()
        try:
            f = open(ff, 'r')
            for item in f:
                followers.add(item.strip())
            return followers
        except:
            return set()

    def fetch(self, url):
        data = {}
        try:
            request=requests.get(url, auth=(self.username, self.password))
            if request.status_code == 200:
                data = request.json()
            else:
                time.sleep(3)
                request=requests.get(url, auth=(self.username, self.password))
                data = request.json()
        except requests.ConnectionError, e:
            print e
            time.sleep(300)
            request=requests.get(url, auth=(self.username, self.password))
            data = request.json()
        finally:
            return data

    def get_direct_message(self):
        # 获取私信json
        return self.fetch(self.direct_message_url)

    def get_public_timeline(self):
        # 获取'随便看看'里的json内容
        return self.fetch(self.public_timeline_url)

    def get_followers(self):
        # 获取followers的json内容
        return self.fetch(self.followers_url)

    def keywords_match(self, text):
        # 关键字匹配是否包含相亲信息
        for word in self.word_list:
            if word in text:
                return 1
        return 0

    def sequence_match(self, text):
        # 序列匹配是否包含相亲信息
        for word in self.seq_list:
            try:
                t = re.search(word, text).group(1)
            except AttributeError:
                t = ''
            if t:
                return 1
        return 0

    def contain_match(self, text):
        # 包含匹配是否包含相亲信息
        for tup in self.contain_list:
            for word in tup:
                if word not in text:
                    return 0
        return 1

    def if_duplicate(self, text):
        # 去重
        pass

    def judge(self, text):
        # 是否为相亲贴
        # 关键词匹配
        key_flag = self.keywords_match(text)
        seq_flag = self.sequence_match(text)
        contain_flag = self.contain_match(text)
        if (key_flag or seq_flag or contain_flag):
            return 1
        return 0

    def parse_followers(self):
        '''
        构建followers的个人信息，后续直接转发此信息。
        '''
        local_followers = self.get_followers_from_local('followers.txt')

        followers = self.get_followers()
        # print followers
        new_followers = set()
        all_followers = set()
        new_user_info = []
        for user in followers:
            id = user['unique_id']

            # print id, description
            all_followers.add(id)

            if id in local_followers:
                continue
            new_followers.add(id)

            msg = ''
            user_name = user['name']
            if user_name:
                msg = '@'+user_name
            try:
                location = user['location']
            except:
                location = ''
            if location:
                msg += '[%s]' % location

            try:
                gender = user['gender']
            except:
                gender = ''
            if gender:
                msg += '[%s]' % gender

            try:
                birthday = user['birthday']
            except:
                birthday = ''
            if birthday:
                msg += '[%s]' % birthday
            try:
                description  = user['description']
            except:
                description = ''
            if description:
                description = description.replace('\n', ' ')
                msg = msg + ':' + description

            msg += u"(关注我将被自动展示)"
            new_user_info.append(msg)

        self.save_followers(all_followers)

        return new_user_info

    def parse_timeline(self, data):
        id_set = set()
        msg_list = []
        for i in data:
            try:
                uid = i['unique_id']
            except:
                uid = ''
            name = i['user']['name']

            if self.in_black_list(uid, name):
                continue
            if uid in id_set:
                continue

            if uid:
                id_set.add(uid)

            text = i['text']
            newest_text = text.split('@')[0]
            # print uid, newest_text

            if self.judge(newest_text):
                msg = ''
                user_name = i['user']['name']
                msg += '@'+user_name + ' '

                in_reply_to_user_id = i['in_reply_to_user_id']
                if not in_reply_to_user_id:
                    # 是本人
                    location = i['location']
                    if location:
                        msg += '[%s]' % location
                    gender = i['user']['gender']
                    if gender:
                        msg += '[%s]' % gender
                    birthday = i['user']['birthday']
                    if birthday:
                        msg += '[%s]' % birthday
                msg = msg +  ' ' + text
                msg_list.append(msg)
        return msg_list

    def parse_conversion(self, data):
        id_set = set()
        msg_list = []
        for i in data:
            try:
                uid = i['dm']['sender']['unique_id']
            except:
                uid = ''
            if uid in id_set:
                continue
            if uid == self.my_unique_id:
                continue
            if uid:
                id_set.add(uid)

            # 判断消息类型
            try:
                text = i['dm']['text']
            except:
                text = ''
            bother_list= [u"#骚扰#", u"删"]
            bother_flag = 0
            for item in bother_list:
                if item in text:
                    print "bother!"
                    bother_flag = 1
            if bother_flag:
                continue

            try:
                user_name = i['dm']['sender']['name']
            except:
                user_name = ''
            if not user_name:
                continue

            if self.in_black_list(uid, user_name):
                continue

            # 构建信息
            msg = ''
            msg += '@'+user_name + ' '

            try:
                location = i['dm']['sender']['location']
            except:
                location = ''
            if location:
                msg += '[%s]' % location

            try:
                gender = i['dm']['sender']['gender']
            except:
                gender = ''
            if gender:
                msg += '[%s]' % gender

            try:
                birthday = i['dm']['sender']['birthday']
            except:
                birthday = ''
            if birthday:
                msg += '[%s]' % birthday

            msg = msg +  ' ' + text
            msg += u"(用户私信)"
            msg_list.append(msg)
        return msg_list

    def send_message(self, msg_list):
        if len(msg_list):
            for item in msg_list:
                print item
                body = {'status': item}
                try:
                    tl.client.request('/statuses/update', 'POST',  body)
                except Exception as e:
                    print '发送消息失败: ' + repr(e)
                    break

    def run(self, interval):
        while(1):
            print 'go on...'
            try:
                # public_timeline抓取信息
                public_data = self.get_public_timeline()
                public_msg_list = tl.parse_timeline(public_data)
                self.send_message(public_msg_list)

                # 暂时不展示个人信息
                # followers_msg = []
                # if random.random() < 0.9:
                #     followers_msg = tl.show_followers()
                # msg_list.extend(followers_msg)

                # 私信信息,半小时监测1次数
                if random.random() < 0.005:
                    conversation_msg_data = self.get_direct_message()
                    conversation_msg_list = tl.parse_conversion(conversation_msg_data)
                    self.send_message(conversation_msg_list)

                time.sleep(interval)
            except Exception as e:
                print "连接失败！" + str(e)
                time.sleep(interval)

if __name__ == '__main__':
    try:
        tl = Timeline()
        tl.run(10)
    except:
        time.sleep(10)
        tl = Timeline()
        tl.run(10)