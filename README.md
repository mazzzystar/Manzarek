# Fate
F(anfouD)ate.

# 简介
一个小巧的饭否相亲机器人。功能如下：
* 1.定期爬取fanfou"随便看看"页面数据。
* 2.识别text中包含的关键字是否有相亲性质，确认转发还是原创，最后获取原创主页，查看其性别，地址，自述。
* 3.转发相亲信息。
* 4.对每一个关注我的人，也将自动发送他们的名片。

# 使用
你需要有fanfou API的consumer key，然后新建一个文件`config.py`配置自己的信息。
```python
# 账号+密码
client_key = ""
client_passwd = ""

# api consumer key
consumer_key = ''
consumer_secret = ''

consumer = {
        'key': consumer_key,
        'secret': consumer_secret
    }

```

# TODO
此项目是我一个晚上的成果，存在许多有待完善的地方：
* (紧急且重要)此'相亲bot'不是真正的转发消息，而是拼凑'@'+'user_name'，因此无法点击用户昵称跳转主页。
* 简繁体识别。
* 内容识别准确率有待提高。
* 公布用户私信@我的内容。
* 同一用户半小时内仅转发一次。
