import json
import requests
import datetime
from time import strptime
import logging

class Cloud:
    json_token_request = '{"auth":{"tenantName": "%s", "passwordCredentials": {"username": "%s", "password": "%s"}}}'
    url_keystone = None
    tenant_name = None
    username = None
    password = None
    token = None 
    expire = None
    'Make Cloud follow Singleton pattern'
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def parse_token(self, json_resp):
        return json_resp["access"]["token"]["id"]

    def parse_expire(self, json_resp):
	# Date string example: "2012-02-05T00:00:00"
	expire_time = json_resp["access"]["token"]["expires"]
	logging.debug("New keystone expire time: %s"%expire_time)
	return datetime.datetime(*strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")[:6])
    
    def request_keystone_token(self):
        'check if token is expired'
	if (self.expire == None or datetime.datetime.now() > self.expire):
            logging.info('Keystone token expired, request new token')
	    headers = {'Content-type': 'application/json'}
	    req = self.json_token_request%(self.tenant_name, self.username, self.password)
	    logging.debug("Receive keystone response: %s"%req)

            resp = requests.post(self.url_keystone, data=req, headers=headers).json()
            self.token = self.parse_token(resp)
            self.expire = self.parse_expire(resp)
        return self.token

    def request_scale(self, alarm_url):
        token = self.request_keystone_token()
	headers = {"X-Auth-Token":"%s"%token}
	logging.debug("Send scaling request to: %s"%alarm_url)
        resp = requests.post(alarm_url, headers=headers)
	logging.debug("Receive response after scale: %s"%resp)
