#!/usr/bin/env python
import SocketServer
import argparse
import atexit

from httprequesthandler import CDNHttpRequestHandler


class CDNHttpServer:
    '''
    The Constructor of CDNHttpServer.
    Given a String represents the host address of server, and a
    Number represents the port number of the CDNHttpServer that
    will listen to. Setup the HTTP server handler and activate
    this CDNHttpServer
    '''
    def __init__(self, port):
        self.host = '0.0.0.0'
        #self.host = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.http_serv_handler = CDNHttpRequestHandler
        self.httpd = SocketServer.TCPServer((self.host, self.port),
                                            self.http_serv_handler)
        self.load_cache()

    def start(self):
        print 'CDN HTTP Server activated.'
        print 'Host Address: %s. Listen on Port: %d' % (self.host, self.port)
        self.httpd.serve_forever()

    def stop(self):
        '''
        Close the HTTP server
        '''
        self.httpd.server_close()
        print 'CDN HTTP Server closed'

    def load_cache(self):
        CDNHttpRequestHandler.CDNCache.load()


def cleanup(cdn_http_server):
    cdn_http_server.stop()


def parse_arguments():
    '''
    Set up the command line arguments parser
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--origin', type=str,
                        default='ec2-54-85-79-138.compute-1.amazonaws.com',
                        action='store',
                        help='The name of the origin server for the CDN')
    parser.add_argument('-p', '--port', type=int,
                        default='51150', action='store',

                        help='The port number that the HTTP server binds to')
    return parser.parse_args()


def main():
    args = parse_arguments()
    cdn_http_server = CDNHttpServer(args.port)
    atexit.register(cleanup, cdn_http_server)
    cdn_http_server.start()


if __name__ == '__main__':
    main()
