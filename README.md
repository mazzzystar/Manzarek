# Fate
F(anfouD)ate.

# 简介
一个小巧的饭否相亲机器人。功能如下：
* 1.定期爬取fanfou"随便看看"页面数据。
* 2.识别text中包含的关键字是否有相亲性质，确认转发还是原创，最后获取原创主页，查看其性别，地址，自述。
* 3.转发相亲信息。
* 4.私信"连接"起同城用户。

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

# 该机器人的unique_id
my_unique_id = ''
```
# 更新
* 应用雏形：识别用户信息+调用api自动转发。 (2017/8/13)
* 支持用户私信自动转发，用户可以将相亲帖私信给我，我将自动转发。 (2017/8.14)
* 对每一位关注我的用户，发送包含其他同城用户个人信息的私信，帮助大家更好地勾搭。(2017/8/15)

# TODO
此项目是我一个晚上的成果，存在许多有待完善的地方：
* 内容识别准确率有待提高。
* 同一用户半小时内仅转发一次。