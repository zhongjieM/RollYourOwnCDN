#!/usr/bin/env python

'''
Created on Apr 2, 2014

@author: kevin
'''


from _struct import unpack
import atexit
import random
import socket
import sys
import time


HOST_NAME = socket.gethostname()
PORT = 34567


class Client:
    def __init__(self, dnsHostName, dnsPort):
        self._sock = self._initSock(dnsHostName, dnsPort)

    def _initSock(self, dnsHostName, dnsPort):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error, msg:
            print msg
            exit(1)
        self._dnsHost = socket.gethostbyname(dnsHostName)
        self._dnsPort = dnsPort
        sock.connect((self._dnsHost, self._dnsPort))
        return sock

    def send(self, msg):
        try:
            self._sock.send(msg)
            response = self._sock.recv(1024)
            dns_packet = DNSPacket()
            dns_packet.unpack(response)
            answers = dns_packet.answers
            for answer in answers:
                print 'Question: %s;\n Answer is: %s' % \
                    (answer.question, bite2IP(answer.answer))
        except socket.error, msg:
            print msg
            exit(1)

    def close(self):
        if self._sock:
            self._sock.close()
            print 'client closed'


def bite2IP(data):
    ip_1 = unpack('!B', data[0])[0]
    ip_2 = unpack('!B', data[1])[0]
    ip_3 = unpack('!B', data[2])[0]
    ip_4 = unpack('!B', data[3])[0]
    return '%d.%d.%d.%d' % (ip_1, ip_2, ip_3, ip_4)


def main(msg='Hi DNS Server'):
    client = Client(HOST_NAME, PORT)
    atexit.register(cleanup, client)
    ranid = random.randint(0, 2 ** 16)
    dns_questions = [DNSQuestion('neu.edu'), DNSQuestion('ccs.neu.edu')]
    dns_packet = DNSPacket(ranid=ranid, qr=0, questions=dns_questions)
    pack = dns_packet.pack()
    while 1:
        client.send(pack)
        time.sleep(5)


def cleanup(client):
    if client:
        client.close()

if __name__ == '__main__':
    argvLen = len(sys.argv)
    sys.path.append('../src/dnsserver')
    from dnspacket import DNSPacket
    from dnspacket import DNSQuestion
    if argvLen == 1:
        main()
        pass
    if argvLen >= 2:
        main(sys.argv[1])
        pass
