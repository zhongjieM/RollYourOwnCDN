'''
Created on Apr 14, 2014

'''


import argparse
import os


#HOME_DIR = os.getcwd()
#DIR = HOME_DIR + '/db_geoip/'
#DIR = '../db_geoip/'
DIR = '/'
BLOCK_DIR = 'blocks/'
LOC_DIR = 'locations/'
BLOCK_SUFFIX = '_blocks.csv'
LOC_SUFFIX = '_locations.csv'
BLOCK_BASE = 10000000  # 10,000,000
LOC_BASE = 10000  # 10,000



def split_blocks_file():
    print 'Splitting Blocks file...'
    block_file = open(DIR + 'GeoLiteCity-Blocks.csv', 'r')
    raw_lines = block_file.readlines()
    lines = raw_lines[2:]
    base = BLOCK_BASE
    start = 1
    filename = create_blocks_subfilename(start)
    data = []
    for line in lines:
        columns = line.split(',')
        start_ip = long(columns[0].split('"')[1])
        end_ip = long(columns[1].split('"')[1])
        loc = long(columns[2].split('"')[1])
        edited_line = str(start_ip) + ',' + str(end_ip) + ',' + str(loc) + '\n'
        if start_ip > (start + 1) * base:
            # wrote into file
            wrote_file(filename, data)
            start += 1
            filename = create_blocks_subfilename(start)
            data = []
        data.append(edited_line)


def split_locations_file():
    print 'Splitting Location file...'
    location_file = open(DIR + "GeoLiteCity-Location.csv", 'r')
    raw_lines = location_file.readlines()
    lines = raw_lines[2:]
    base = LOC_BASE
    start = 0
    filename = None
    data = None
    for line in lines:
        columns = line.split(',')
        loc_id = int(columns[0])
        if '"' in columns[5]:
            longtitude = float(columns[6])
            latitude = float(columns[7])
        else:
            longitude = float(columns[5])
            latitude = float(columns[6])
        edited_line = str(loc_id) + ',' + str(longitude) + ',' + str(latitude) + ',' + columns[1] + ',' + columns[3] + '\n'
        if loc_id > start * base:
            wrote_file(filename, data)
            start += 1
            filename = create_locations_subfilename(start)
            data = []
        data.append(edited_line)


def cleanup():
    cleanup_blocks()
    cleanup_locations()


def cleanup_blocks():
    if os.path.isdir(BLOCK_DIR) is False:
        return
    for file in os.listdir(BLOCK_DIR):
        file_path = os.path.join(BLOCK_DIR, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except:
            continue


def cleanup_locations():
    if os.path.isdir(LOC_DIR) is False:
        return
    for file in os.listdir(LOC_DIR):
        file_path = os.path.join(BLOCK_DIR, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except:
            continue


def create_blocks_subfilename(start):
    if os.path.exists(BLOCK_DIR) is False:
        os.makedirs(BLOCK_DIR)
    filename = BLOCK_DIR + str(start) + BLOCK_SUFFIX
    return filename


def create_locations_subfilename(start):
    if os.path.exists(LOC_DIR) is False:
        os.makedirs(LOC_DIR)
    filename = LOC_DIR + str(start) + LOC_SUFFIX
    return filename


def wrote_file(filename, data):
    if filename is None or data is None:
        return
    f = open(filename, 'w')
    for d in data:
        f.write(d)


def parse_arguments():
    '''
    Set up the command line arguments parser
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', type=str,
                        default='enzen',
                        action='store',
                        help='Please specify the source GEOIP database directory.')
    parser.add_argument('-d', '--dest', type=str,
                        default='enzen', action='store',
                        help='Please specify the destination GEOIP splitted file directory.')
    return parser.parse_args()


def init(source_path, dest_path):
    global DIR, BLOCK_DIR, LOC_DIR
    DIR = source_path + DIR
    BLOCK_DIR = dest_path + '/' + BLOCK_DIR
    LOC_DIR = dest_path + '/' + LOC_DIR


def main():
    print 'Splitting GeoIP source database file...'
    args = parse_arguments()
    source_path = args.source
    dest_path = args.dest
    init(source_path, dest_path)
    cleanup()
    split_blocks_file()
    split_locations_file()


if __name__ == '__main__':
    main()
