'''
Created on Apr 17, 2014

'''
import socket
import struct
import time

from cdns import CDN_MAP
import client_cdns as cc
from dns_config import DEFAULT_DNS_AREA_IP
from dns_config import DNS_DOMAIN_END
from dns_config import DNS_DOMAIN_START
from dns_config import verbose_print as vp


BUFF_SIZE = 1024



class StatisticServer:

    '''
    None -> None
    '''
    def __init__(self, name, port):
        self._port = 60000
        self._name = name
        self._sock = self._setup()

    '''
    None -> Socket
    '''
    def _setup(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print msg
        sock.bind(('0.0.0.0', self._port))
        sockname = sock.getsockname()
        print 'Already bind DNS statistic Server to %s : %d' % (sockname[0], sockname[1])
        return sock

    '''
    None -> None
    Listen to the RTT sent from CDNs
    '''
    def listen(self):
        print 'listen to the port: %d' % (self._port)
        try:
            while 1:
                self._sock.listen(8)
                conn, addr = self._sock.accept()
                data = conn.recv(BUFF_SIZE)
                # Reply CDN with this message
                conn.send('Received data')
                conn.close()
                self._process_data(data, addr[0])
            print 'stopped'
        except socket.error, msg:
            print msg
            self._sock.close()

    '''
    None -> None
    '''
    def close(self):
        try:
            self._sock.close()
        except socket.error, msg:
            print msg

    '''
    data -> None
    '''
    def _process_data(self, data, cdn):
        # columns should be
        # String,         float
        # Client address, RTT
        columns = data.split(' ')
        if len(columns) != 2:
            vp('Bad RTT packet')
            return False
        try:
            client_addr = columns[0]
            rtt = float(columns[1])
        except BaseException, msg:
            vp('RTT Packet Format error')
            vp(msg)
            return False
        # If client ip is within the DNS domain, use DNS ip as the client IP
        if is_ip_in_dns_domain(client_addr):
            client_addr = DEFAULT_DNS_AREA_IP
        vp('-------------------')
        vp('Received statistic : client addr: %s; CDN addr: %s; RTT: %f' % (client_addr, cdn, rtt))
        vp('-------------------')
        cc.add_cdn_rtt_for_client(client_addr, socket.inet_aton(cdn), rtt)
        return True

'''
String -> Boolean
'''
def is_ip_in_dns_domain(client_addr):
    client_ip_value = struct.unpack('!L', socket.inet_aton(client_addr))[0]
    if client_ip_value >= DNS_DOMAIN_START and client_ip_value <= DNS_DOMAIN_END:
        return True
    else:
        return False
