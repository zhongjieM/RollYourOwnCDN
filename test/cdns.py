'''
Created on Apr 3, 2014

@author: kevin
'''
'''
ec2-54-85-79-138.compute-1.amazonaws.com        Origin server (running Web server on port 8080)
ec2-54-84-248-26.compute-1.amazonaws.com        N. Virginia
ec2-54-186-185-27.us-west-2.compute.amazonaws.com       Oregon
ec2-54-215-216-108.us-west-1.compute.amazonaws.com      N. California
ec2-54-72-143-213.eu-west-1.compute.amazonaws.com       Ireland
ec2-54-255-143-38.ap-southeast-1.compute.amazonaws.com  Singapore
ec2-54-199-204-174.ap-northeast-1.compute.amazonaws.com Tokyo
ec2-54-206-102-208.ap-southeast-2.compute.amazonaws.com Sydney
ec2-54-207-73-134.sa-east-1.compute.amazonaws.com       Sao Paulo
'''

import socket


ORIGIN_STR = '54.85.79.138'
NORTH_VIRGINIA_STR = '54.84.248.26'
OREGON_STR = '54.186.185.27'
NORTH_CALIFORNIA_STR = '54.215.216.108'
IRELAND_STR = '54.72.143.213'
SINGAPORE_STR = '54.255.143.38'
TOKYO_STR = '54.199.204.174'
SYDNEY_STR = '54.206.102.208'
SAO_PAULO_STR = '54.207.73.134'

ORIGIN = socket.inet_aton(ORIGIN_STR)
NORTH_VIRGINI = socket.inet_aton(NORTH_VIRGINIA_STR)
OREGON = socket.inet_aton(OREGON_STR)
NORTH_CALIFORNIA = socket.inet_aton(NORTH_CALIFORNIA_STR)
IRELAND = socket.inet_aton(IRELAND_STR)
SINGAPORE = socket.inet_aton(SINGAPORE_STR)
TOKYO = socket.inet_aton(TOKYO_STR)
SYDNEY = socket.inet_aton(SYDNEY_STR)
SAO_PAULO = socket.inet_aton(SAO_PAULO_STR)

CDN_MAP = {ORIGIN : ('Origin', ORIGIN_STR, ORIGIN), \
           NORTH_VIRGINI : ('North Viginia', NORTH_VIRGINIA_STR, NORTH_VIRGINI), \
           OREGON : ('Oregon', OREGON_STR, OREGON), \
           NORTH_CALIFORNIA : ('North California', NORTH_CALIFORNIA_STR, NORTH_CALIFORNIA), \
           IRELAND : ('Ireland', IRELAND_STR, IRELAND), \
           SINGAPORE : ('Singapore', SINGAPORE_STR, SINGAPORE), \
           TOKYO : ('Tokyo', TOKYO_STR, TOKYO), \
           SYDNEY : ('Sydney', SYDNEY_STR, SYDNEY), \
           SAO_PAULO : ('Sao Paulo', SAO_PAULO_STR, SAO_PAULO)}
