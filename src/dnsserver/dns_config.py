DEFAULT_DNS_AREA_IP = '129.10.117.186'
DNS_DOMAIN_START = 2164916224
DNS_DOMAIN_END = 2164981759

debug = False


def verbose_print(content):
    global debug
    if debug:
        print content
