'''
Created on Apr 17, 2014

'''
import math
import os
import socket
import struct
import time

import cdns
import client_cdns as cc
from dns_config import DEFAULT_DNS_AREA_IP
from dnspacket import DNSPacket, DNSAnswer, build_qname
from dns_config import verbose_print as vp


# DNS server buffer size. Normally, this buffer size will not exceed 512 bytes.
# For safety, I set it to 1024 bytes to guarantee enough space for the data.
BUF_SIZE = 1024

# The minimum DNS packet length is the header of a DNS packet (12 bytes)
MIN_DNS_QUESTION_LEN = 12


DIR = os.getcwd()  # + '/dnsserver/'
BLOCKS_DIR = DIR + '/blocks/'
LOC_DIR = DIR + '/locations/'
BLOCK_SUFFIX = '_blocks.csv'
LOC_SUFFIX = '_locations.csv'
BLOCK_BASE = 10000000
LOC_BASE = 10000
PRIVATE_IP_RANGE = [(167772160, 184549375), (2886729728, 2887778303), (3232235520, 3232301055)]
8,4795,0304
EARTH_RADIUS = 6378.137

debug = True

class DNSServer:
    '''
    In our DNS server, for client query, DNS server uses UDP.
    Because normally, the response content will not exceed 512
    bytes. Thus UDP is sufficient for such requirement to
    accelerate DNS response speed and decrease DNS load.
    '''
    def __init__(self, name, port):
        self._target_qname = name
        self._port = port
        self._sock = self._setup(self._port)
        self.blocks = {}
        self.locations = {}
        self._load_geoip_files()

    def _load_geoip_files(self):
        print 'Please wait, loading GeoIP files...'
        self._load_geoip_blocks();
        self._load_geoip_locations()
        print 'Loading GeoIP files complete!'

    def _load_geoip_blocks(self):
        print 'Loading GeoIP Blocks files.'
        if os.path.isdir(BLOCKS_DIR) is False:
            print 'Cannot find GeoIP Blocks file!'
            return
        for the_file in os.listdir(BLOCKS_DIR):
            file_path = BLOCKS_DIR + the_file
            if os.path.isfile(file_path):
                f = open(file_path, 'r')
                lines = f.readlines()
                data = []
                for line in lines:
                    columns = line.split(',')
                    record = (long(columns[0]), long(columns[1]), int(columns[2]))
                    data.append(record)
                self.blocks[the_file] = data

    def _load_geoip_locations(self):
        print 'Load GeoIP Locations files...'
        if os.path.isdir(LOC_DIR) is False:
            print 'Cannot find GeoIP Locations files!'
            return
        for the_file in os.listdir(LOC_DIR):
            file_path = LOC_DIR + the_file
            if os.path.isfile(file_path):
                f = open(file_path, 'r')
                lines = f.readlines()
                data = []
                for line in lines:
                    columns = line.split(',')
                    record = (int(columns[0]), float(columns[1]), float(columns[2]), columns[3], columns[4])
                    data.append(record)
                self.locations[the_file] = data

    '''
    Give a String which is the host name and
         an integer which is the port number.
    Setup the server by creating a socket and
    bind the host and port to the socket.
    Return a workable socket object
    '''
    def _setup(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error, msg:
            # handle exception
            handleException(msg)
        sock.bind(('0.0.0.0', port))
        sockname = sock.getsockname()
        print 'Already bind DNS to %s : %d' % (sockname[0], sockname[1])
        return sock

    def listen(self):
        try:
            print 'listen to the port : %d' % (self._port)
            while 1:
                request = self._sock.recvfrom(BUF_SIZE)
                self._process_data(request)
            print 'stopped'
        except socket.error, msg:
            handleException(msg)
            self.close()

    def close(self):
        try:
            self._sock.close()
            print 'socket closed'
        except socket.error, msg:
            handleException(msg)
        except BaseException, msg:
            handleException(msg)

    '''
    (byte[], (String, Integer)) -> Boolean
    Given the (received data, client address), process this request.
    Return False: if this data is invalid and dropped.
           True : if this data is processed appropriately.
    '''
    def _process_data(self, request):
        data = request[0]
        addr = request[1]
        if self._verify_recv_data(data) is False:
            # Drop this packet
            vp('1')
            return False
        # The data received is a valid DNS Question packet
        # Parse it and get the DNSPacket object
        dns_packet, parse_result = self._process_dns_question(data)
        # DNSPacket object was attempted to be built. Check the result
        # to decide drop it or not
        if parse_result is False:
            vp('2')
            return False
        # DNSPacket object was built; now get the question part from it
        # and handle the question
        vp('----------------------------------------------------------------')
        vp('Received DNS Packet as:')
        vp(dns_packet)
        questions = dns_packet.questions
        # Check the validation of questions part
        if questions and len(questions) > 0 and \
            (questions[0].question == self._target_qname or
             questions[0].qtype == 2):
            # get the first question and keep processing it
            # In our application RIGHT NOW, we only handle the first question
            question = questions[0]
            answer = self._find_answer(question, addr[0])
            dns_answer_packet = self._build_dns_answer(dns_packet, answer)
            vp('Send DNS Answer as:')
            vp(dns_answer_packet)
            vp('----------------------------------------------------------------')
            self._send_dns_answer(dns_answer_packet.pack(), addr)
            return True
        else:
            # questions part is invalid, drop this request
            vp('3')
            dns_answer_packet = self._build_dns_answer_host_not_found(dns_packet)
            self._send_dns_answer(dns_answer_packet.pack(), addr)
            return False

    '''
    byte[] -> Boolean
    Verify if received data is a valid DNS packet
    TODO: Not fully implemented it yet.
    '''
    def _verify_recv_data(self, data):
        return len(data) > MIN_DNS_QUESTION_LEN

    '''
    byte[] -> (DNSPacket, Boolean) or (None, False)
    Given the binary data received from socket which which is a potentially
    valid DNS Question. Unpack this DNS question and give the unpack result
    Return  (DNSPacket object, True) if parsed successfully;
            (None, False) if parsed failed.
            (DNSPacket object, False) if this packet is an answer.
    '''
    def _process_dns_question(self, data):
        dns_packet = DNSPacket()
        try:
            dns_packet.unpack(data)
        except BaseException, msg:
            print 'This is not a valid DNS Question Packet: %s' % (msg)
            return None, False
        # TODO: need a way to know if the current parsed dns_packet is valid
        # or not so that here if invalid, need to return (None, False)
        if dns_packet.qr == 1:
            # It is a DNS response, return (DNSPacket object, False)
            return dns_packet, False
        else:
            return dns_packet, True

    '''
    DNSQuestion, String -> DNSAnswer
    Given an object of DNSQuestion, and the client IP address.
    Return an object of DNSAnswer for the given DNS question from the client.
    '''
    def _find_answer(self, question, addr):
        if question.qtype == 2:
            root_server = 'i.root-servers.net'
            answer = DNSAnswer(build_qname(root_server), question.question,
                               rtype=question.qtype, rclass=question.qclass,
                               TTL=600)
        else:
            # 1. first need to check if addr is Private ip. Which means client
            # is at the same local network with DNS server.
            # 1) If it is a local Address, use DNS's IP address to find out the
            # best CDN for the client.
            # 2) If it is a public global Address, use the real address to find
            # out the best CDN for the client.
            # 2. Then send the client IP address to CDN.
            # 3. CDNs ping the client IP for one time and send the RTT back to
            #    DNS Server.
            # 4. DNS Server judges which one is the best and send the answer back
            #    to the client.
            # 5. If DNS server get nothing from CDNs, it will use GEOIP to give
            #    a rough answer based on client's IP location.
            # *  How to use GEOIP became a problem.
            # *  HttpServer needs to have another program to run to deal with ping
            #    work
            if self._is_ip_private(addr):
                real_addr = DEFAULT_DNS_AREA_IP
            else:
                real_addr = addr
            ans = self._primary_solution(real_addr)
            if ans is None:
                ans = self._geo_ip_solution(real_addr)
            answer = DNSAnswer(ans, question.question,
                               rtype=question.qtype, rclass=question.qclass)
        return answer

    '''
    DNSQuestion, DNSAnswer -> DNSPacket
    '''
    def _build_dns_answer(self, qp, answer):
        question = qp.questions[0]
        dns_answer_packet = DNSPacket(ranid=qp.ranid, qr=1, opcode=qp.opcode,
                                      aa=qp.aa, tc=qp.tc, rd=qp.rd, ra=qp.ra,
                                      z=qp.z, rcode=0, nscount=0, arcount=0,
                                      questions=[question], answers=[answer])
        return dns_answer_packet

    '''
    DNSQuestion -> DNSPacket
    '''
    def _build_dns_answer_host_not_found(self, qp):
        dns_answer_packet = DNSPacket(ranid=qp.ranid, qr=1, opcode=qp.opcode,
                                      aa=qp.aa, tc=qp.tc, rd=qp.rd, ra=qp.ra,
                                      z=qp.z, rcode=3, nscount=0, arcount=0,
                                      questions=qp.questions, answers=[])
        return dns_answer_packet

    '''
    DNSAnswer, (String, Integer) -> None
    '''
    def _send_dns_answer(self, dns_answer, addr):
        try:
            self._sock.sendto(dns_answer, addr)
        except socket.error, msg:
            handleException(msg)

    # -------------------------------------------------------------------------
    #    Primary Solution

    '''
    String -> byte[] / None
    Given the address of a client in String format, find the best CDN for this
    client. If the best CDN exists, return the CDN's IP address in struct pack
    byte[] format. If not, return None.
    '''
    def _primary_solution(self, addr):
        vp('primary solution for client: %s' % (addr))
        return cc.find_best_cdn(addr)

    # -------------------------------------------------------------------------
    #    GeoIP Solution
    # TODO: put it into another python script file

    '''
    <BACKUP SOLUTION>
    String -> byte[]
    Given the address of the client. Get the best CDN according the GeoIP info.
    Return the best CDN address in byte[] format (struct packed).
    '''
    def _geo_ip_solution(self, addr):
        result = self._is_ip_private(addr)
        if self._is_ip_private(addr):
            client_location = self._get_longitude_latitude(DEFAULT_DNS_AREA_IP)
        else:
            client_location = self._get_longitude_latitude(addr)
            ans = cdns.ORIGIN
        if client_location:
            ans = self._get_best_cdn_by_geoip(client_location)
        return ans

    '''
    (float, float) -> byte[]
    Given the client's latitude and longitude values, find the best matched CDN
    for it.
    Return the best CDN's ip address in byte[] format
    '''
    def _get_best_cdn_by_geoip(self, client_location):
        smallest = -1
        map = cdns.CDN_MAP
        for key in map:
            s = self._get_distance(map[key][3], client_location)
            if smallest == -1:
                smallest = s
                ans = key
            elif smallest > s:
                smallest = s
                ans = key
        return ans

    '''
    (float, float), (float, float) -> float
    Given two locations' latitudes and longitudes, calculate the distance
    between them.
    '''
    def _get_distance(self, loc1, loc2):
        radlat1 = rad(loc1[0])
        radlat2 = rad(loc2[0])
        a = radlat1 - radlat2
        b = rad(loc1[1]) - rad(loc2[1])
        s = 2 * math.asin(math.sqrt(math.pow(math.sin(a / 2), 2) \
                                        + math.cos(radlat1) * math.cos(radlat2) \
                                        * math.pow(math.sin(b / 2), 2)))
        s *= EARTH_RADIUS
        if s > 0:
            return s
        else:
            return -s

    '''
    String -> Boolean Given a IP String in human readable format, check if it is
    a private IP.
    Example: _is_ip_private('192.168.000.001') -> True
             _is_ip_private('129.010.117.186') -> False
    Private IP Rage from:
        10.0.0.0    - 10.255.255.255
        172.16.0.0  - 172.31.255.255
        192.168.0.0 - 192.168.255.255
    '''
    def _is_ip_private(self, ip):
        # check if this ip String is valid or not
        try:
            ip_value = struct.unpack('!L', socket.inet_aton(ip))[0]
        except BaseException, msg:
            # If this ip String invalid, regard it as an private ip.
            # Use DNS IP address to do that.
            return True
        for iprange in PRIVATE_IP_RANGE:
            if ip_value >= iprange[0] and ip_value <= iprange[1]:
                return True
        return False

    '''
    String -> (float, float) or None
    Given a string of IP address;
    Get the longitude and latitude of the IP location.
    Return origin location if the IP not valid or GeoIP files are broken.
    '''
    def _get_longitude_latitude(self, ip=cdns.ORIGIN_STR):
        # convert string ip to long value
        packedIP = socket.inet_aton(ip)
        ip_value = struct.unpack('!L', packedIP)[0]
        file_prefix = ip_value / BLOCK_BASE
        key = str(file_prefix) + BLOCK_SUFFIX
        if key in self.blocks:
            records = self.blocks[key]
            for record in records:
                start_ip = record[0]
                end_ip = record[1]
                loc_id = record[2]
                if ip_value >= start_ip and ip_value <= end_ip:
                    record = self._search_locations(loc_id)
                    if record:
                        return (record[1], record[2])
        else:
            vp('key not in blocks')
        return None

    '''
    integer -> (integer, float, float, String, String) / None
    Given a location id in GeoIP database, get this location record
    Return None if this record not exists.
    '''
    def _search_locations(self, loc_id):
        key = str((loc_id / LOC_BASE) + 1) + LOC_SUFFIX
        if key in self.locations:
            records = self.locations[key]
            for record in records:
                if int(record[0]) == loc_id:
                    return record
        return None

    ## ------------------------------------------------------------------------

def rad(d):
    return d * math.pi / 180.0


def handleException(msg):
    print msg
    exit(0)
