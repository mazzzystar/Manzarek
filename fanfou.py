#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import urllib
import hmac
import urllib2
import hashlib
import binascii
import random
import urlparse
import config

# @Setfme http://fanfou.com/home2

def oauth_escape(s):
    s = s.encode('utf-8')  if isinstance(s, unicode) else str(s)
    return urllib.quote(s, safe='~')

def oauth_timestamp():
    return str(int(time.time()))

def oauth_nonce(size=8):
    return ''.join([str(random.randint(0, 9)) for i in range(size)])

def oauth_query(base_args):
    return '&'.join('%s=%s' % (k, oauth_escape(v)) for k, v in sorted(base_args.items()))

def oauth_http_url(http_url):
    parts = urlparse.urlparse(http_url)
    scheme, netloc, path = parts[:3]
    return '%s://%s%s' % (scheme, netloc, path)

class Auth(object):
    def __init__(self, oauth_consumer, oauth_token={}, callback=None):
        self.oauth_consumer = oauth_consumer
        self.oauth_token = oauth_token
        self.callback = callback or 'http://localhost:8080/callback'
        self.form_urlencoded = 'application/x-www-form-urlencoded'
        self.base_api_url = 'http://api.fanfou.com%s.json'
        self.access_token_url = 'http://fanfou.com/oauth/access_token'
        self.request_token_url = 'http://fanfou.com/oauth/request_token'
        self.authorize_url = 'http://m.fanfou.com/oauth/authorize?oauth_token=%s&oauth_callback=%s'

    def HMAC_SHA1(self, keys_string, base_string):
        hashed = hmac.new(keys_string, base_string, hashlib.sha1)
        return binascii.b2a_base64(hashed.digest())[:-1]

    def oauth_signature(self, http_url, http_method, base_args):
        normalized_url = oauth_http_url(http_url)
        query_items = oauth_query(base_args)
        base_elems = (http_method.upper(), normalized_url, query_items)
        base_string = '&'.join(oauth_escape(s) for s in base_elems)
        keys_elems = (self.oauth_consumer['secret'], self.oauth_token.get('secret', ''))
        keys_string = '&'.join(oauth_escape(s) for s in keys_elems)
        return self.HMAC_SHA1(keys_string, base_string)

    def oauth_header(self, base_args, realm=''):
        auth_header = 'OAuth realm="%s"' % realm
        for k, v in sorted(base_args.items()):
            if k.startswith('oauth_') or k.startswith('x_auth_'):
                auth_header += ', %s="%s"' % (k, oauth_escape(v))
        return {'Authorization': auth_header}

    def oauth_request(self, http_url, http_method, http_args={}, headers={}):
        base_args = {
            'oauth_consumer_key': self.oauth_consumer['key'],
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp':  oauth_timestamp(),
            'oauth_nonce': oauth_nonce(),
            'oauth_version': '1.0'
        }

        http_args = http_args.copy()
        headers = headers.copy()
        if http_url.startswith('/'):
            if ':' in http_url:
                path, argv = http_url.split(':')
                http_url = path + http_args.get(argv)
            http_url = self.base_api_url % http_url

        if http_method == 'POST':
            headers['Content-Type'] = headers.get('Content-Type', self.form_urlencoded )
            (headers['Content-Type'] == self.form_urlencoded) and base_args.update(http_args)
        else:
            base_args.update(http_args)
            http_url = http_url + '?' + urllib.urlencode(http_args) if http_args else http_url

        self.oauth_token and base_args.update({'oauth_token': self.oauth_token['key']})
        base_args['oauth_signature'] = self.oauth_signature(http_url, http_method, base_args)

        headers.update(self.oauth_header(base_args))
        http_req = urllib2.Request(http_url, headers=headers)
        if headers.get('Content-Type') == self.form_urlencoded:
            http_req.add_data(data=urllib.urlencode(http_args))
        elif 'form-data' in headers.get('Content-Type', ''):    # multipart/form-data
            http_req.add_data(data=http_args['form-data'])

        return urllib2.urlopen(http_req)

class OAuth(Auth):
    def __init__(self, oauth_consumer, oauth_token={}, callback=None):
        Auth.__init__(self, oauth_consumer, oauth_token, callback)

    def request(self, http_url, http_method, http_args={}, headers={}):
        return self.oauth_request(http_url, http_method, http_args, headers)

    def request_token(self):
        resp = self.oauth_request(self.request_token_url, 'GET')
        oauth_token = dict(urlparse.parse_qsl(resp.read()))
        self.authorize_url = self.authorize_url % (oauth_token['oauth_token'], self.callback)
        self.oauth_token = {'key': oauth_token['oauth_token'], 'secret': oauth_token['oauth_token_secret']}
        return self.oauth_token

    def access_token(self, oauth_token={}):
        self.oauth_token = oauth_token or self.oauth_token
        resp = self.oauth_request(self.access_token_url, 'GET')
        oauth_token = dict(urlparse.parse_qsl(resp.read()))
        self.oauth_token = {'key': oauth_token['oauth_token'], 'secret': oauth_token['oauth_token_secret']}
        return self.oauth_token

class XAuth(Auth):
    def __init__(self, oauth_consumer, username, passwd):
        Auth.__init__(self, oauth_consumer)
        self.oauth_token = self.xauth(username, passwd)

    def request(self, http_url, http_method, http_args={}, headers={}):
        return self.oauth_request(http_url, http_method, http_args, headers)

    def xauth(self, username, passwd):
        http_args = {
            'x_auth_username': username,
            'x_auth_password': passwd,
            'x_auth_mode': 'client_auth'
        }
        resp = self.oauth_request(self.access_token_url, 'GET', http_args)
        oauth_token = dict(urlparse.parse_qsl(resp.read()))
        return {'key': oauth_token['oauth_token'], 'secret': oauth_token['oauth_token_secret']}

usage ='''
>>> # Usage:
>>> client = OAuth(consumer)                    # Can also provide callback argument
>>> request_token = client.request_token()      # Keep the returned request_token
>>> print client.authorize_url                  # You need to verify the authorization at client.authorize_url
>>> client = OAuth(consumer, request_token)     # Processing in the callback if provide callback argument
>>> access_token = client.access_token()
>>> body = {'status': 'test by ouath'}
>>> client.request('/statuses/update', 'POST',  body)
>>>
>>> # OR
>>> client = OAuth(consumer, access_token)
>>> body = {'status': 'test by ouath'}
>>> client.request('/statuses/update', 'POST',  body)
>>>
>>> # OR
>>> client = XAuth(consumer, usernanem, passwd)
>>> body = {'status': 'test by ouath'}
>>> client.request('/statuses/update', 'POST',  body)
>>> '''

if __name__ == '__main__':
    consumer = {
        'key': config.consumer_key,
        'secret': config.consumer_secret
    }
    client = XAuth(consumer, config.client_key, config.client_passwd)
    body = {'status': 'test2'}
    client.request('/statuses/update', 'POST',  body)