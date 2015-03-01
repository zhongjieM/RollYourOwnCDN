#!/usr/bin/env python
'''
README

This is a DNS Server.

*** In our DNS Server, for each received valid DNS Question packet,
    we ONLY handle the FIRST question in it.

'''


import argparse
import atexit
from threading import Thread

from dns_server import DNSServer
from statistic_server import StatisticServer


def parse_arguments():
    '''
    Set up the command line arguments parser
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', type=str,
                        default='cs5700cdn.example.com',
                        action='store',
                        help='The CDN-specific name that' +
                        'the DNS server translates to an IP')
    parser.add_argument('-p', '--port', type=int,
                        default='51151', action='store',
                        help='The port number that the DNS' +
                        'server will bind to')
    return parser.parse_args()


def cleanup(t1, t2):
    t1.stop()
    t2.stop()


class DNSServerThread(Thread):

    def __init__(self, name, port):
        Thread.__init__(self)
        self.name = name
        self.port = port
        self.dnsServer = DNSServer(name, port)

    def run(self):
        self.dnsServer.listen()

    def stop(self):
        self.dnsServer.close()


class StatisticServerThread(Thread):

    def __init__(self, name, port):
        Thread.__init__(self)
        self.name = name
        self.port = port
        self.statisticServer = StatisticServer(name, port)

    def run(self):
        self.statisticServer.listen()

    def stop(self):
        self.statisticServer.close()


def main():
    args = parse_arguments()
    dnsServerThread = DNSServerThread(args.name, args.port)
    statisticServerThread = StatisticServerThread(args.name, args.port)
    atexit.register(cleanup, dnsServerThread, statisticServerThread)
    dnsServerThread.start()
    statisticServerThread.start()

if __name__ == '__main__':
    main()
