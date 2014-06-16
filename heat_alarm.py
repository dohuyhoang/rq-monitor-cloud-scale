import json
import threading
from time import sleep
import requests
import sys
import ConfigParser
import logging
from cloud_request import Cloud
import shell as sh
CONFIG_PATH = "./cloud.conf"
DIRECT_SSH = True
'''
Alarm for each queue
'''
class Alarm:
    COOL_DOWN_TIME = 180
    def __init__(self, p_queue, p_threshold_up, p_threshold_down, p_url_up, p_url_down):
        self.url_alarm_up = p_url_up
	self.url_alarm_down = p_url_down
	if (p_threshold_up != None):
	    self.threshold_up = p_threshold_up
	else: 
	    self.threshold_up = MonitorEngine.default_threshold_up
	
	if (p_threshold_down != None):
	    self.threshold_down = p_threshold_down
	else:
	    self.threshold_down = MonitorEngine.default_threshold_down
        self.queue_name = p_queue
	self.cloud = Cloud()

    def trigger_alarm_up(self):
        self.cloud.request_scale(self.url_alarm_up)
 
    def check_threshold(self, value):
        if (self.threshold_up != None and value >= self.threshold_up):
	     logging.info("queue %s has large size: %s. trigger url up %s"%(self.queue_name, value, self.url_alarm_up))
             self.trigger_alarm_up()
	     print "Trigger up queue: %s ----- size: %s"%(self.queue_name, value)
        if (self.threshold_down != None and value < self.threshold_down):
	     logging.info("queue %s has small size: %s. trigger url down %s"%(self.queue_name, value, self.url_alarm_up))
             self.trigger_alarm_up()
             print "Trigger down queue: %s ----- size: %s"%(self.queue_name, value)

'''
Engine to continuing monitor the RQ 
'''
class MonitorEngine(threading.Thread):
    SERVER_URL = None
    INTERVAL = None
    SSH_RQ_SERVER = None

    default_threshold_up = None
    default_threshold_down = None
    def parse_policy_file(self, policy_json):
        self.alarms = []
        default_threshold_up = policy_json.get("default_threshold_up")
	default_threshold_down = policy_json.get("default_threshold_down")
	queues = policy_json["queues"]
	[self.alarms.append(Alarm(q["queue_name"], q.get("threshold_up"), q.get("threshold_down"), q["url_alarm_up"], q["url_alarm_down"])) for q in queues]

    def __init__(self, policy_json , user, password):
        self.parse_policy_file(policy_json)
	self.username = user
        self.password = password

    def query_rq_queue(self):
	if (DIRECT_SSH):
	    return sh.get_queues_all_size(self.SSH_RQ_SERVER)
        else:
            r = requests.get('%s/rq/api/v1.0/queues'%MonitorEngine.SERVER_URL, auth=(self.username, self.password))
	    return r.json()



    def run(self):
	while (True): 
	    logging.debug("Send REST request to server %s"%MonitorEngine.SERVER_URL)

            'handle json response'
            data = self.query_rq_queue()
	    print data
            [[alarm.check_threshold(d.get("size")) for d in data if d.get("queue") == alarm.queue_name] for alarm in self.alarms]
            sleep(MonitorEngine.INTERVAL)




if __name__ == '__main__':

    'Load configs'
    config = ConfigParser.ConfigParser()
    config.read(r'%s'%CONFIG_PATH)
    logging.basicConfig(filename=config.get('Log', 'log_path'),level=config.get('Log', 'log_level'))
    
    username = config.get('REST_server', 'username')
    password = config.get('REST_server', 'password')
    MonitorEngine.SERVER_URL = config.get('REST_server', 'server_url')
    MonitorEngine.INTERVAL = config.getint('General', 'request_interval')
    MonitorEngine.SSH_RQ_SERVER = "%s@%s"%(config.get('SSH', 'ssh_username')
		    , config.get('SSH', 'RQ_server')) 

    Cloud.username = config.get('OpenStack', 'username')
    Cloud.password = config.get('OpenStack', 'password')
    Cloud.tenant_name = config.get('OpenStack', 'tenant_name')
    Cloud.url_keystone = config.get('OpenStack', 'url_keystone')
    DIRECT_SSH = config.getboolean('General', 'use_ssh')
    policy_file = config.get('Scaling', 'policy_path')

    data = open(policy_file).read()
    json_data = json.loads(data)
    m = MonitorEngine(json_data, username, password)
    m.run()

