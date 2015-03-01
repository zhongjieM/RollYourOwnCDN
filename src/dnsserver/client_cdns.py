'''
Created on Apr 18, 2014

'''


'''
{String   , {byte[], float}}
{client ip, {CDN IP, RTT from this CDN to this client}}
'''
import cdns
from dns_config import verbose_print as vp


RECORD_INIT_VALUE = -1
BEST_RTT_INIT_VALUE = 10000
dict_clients = {}


'''
TODO:
Load data from disk when the server starts
'''
def load_data():
    pass


'''
String -> None
'''
def initit_client(client_addr):
    record = {}
    for cdn in cdns.CDNS:
        record[cdn] = RECORD_INIT_VALUE
    dict_clients[client_addr] = record


'''
String, byte[], float -> None
'''
def add_cdn_rtt_for_client(client_addr, cdn, rtt):
    if client_addr not in dict_clients:
        initit_client(client_addr)
    dict_clients[client_addr][cdn] = rtt


'''
String -> byte[] / None
'''
def find_best_cdn(client_addr):
    vp('++++++++++++++++++')
    vp(dict_clients)
    vp('++++++++++++++++++')
    vp(client_addr)
    vp('++++++++++++++++++')
    if client_addr not in dict_clients:
        initit_client(client_addr)
    best_rtt = BEST_RTT_INIT_VALUE
    record = dict_clients[client_addr]
    for cdn in record:
        rtt = record[cdn]
        if rtt == RECORD_INIT_VALUE:
            best_one = cdn
            break
        else:
            if best_rtt > rtt:
                best_rtt = rtt
                best_one = cdn
    return best_one
