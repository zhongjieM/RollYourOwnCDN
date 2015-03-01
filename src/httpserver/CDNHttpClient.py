'''
Created on Apr 7, 2014

'''
import httplib


def main():
    httpConn = httplib.HTTPConnection('ec2-54-85-79-138.compute-1.amazonaws.com', 8080, 100)
    httpConn.request('GET', 'http://ec2-54-85-79-138.compute-1.amazonaws.com:8080/wiki/Main_Pag')
    response = httpConn.getresponse()
    print response.msg
    print response.read()
    response.get
    print response.status


if __name__ == '__main__':
    main()
