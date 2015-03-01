'''
Created on Apr 14, 2014

'''


import os
import socket
import struct

import cdns


HOME_DIR = os.getcwd()
DIR = HOME_DIR + '/db_geoip/'
BLOCKS_DIR = DIR + 'blocks/'
LOC_DIR = DIR + 'locations/'
BLOCK_SUFFIX = '_blocks.csv'
LOC_SUFFIX = '_locations.csv'
BLOCK_BASE = 10000000  # 10,000,000
LOC_BASE = 10000  # 10,000


def load_geoip_files():
    print 'Please wait, loading GeoIP files...'
    blocks = load_geoip_blocks();
    locations = load_geoip_locations()
    print 'Loading GeoIP files complete!'
    return blocks, locations


def load_geoip_blocks():
    print 'Loading GeoIP Blocks files.'
    if os.path.isdir(BLOCKS_DIR) is False:
        print 'Cannot find GeoIP Blocks file!'
        return
    blocks = {}
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
        blocks[the_file] = data
    return blocks


def load_geoip_locations():
    print 'Load GeoIP Locations files...'
    if os.path.isdir(LOC_DIR) is False:
        print 'Cannot find GeoIP Locations files!'
        return
    locations = {}
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
        locations[the_file] = data
    return locations


'''
    Given a string of IP address;
    Get the longitude and latitude of the IP location.
    Return origin location if the IP not valid or GeoIP files are broken.
'''
def get_longitude_latitude(blocks, locations, ip=cdns.ORIGIN_STR):
    # convert string ip to long value
    packedIP = socket.inet_aton(ip)
    ip_value = struct.unpack('!L', packedIP)[0]
    print 'ipvalue : %d' % (ip_value)
    file_prefix = ip_value / BLOCK_BASE
    key = str(file_prefix) + BLOCK_SUFFIX
    print 'key : %s' % (key)
    if key in blocks:
        records = blocks[key]
        for record in records:
            start_ip = record[0]
            end_ip = record[1]
            loc_id = record[2]
            if ip_value >= start_ip and ip_value <= end_ip:
                print 'loc id: %d'%(loc_id)
                record = search_locations(locations, loc_id)
                # TODO: for testing, print out
                if record:
                    print record
                    return (record[1], record[2])
    else:
        print 'key not in blocks'
    return None


'''
    integer -> (integer, float, float, String, String) / None
    Given a location id in GeoIP database, get this location record
    Return None if this record not exists.
'''
def search_locations(locations, loc_id):
    key = str((loc_id / LOC_BASE) + 1) + LOC_SUFFIX
    if key in locations:
        records = locations[key]
        for record in records:
            if int(record[0]) == loc_id:
                return record
    return None


def main():
    blocks, locations = load_geoip_files()
    map = cdns.CDN_MAP
    print '----------------------------'
    for key in map:
        ip = map[key][1]
        record = get_longitude_latitude(blocks, locations, ip)
        print map[key]
        print record
        print '----------------------------'

if __name__ == '__main__':
    main()
