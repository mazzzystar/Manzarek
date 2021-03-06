# Manzarek

## 简介
一个小巧的饭否相亲机器人。功能如下：
* 1.定期爬取fanfou"随便看看"页面数据。
* 2.识别text中包含的关键字是否有相亲性质，确认转发还是原创，最后获取原创主页，查看其性别，地址，自述。
* 3.转发相亲信息。
* 4.私信"连接"起同城用户。

## 使用
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
运行
```
python timeline.py
```
## 更新
* 应用雏形：识别用户相亲内容+调用饭否api自动转发。 (2017/8/13 10:00 pm ~ 8/14 3:30 am)
* 支持用户私信自动转发，用户可以将相亲帖私信给我，我将自动转发。 (2017/8/14 8:30 pm ~ 8/15 1:00 am)
* 对每一位关注我的用户，私信向TA介绍同城(可指定性别)饭友。(2017/8/15 9:00 pm ~ 8/16 1:10 am)

## TODO
此项目是我一个晚上的成果，存在许多有待完善的地方：
* 内容识别准确率有待提高。
* 同一用户半小时内仅转发一次。
* 针对同城用户私信介绍功能，未来考虑引入机器学习，推荐兴趣相投的用户，而非目前的简单同城推荐。

## 致谢
项目中`fanfou.py`直接使用饭否用户[home2](http://fanfou.com/home2)提供的代码，此处表示感谢。

