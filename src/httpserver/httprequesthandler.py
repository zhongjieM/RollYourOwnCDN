'''
Created on Apr 6, 2014

'''
from SimpleHTTPServer import SimpleHTTPRequestHandler
from collections import deque
import httplib
import os
import socket
from subprocess import PIPE
import subprocess


CACHE_MAX_SIZE = 9 * 1024 * 1024  # Byte
DNS_SERVER = 'cs5700cdnproject.ccs.neu.edu'
DNS_PORT = 60000



class Cache:
    def __init__(self, cache_max_size):
        self.cache_max_size = cache_max_size
        # cache field
        # cache field is queue structure.
        # Cache stores tuples of (path_to_file, file_size)
        # 1. Once a new file is get from origin, it appends to
        #    the end of cache
        # 2. Once the local cache is not enough for storing the
        #    new file received from origin, it remove the files
        #    from the top of it until the space is sufficient
        #    for the new file received from origin.
        # 3. When the client request a file in the cache, it get
        #    the item out from the queue, processing it and append
        #    it again to the end of the queue.
        self.cache_store = deque()
        # the cache's available space for storing files.
        # initially, it is set to CACHE_MAX_SIZE
        self.cache_avail = self.cache_max_size

    def load(self):
        self.cache_store = deque()
        self.cache_avail = self.cache_max_size
        rootdir = os.getcwd()
        cache_dir = rootdir + '/wiki/'
        if os.path.isdir(cache_dir) == False:
            return
        self._load_all_file(cache_dir)
        print self.cache_avail

    def _load_all_file(self, path):
        for the_file in os.listdir(path):
            file_path = path + the_file
            if os.path.isdir(file_path):
                self._load_all_file(file_path + '/')
            elif os.path.isfile(file_path):
                filesize = os.path.getsize(file_path)
                if self.cache_avail < filesize:
                    # remove this file
                    os.remove(file_path)
                else:
                    self.cache_store.append((file_path, filesize))
                    self.cache_avail -= filesize

    '''
    Check if local cache has enough space for the new file
    if local cache doesn't has enough space,
    Delete the earliest files from the local cache until
    there is enough room for the new file.
    Save the file into local cache and record it.

    '''
    def add_new_file(self, new_file_path, new_file_data):
        new_file_size = len(new_file_data)
        # Try to make room for new file
        if self._make_room(new_file_size) == True:
            # make room successfully
            # save file to the path
            save_result = self._save_file(new_file_path, new_file_data)
            if save_result == True:
                # save file successfully
                # add new record to the end of cache_store queue
                self.cache_store.append((new_file_path, new_file_size))
                # update cache_avail
                self.cache_avail -= new_file_size
                return True
        return False

    '''
    Given a path, check if the file to which the path points is exists.
    If exists and file really exists in the local disk, return True;
    Otherwise, return False
    '''
    def update_cache(self, path):
        record = self._is_file_in_cache(path)
        if record:
            try:
                self.cache_store.remove(record)
            except ValueError, msg:
                print msg
                return False
            if os.path.exists(record[0]):
                self.cache_store.append(record)
                return True
        return False

    '''
    Given a file's path, check if it is in the local cache
    If in the cache, return the record which is a tuple in the cache;
    otherwise, return None
    '''
    def _is_file_in_cache(self, path):
        for c in self.cache_store:
            if path == c[0]:
                return c
        return None

    '''
    Make room for the new file in the cache according to the new file size.
    If new file size exceeds the maximum cache size, return False directly;
    Remove the left-most file in the cache and release the space in the disk,
    until the available space in the cache is sufficient for the new file.
    '''
    def _make_room(self, new_file_size):
        if new_file_size > self.cache_max_size:
            return False
        else:
            while self.cache_avail <= self.cache_max_size and\
                self.cache_avail < new_file_size:
                file_record = self.cache_store.popleft()
                self._remove_file(file_record[0])
                self.cache_avail += file_record[1]
            if self.cache_avail <= self.cache_max_size and\
                self.cache_avail >= new_file_size:
                return True
            else:
                return False

    '''
    Given the path of a new file and the data of the new file;
    Create the file on the path.
    Return True if created successfully; otherwise False.
    '''
    def _save_file(self, path, data):
        try:
            file_dir = os.path.dirname(path)
            os.makedirs(file_dir)
        except OSError, msg:
            # already exists.
            print msg
        try:
            f = open(path, 'w')
            f.write(data)
            f.close()
        except IOError, msg:
            print msg
            return False
        return True

    '''
    Given the path of a file which has been proved to exists in local cache.
    Get the file data.
    '''
    def _read_file(self, path):
        try:
            f = open(path, 'r')
            data = f.read()
            f.close()
            return data
        except IOError, msg:
            print msg
            return None

    '''
    Given a file's path, remove the file from the local disk.
    '''
    def _remove_file(self, path):
        try:
            os.remove(path)
        except IOError, msg:
            print msg


class CDNHttpRequestHandler(SimpleHTTPRequestHandler):

    # A static field of CDNHttpRequestHandler class which is the cache
    # of our CDN server
    CDNCache = Cache(CACHE_MAX_SIZE)

    # SimpleHTTPRequestHandler and above are an old-style class which can't use
    # super() method to call its methods.
    # To inherit their methods, the only way is to call those methods directly.

    def __init__(self, request, client_address, server):
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
        self._handle_rtt(client_address, server)

    def _handle_rtt(self, client_address, server):
        server_name, server_port, client_name, client_port = self._get_server_client_name_port(server, client_address)
        rtt = self._get_rtt_from_connection(server_name, server_port, client_name, client_port)
        self._send_rtt_to_dns((DNS_SERVER, DNS_PORT), client_name, rtt)

    '''
    Server, (String, Integer) -> String, String, String, String
    '''
    def _get_server_client_name_port(self, server, client_address):
        server_name = socket.gethostbyname(socket.gethostname())
        server_port = server.server_address[1]
        client_name = client_address[0]
        client_port = client_address[1]
        return server_name, server_port, client_name, client_port

    '''
    String String String String -> float
    Get RTT from the connection.
    Return RTT value or -1 if not get RTT
    '''
    def _get_rtt_from_connection(self, server_name, server_port, client_name, client_port):
        arg3 = 'src ' + server_name + ':' + str(server_port) + ' and dst ' + client_name + ':' + str(client_port)
        process = subprocess.Popen(['ss', '-i', arg3], stdout=PIPE)
        results = process.communicate()[0].split(' ')
        for result in results:
            if 'rtt' in result:
                rtt = float(result.split(':')[1].split('/')[0])
                return rtt
        return -1.0

    '''
    (String, Integer), String, float -> None
    Start a new Thread to send RTT with the client IP back to DNS.
    '''
    def _send_rtt_to_dns(self, dns_server_address, client_IP, rtt):
        # TODO: start a new thread to connect with DNS server to send the RTT
        result = '%s %f' % (client_IP, rtt)
        print result
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('129.10.117.186', 60000))
            sock.send(result)
            data = sock.recv(1024)
            print data
        except socket.error, msg:
            print msg

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            # client request a directory, our CDN http server can't handle this
            # kind of query. Thus seek help from the origin server
            self._request_origin_server(path)
            return
        # client request a file
        # check if file in the cache
        cache_update_result = CDNHttpRequestHandler.CDNCache.update_cache(path)
        if cache_update_result == True:
            # send the file to the client
            self._request_local_cache(path)
        else:
            self._request_origin_server(path)

    '''
    Given a path where the file is 100% sure exists in local CDN cache.
    Send this file back to the server if open successfully.
    Otherwise, send 404 error to the client.
    '''
    def _request_local_cache(self, path):
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError, msg:
            print msg
            self._send_error_404()
            return
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()

    def _request_origin_server(self, path):
        # Send request to the origin server
        # Receive file from origin server
        response = self._send_request_to_origin_server()
        if response is None:
            self._send_error_404()
            return
        status = response.status
        if status == 200:
            # Save content into local cache
            print path
            self._save_file_in_cache(path, response.read())
            # Read file from cache and send to client
            self._request_local_cache(path)
        else:
            # Send the response get from origin server to the client directly
            self.send_response(response.status, response.msg)
            for head in response.getheaders():
                self.send_header(head[0], head[1])
            self.end_headers()

    '''
    File not exists both in local cache or origin server.
    Send 404 error to client.
    '''
    def _send_error_404(self):
        self.send_error(404, 'File not found')

    '''
    Send request to origin server for file.
    Return file if get response.
    Otherwise, return None if origin server doesn't have this file either.
    '''
    def _send_request_to_origin_server(self):
        origin_host = 'ec2-54-85-79-138.compute-1.amazonaws.com'
        url_base = 'http://%s:8080%s'
        url = url_base % (origin_host, self.path)
        try:
            httpConn = httplib.HTTPConnection(origin_host, 8080)
            httpConn.request('GET', url)
            response = httpConn.getresponse()
            return response
        except BaseException, msg:
            print msg
            return None

    '''
    Save the received data from origin server to local cache and disk.
    '''
    def _save_file_in_cache(self, path, response):
        return CDNHttpRequestHandler.CDNCache.add_new_file(path, response)










