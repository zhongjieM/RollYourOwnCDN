'''
Created on Apr 13, 2014

@author: kevin
'''

from subprocess import Popen
import subprocess

import cdns


def main():
    cdn_dict = cdns.CDN_MAP;
    response = []
    for key in cdn_dict:
        location = cdn_dict[key][0]
        ip = cdn_dict[key][1]
        p = Popen(['scamper', '-i', ip], stdout=subprocess.PIPE)
        print 'Location: %s; IP: %s'%(location, ip)
        msg = p.communicate()[0]
        lines = msg.split('\n')
        for line in lines:
            cols = line.split('  ')
            if len(cols) < 3:
                continue
            last_time = cols[2]
        print 'Location: %s; RTT: %s'%(location, last_time)


if __name__ == "__main__":
    main()
