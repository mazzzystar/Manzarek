# coding:utf-8
import requests
import time
import logging
import re
import config
import fanfou
import random
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(filename='log.txt',level=logging.INFO)
logging.info('Starting……')


class Timeline:
    def __init__(self):
        # 通过api抓取数据
        self.public_timeline_url = 'http://api.fanfou.com/statuses/public_timeline.json'
        self.followers_url = 'http://api.fanfou.com/users/followers.json'
        self.direct_message_url = 'http://api.fanfou.com/direct_messages/conversation_list.json'
        self.send_private_msg_url = 'http://api.fanfou.com/private_messages/new.json'
        self.local_followers_file = 'followers.txt'
        self.local_conversation_file = 'conversations.txt'
        self.local_timeline_file = 'timelines.txt'
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
        self.message_user = set()

    def init_dict(self):
        # black_uid
        black_list = ['IAVAofofcEY', '9Msmu_J_t3s']
        black_uname = [u"糗百"]

        # key_match dict
        key_words_zy = [u"征友：", u"征友:", u"发一个征友", u"一条征友",u"征友启事", u"我要征友",]
        key_words_xq = [u"要相亲", u"要相親", u"去相亲", u"我相亲"]
        key_words_npy = [u"没有男朋友", u"假装有男朋友", u"我介绍男朋友", u"我介绍女朋友", u"没有女朋友", u"假装有女朋友",u"单身狗", u"求男朋友", u"求一个男朋友", u"找个男朋友", u"求男友", u"求一个女朋友", u"找个女朋友",u"想谈恋爱", u"想有个男朋友", u"想有个男票"]

        key_words_zy.extend(key_words_xq)
        key_words_zy.extend(key_words_npy)

        # sequence_match dict
        male_seq_words = [u"本人男(.*?)岁(.*?)单身", u"本人男(.*?[0-9]+)岁(.*?)年薪", u"本人男(.*?[0-9]+)年(.*?)房", u"本人男(.*?[0-9]+)后(.*?)房", u"男(.*?[0-9]+)(.*?)车", u"我单身(.*?[0-9]+)年"]
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

    def save_users(self, user_set, uid_file):
        '''
        user_id保存成文件
        '''
        if len(user_set) == 0:
            return
        try:
            f = open(uid_file, 'a')
            for item in user_set:
                f.write(item)
                f.write('\n')
            f.close()
        except Exception as e:
            logging.error(repr(e))

    def save_followers(self, user_set, uid_file):
        '''
        因user可能会unfo,因此本地followers的uid更新
        每次都重新写文件。
        '''
        if len(user_set) == 0:
            return
        try:
            f = open(uid_file, 'w')
            for item in user_set:
                f.write(item)
                f.write('\n')
            f.close()
        except Exception as e:
            logging.error(repr(e))


    def get_users_from_local(self, ff):
        '''
        从本地dump users
        '''
        users = set()
        try:
            f = open(ff, 'r')
            for item in f:
                users.add(item.strip())
            f.close()
            return users
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
            logging.error(repr(e))
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
            flag = 1
            for word in tup:
                if word not in text:
                    flag = 0
                    break
            if flag:
                return 1
        return 0

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

    def parse_followers(self, opposite_sex=1):
        '''
        构建followers的个人信息，同城followers互相发私信。
        '''
        msg_info_set = set()
        local_followers = self.get_users_from_local(self.local_followers_file)

        followers = self.get_followers()
        # print followers
        new_location_followers = []
        all_location_followers = []

        all_user_uid_set = set()

        # 找出全部有location的用户
        for user in followers:
            uid = user['unique_id']
            name = user['name']
            if self.in_black_list(uid, name):
                continue

            try:
                location = user['location']
            except:
                location = ''
            if not location:
                continue

            # 记录全部followers的uid方便写入本地
            all_user_uid_set.add(uid)

            if uid not in local_followers:
                new_location_followers.append(user)

            if not len(new_location_followers):
                # 没有新的有地址的用户
                self.save_followers(all_user_uid_set, self.local_followers_file)
                return msg_info_set

            all_location_followers.append(user)

        # 为每个用户制作信息字典
        user_info_dict = {}
        for user in all_location_followers:
            # uid是用户唯一id
            uid = user['unique_id']

            msg = ''
            user_name = user['name']
            if user_name:
                msg = u"TA与你同城。" + ' ' + '@' + user_name + ' '

            location = user['location']
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

            try:
                # id用于拼凑用户主页url
                id = user['id']
            except:
                id = ''
            if id:
                url = u'http://fanfou.com/' + id
                msg = msg + '[' + url + ']'
            msg += u"(请勿回复，如若打扰请unfo我)"
            user_info_dict[uid] = msg

        # 制作发送信息
        user_pair_set = set()
        for new_user in new_location_followers:
            new_uid = new_user['unique_id']
            new_location = new_user['location']
            new_id = new_user['id']

            try:
                new_gender = new_user['gender']
            except:
                new_gender = ''

            for all_user in all_location_followers:
                uid = all_user['unique_id']
                id = all_user['id']
                if uid == new_uid:
                    # 同一个用户
                    continue

                # 不遍历两次互相私信的用户
                uid_pair = (new_uid, uid)
                if uid_pair in user_pair_set:
                    continue
                user_pair_set.add((uid_pair))

                location = all_user['location']

                new_location = self.get_clean_city(new_location)
                location = self.get_clean_city(location)

                if new_location == location:
                    if opposite_sex == 1:
                        # 仅发送异性信息
                        try:
                            gender = all_user['gender']
                        except:
                            gender = ''

                        # 两用户性别必须均不为空
                        if not new_gender:
                            # 新用户必须要有性别
                            continue
                        if not gender:
                            continue

                        # 两用户性别必须不同
                        if gender == new_gender:
                            continue
                        # print new_name, new_gender,'|',name, gender
                    try:
                        new_user_msg = user_info_dict[new_uid]
                        user_msg = user_info_dict[uid]

                        # 给双方添加对方的信息
                        msg_info_set.add((new_id, user_msg))
                        msg_info_set.add((id, new_user_msg))
                    except Exception as e:
                        logging.error(repr(e))

        self.save_followers(all_user_uid_set, self.local_followers_file)
        return msg_info_set

    # 城市判别时需要清洗
    def get_clean_city(self, city):
        special_case = [u"北京", u"上海"]

        clean_city = ''
        city_part = city.split()
        if city_part[0] in special_case:
            clean_city = city_part[0]
        else:
            if len(city_part) == 2:
                clean_city = city_part[1]
            else:
                clean_city = city_part[0]
        return clean_city


    def parse_timeline(self, data):
        local_timeline = self.get_users_from_local(self.local_timeline_file)

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
            if uid in local_timeline:
                continue

            if uid:
                id_set.add(uid)

            text = i['text']
            newest_text = text.split('@')[0]
            # print uid, newest_text

            if self.judge(newest_text):
                msg = ''
                user_name = i['user']['name']
                msg = msg +  u"转" + '@'+user_name + ' '

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

        self.save_users(id_set, self.local_timeline_file)

        return msg_list

    def parse_conversation(self, data):
        local_conversation = self.get_users_from_local(self.local_conversation_file)

        id_set = set()
        msg_list = []
        for i in data:
            try:
                uid = i['dm']['sender']['unique_id']
            except:
                uid = ''
            if uid in id_set:
                continue
            if uid in local_conversation:
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
            if uid in self.message_user:
                continue
            self.message_user.add(uid)
            msg = ''
            msg = msg +  u"转" + '@'+user_name + ' '

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
            msg += u"(用户私信:该用户向你表明TA正单身)"
            msg_list.append(msg)

        self.save_users(id_set, self.local_conversation_file)
        return msg_list

    def send_private_msg(self, private_msg_set):
        if not len(private_msg_set):
            return

        for msg in private_msg_set:
            try:
                id = msg[0]
                text = msg[1]
                information = {'user': id, 'text': text}
                request=requests.post(self.send_private_msg_url, auth=(self.username, self.password), data=information)
                print request.text
                if request.status_code == 200:
                    logging.info("send private msg success")
                else:
                    logging.error("fail")
            except requests.ConnectionError, e:
                logging.error(repr(e))

    def send_message(self, msg_list):
        if len(msg_list):
            for item in msg_list:
                print item
                body = {'status': item}
                try:
                    tl.client.request('/statuses/update', 'POST',  body)
                except Exception as e:
                    logging.error('发送消息失败: ' + repr(e))
                    break

    def run(self, interval):
        while(1):
            logging.info('go on...')
            try:
                # public_timeline抓取信息
                try:
                    public_data = self.get_public_timeline()
                    public_msg_list = self.parse_timeline(public_data)
                    self.send_message(public_msg_list)
                except:
                    pass

                # 发送同城私信,每5小时检测一次
                if random.random() < 0.0005:
                    try:
                        private_msg_set = self.parse_followers()
                        self.send_private_msg(private_msg_set)
                    except:
                        pass

                # 监控用户私信信息
                try:
                    conversation_msg_data = self.get_direct_message()
                    conversation_msg_list = self.parse_conversation(conversation_msg_data)
                    self.send_message(conversation_msg_list)
                except:
                    pass

                time.sleep(interval)
            except Exception as e:
                logging.error("连接失败！" + str(e)) 
                time.sleep(interval)

if __name__ == '__main__':
    tl = Timeline()
    try:
        tl = Timeline()
        tl.run(10)
    except:
        time.sleep(10)
        tl = Timeline()
        tl.run(10)
