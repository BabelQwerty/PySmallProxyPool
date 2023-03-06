"""
python3 -m pip install requests colorslogging
"""

import requests
from colorslogging import *
from pymongo import MongoClient
from concurrent.futures import (
    ThreadPoolExecutor, as_completed
)
quake_api = 'quake_api'
mongo_host = 'mongo_host'
mongo_user = 'mongo_user'
mongo_pwd = 'mongo_pwd'

class MongoDBClient(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance=super(MongoDBClient, cls).__new__(cls)
        return cls.instance
 
    def __init__(self):
        local_host=mongo_host
        local_port=27017
        self.local_client=MongoClient(local_host, local_port, connect=False, maxPoolSize=2000)
 
        online_host=mongo_host
        online_port=27017
        client=MongoClient(online_host, online_port,connect=False, maxPoolSize=2000)
        db_user=mongo_user
        password=mongo_pwd
        db=client.admin
        db.authenticate(db_user, password, mechanism='SCRAM-SHA-1')
        self.online_client=client
 
    def getMongo_Local_Client(self):
        return self.local_client
 
    def getMongo_Online_Client(self):
        return self.online_client

def ipinfo_req(item):
    try:
        ip = requests.get('https://ipinfo.io' , 
             proxies = {
                'http':f'socks5://{item["ip"]}:{item["port"]}',
                'https':f'socks5://{item["ip"]}:{item["port"]}'
            } , 
            timeout=5,
            verify=False
        ).json()['ip']
        return ip
    except:
        return False

# def do_grab_socks(client , item , collection):
def do_grab_socks(datas):
    # collection,item  = datas
    item  = datas
    logger.info(type(item))
    if ipinfo_req(item):
        item.update({'valid':True})
    else:
        item.update({'valid':False})
    return item


def grab_sock5_from_quake():
    headers = {
        'X-QuakeToken': quake_api,
        'Content-Type': 'application/json',
    }

    json_data = {
        'query': 'service:socks5 && response:"0x0 (No authentication)" && port:1080 && country: "United States of America"',
        'start': 0,
        'size': 500,
    }

    response = requests.post('https://quake.360.cn/api/v3/search/quake_service', headers=headers, json=json_data)
    # with MongoDBClient().getMongo_Online_Client() as client:
    # collection=client['proxy']["socks_from_quake_raw"]
    with ThreadPoolExecutor(max_workers=10) as t:
        obj_list = []
        for item in response.json()['data']:
            # datas = (collection , item)
            # obj = t.submit(do_grab_socks, datas)
            obj = t.submit(do_grab_socks, item)
            obj_list.append(obj)

        for future in as_completed(obj_list):
            try:
                data = future.result()
                logger.info(repr(data))
            except Exception as e1:
                logger.error(repr(e1.args))

grab_sock5_from_quake()
