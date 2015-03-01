'''
Created on Apr 3, 2014

'''
from _struct import calcsize, pack_into, unpack
from ctypes import create_string_buffer

import cdns


DNS_HDR_FMT = '!HHHHHH'
DNS_HDR_LEN = 12  # Bytes
# The DNS answer format includes only:
# TYPE(2), Class(2), TTL(4), RDLENGTH(2), RDATA(4)
# ** THE NAME or pointer part will be append to the head of it.
# ** Assume the response is all the IP address
DNS_ANS_FMT = '!HHLH'
QA_TYPE_CLASS_FMT = '!HH'

QT_HOST_ADDR = 0x0001
QT_MAIL_SERV = 0x000f
QT_NAME_SERV = 0x0002
QC_INET_ADDR = 0x0001
QN_MAX_LBL_LEN = 63
QN_MAX_LEN = 253

DNS_ANS_QISP = 'QUESTION IS POINTER'

DNS_PRINT_QFMT = '--- Question: %s; Type: %d; Class: %d ---\n'
DNS_PRINT_AFMT = '--- Question: %s; Type: %d; Class: %d; TTL: %d;\n'\
                      'Length of response: %d; Response: '
DNS_PRINT_HFMT = '--- DNS Packet ---\n'\
                 'Header: ID: %d;\n'\
                 'QR: %d; Opcode: %d; AA: %d; TC: %d; RD: %d; RA: %d; Z: %d; RCODE: %d;\n'\
                 'No. Of Question: %d\n'\
                 'No. Of Answer: %d\n'\
                 'NSCOUNT: %d\n'\
                 'ARCOUNT: %d\n'\

class DNSQuestion:
    '''
    QNAME: could be a host address, a mail server or name server
    QTYPE: 0x0001: Host Address
           0x000f: Mail Server
           0x0002: Name Server
    QCLASS:0x0001: Internet address
    '''
    def __init__(self, question='', qtype=QT_HOST_ADDR, qclass=QC_INET_ADDR):
        self.question = question
        self.qtype = qtype
        self.qclass = qclass
        self.valid = False
        if  (question is None and qtype == QT_NAME_SERV) or \
            (len(question) <= QN_MAX_LEN \
             and qtype == QT_HOST_ADDR \
             and qclass == QC_INET_ADDR):
            # process this question for our project.
            self.valid = True

    '''
    Build the question field of a DNS request
    Return the raw value of a string builder
    Its format should be:
    ---------------------
    |                   |
    /       QNAME       /
    /                   /
    ---------------------
    |       QTYPE       |
    ---------------------
    |       QCLASS      |
    ---------------------
    '''
    def build_question(self):
        qname_raw = build_qname(self.question)
        typeclass_buffer = create_string_buffer(QA_TYPE_CLASS_FMT)
        pack_into('!HH', typeclass_buffer, 0, self.qtype, self.qclass)
        question_raw = qname_raw + typeclass_buffer.raw
        return question_raw

    def print_str(self):
        return DNS_PRINT_QFMT % (self.question, self.qtype, self.qclass)

    def __str__(self):
        return self.print_str()

class DNSAnswer:

    '''
    The answer given is already a packed answer after socket.inet_aton(IP).
    The question should be a human-readable host address, e.g 'www.baidu.com'.
    '''
    def __init__(self, answer, question, rtype=QT_HOST_ADDR, \
                 rclass=QC_INET_ADDR, TTL=600):
        self.question = question
        self.answer = answer
        self.rtype = rtype
        self.rclass = rclass
        self.TTL = TTL
        self.rdlength = len(answer)

    '''
    Return the raw binary format of the built answer
    Its format should be:
    ---------------------
    |                   |
    /        NAME       /
    |                   |
    ---------------------
    |        TYPE       |
    ---------------------
    |        CLASS      |
    ---------------------
    |         TTL       |
    |                   |
    ---------------------
    |       RDLENGTH    |
    ---------------------
    /        RDATA      /
    /                   /
    ---------------------
    '''
    def build_answer(self):
        qname = build_qname(self.question)
        remain_buffer = create_string_buffer(calcsize(DNS_ANS_FMT))
        pack_into(DNS_ANS_FMT, remain_buffer, 0, self.rtype, self.rclass, \
                  self.TTL, self.rdlength)
        self.rawanswer = qname + remain_buffer.raw + self.answer
        return self.rawanswer

    def print_str(self):
        print_str = DNS_PRINT_AFMT % (self.question, self.rtype, self.rclass, self.TTL, self.rdlength)
        print_str = print_str + str(self.answer) + '----\n'
        return print_str

    def __str__(self):
        return self.print_str()


class DNSPacket:
    '''
    Ranid: client side will generate this field. When response, DNS server
           is required to set the same value for the client request.
    QR: 0 query, 1 response
    Opcode: 0 standard query
    AA: Authoritative answer, meaningful in response
        1 authoritative, 0 not
    TC: Truncated. 1 truncated. 0 not truncated.
        ** For DNS server if received this field as 1, drop it.
    RD: Recursion Desired. 1 desired, 0 not
    RA: Recursion Available. 1 available, 0 not. Set or cleared in response.
        In our DNS server response, we set it as 1.
    Z:  Reserved for future usage. Set it to 0.
    Rcode:  Response code:
            0: No error condition
            1: Request packet Format error
            2: Server failure
            3: Name error the domain name does not exists
            4: Not support the requested kind of query
            5: Refused.
    QDCOUNT: the number of entries in the question section
    ANCOUNT: the number of resource records in the answer section
    NSCOUNT: (set to 0 and ignore it)
    ARCOUNT: (set to 0 and ignore it)
    The questions should be an array of DNSQuestion objects
    The answers should be an array of DNSAnswer objects
    '''
    def __init__(self, ranid=-1, qr=-1, opcode=0, aa=0, tc=0, rd=0, ra=1, z=0, rcode=0, \
                 nscount=0, arcount=0, questions=[], answers=[]):
        self.ranid = ranid
        self.qr = qr
        self.opcode = opcode
        self.aa = aa
        self.tc = tc
        self.rd = rd
        self.ra = ra
        self.z = z
        self.rcode = rcode
        self.qdcount = len(questions)
        self.ancount = len(answers)
        self.nscount = nscount
        self.arcount = arcount
        self.questions = questions
        self.answers = answers

    def pack(self):
        # Build header
        self.dns_hdr = self._build_header(self.ranid, self.qr, self.opcode, self.aa,
                                          self.tc, self.rd, self.ra, self.z, self.rcode,
                                          self.qdcount, self.ancount, self.nscount, self.arcount)
        self.dns_packet_raw = self.dns_hdr
        # Build questions
        for question in self.questions:
            qraw = question.build_question()
            self.dns_packet_raw += qraw
        if self.qr == 0:
            return self.dns_packet_raw
        # Build answers
        # When building answers, we never use pointer thing in our application
        for ans in self.answers:
            araw = ans.build_answer()
            self.dns_packet_raw += araw
        return self.dns_packet_raw

    '''
    Given the dns_packet in binary format
    Parse its header, questions and answers
    questions will be an array of DNSQuestion objects;
    answers will be an array of DNSAnswer objects.
    '''
    def unpack(self, dns_packet):
        # parse header
        self._parse_header(dns_packet[:DNS_HDR_LEN])
        hlen = DNS_HDR_LEN
        # parse questions
        self.questions, qlen = parse_questions(self.qdcount, dns_packet[hlen:])
        hqlen = hlen + qlen
        # parse answers
        self.answers, alen = parse_answers(self.ancount, dns_packet[hqlen:])

    def _parse_header(self, hdr_part):
        hdr_fields = unpack(DNS_HDR_FMT, hdr_part)
        self.ranid = hdr_fields[0]
        flag_field = hdr_fields[1]
        flags = self._deshift_flags(flag_field)
        self.qr = flags[0]
        self.opcode = flags[1]
        self.aa = flags[2]
        self.tc = flags[3]
        self.rd = flags[4]
        self.ra = flags[5]
        self.z = flags[6]
        self.rcode = flags[7]
        self.qdcount = hdr_fields[2]
        self.ancount = hdr_fields[3]
        self.nscount = hdr_fields[4]
        self.arcount = hdr_fields[5]

    '''
    Given DNS packet header data, build them into binary header.
    Return the raw value of a string builder.
    '''
    def _build_header(self, ranid, qr, opcode, aa, tc, rd, ra, z, rcode, qdcount, \
                      ancount, nscount, arcount):
        flags = self._shift_flags(qr, opcode, aa, tc, rd, ra, z, rcode)
        dns_header_buf = create_string_buffer(calcsize(DNS_HDR_FMT))
        pack_into(DNS_HDR_FMT, dns_header_buf, 0, ranid, flags, qdcount, ancount, nscount, arcount)
        return dns_header_buf.raw

    '''
    Given DNS header flags
    Parse them into an unsigned short integer.
    '''
    def _shift_flags(self, qr, opcode, aa, tc, rd, ra, z, rcode):
        return rcode + (z << 4) + (ra << 7) + (rd << 8) + (tc << 9) + (aa << 10)\
            + (opcode << 11) + (qr << 15)

    '''
    Given an unsigned short integer
    Parse it to a tuple of DNS header flags.
    '''
    def _deshift_flags(self, flags):
        qr = (flags >> 15) & 0x01
        opcode = (flags >> 11) & 0x0F
        aa = (flags >> 10) & 0x01
        tc = (flags >> 9) & 0x01
        rd = (flags >> 8) & 0x01
        ra = (flags >> 7) & 0x01
        z = (flags >> 4) & 0x07
        rcode = flags & 0x0F
        return (qr, opcode, aa, tc, rd, ra, z, rcode)

    def __str__(self):
        print_str = DNS_PRINT_HFMT % (self.ranid, self.qr, self.opcode, self.aa, \
                                 self.tc, self.rd, self.ra, self.z, self.rcode, \
                                 self.qdcount, self.ancount, self.nscount, \
                                 self.arcount)
        if self.questions and len(self.questions) > 0:
            print_str += self.questions[0].print_str()
        if self.answers and len(self.answers) > 0:
            print_str += self.answers[0].print_str()
        print_str += '----- Over -----\n'
        return print_str
'''
Given a DNS question, return its raw binary packed data value.
** NOTE: if the question is None. Just return 0x00 which is the end
         tag of QNAME field
Example: given 'www.neu.edu', generate '....'(no idea binary data)
'''
def build_qname(question):
    if question is None:
        qname_buffer = create_string_buffer(1)
        pack_into('!B', qname_buffer, 0, 0x00)
        return qname_buffer.raw
    labels = question.split('.')
    bufsize = 0
    for label in labels:
        bufsize += 1
        bufsize += len(label)
    bufsize += 1
    qname_buffer = create_string_buffer(bufsize)
    offset = 0
    for label in labels:
        pack_into('!B', qname_buffer, offset, len(label))
        offset += 1
        pack_into('!%ds' % (len(label)), qname_buffer, offset, label)
        offset += len(label)
    pack_into('!B', qname_buffer, offset, 0x00)  # end with 0x00
    return qname_buffer.raw

'''
Given a sequence of binary raw data, which the first byte of if is 100% sure
to the first byte of a question name. Parse it and get question from it.
Return question and the length of this question name part in original data.
*** If there is just a 0x00 which is the end tag of QNAME field, then we just
    return (None, 1), which means the QNAME is empty.
'''
def parse_qname(rawdata):
    labels = []
    start = 0
    end = 1
    # TODO potential bug might be here. Update it.
    while 1:
        lbllen = unpack('!B', rawdata[start])[0]
        if lbllen == 0x00:
            break;
        start = end
        end += lbllen
        label = unpack('!%ds' % (lbllen), rawdata[start : end])[0]
        labels.append(label)
        start = end
        end += 1
    question = ''
    if len(labels) == 0:
        return None, end
    # Build up question e.g 'www.neu.edu'
    for label in labels:
        question += label
        question += '.'
    question = question[:len(question) - 1]
    return question, end

'''
Given the number questions in the data field, and the data
Return an array list of DNSQuestion objects
'''
def parse_questions(qdcount, data):
    qoffset = 0
    questions = []
    for i in range(0, qdcount):
        rawquestion = data[qoffset:]
        qname, end = parse_qname(rawquestion)
        start = end
        end += 4
        typeClass = unpack('!HH', rawquestion[start:end])
        qtype = typeClass[0]
        qclass = typeClass[1]
        question = DNSQuestion(qname, qtype, qclass)
        questions.append(question)
        qoffset += end
    return questions, qoffset

'''
Given a sequence of binary raw data start from which is definitely the header
of a DNS answer. Find all the of the DNS answers from the start of this data
and build them into DNSAnswer objects.
Return DNSAnswer objects and
       the last byte offset from the start of the data.
'''
def parse_answers(ancount, data):
    aoffset = 0
    answers = []
    for i in range(0, ancount):
        rawanswer = data[aoffset:]
        qname, end = parse_qname(rawanswer)
        start = end
        # next ten bytes are: type(2), class(2), TTL(4), RDLength(2)
        end += calcsize(DNS_ANS_FMT)
        (rtype, rclass, TTL, rdlen) = unpack(DNS_ANS_FMT, rawanswer[start: end])
        start = end
        end += rdlen
        rdata = rawanswer[start : end]
        answer = DNSAnswer(rdata, qname, rtype, rclass, TTL)
        answers.append(answer)
        aoffset += end
    return answers, aoffset

'''
Given the first two byte of a DNS Answer binary raw data.
Check if it is a pointer which points to the QNAME part
of a DNS Question field.
TODO right now, our DNS server doesn't support pointer thing
Thus our DNS client don't need to bother to figure it out.
'''
def _isAnswerNamePointer(first2Byte):
    value = unpack('!H', first2Byte)[0]
    if (value >> 14) == 3:
        return True
    else:
        return False

def test():
    pass

if __name__ == '__main__':
    test()
