#!/bin/bash

# hosts contants
DNSHOST=cs5700cdnproject.ccs.neu.edu
HTTPHOSTS=(ec2-54-84-248-26.compute-1.amazonaws.com
           ec2-54-186-185-27.us-west-2.compute.amazonaws.com
           ec2-54-215-216-108.us-west-1.compute.amazonaws.com
           ec2-54-72-143-213.eu-west-1.compute.amazonaws.com
           ec2-54-255-143-38.ap-southeast-1.compute.amazonaws.com
           ec2-54-199-204-174.ap-northeast-1.compute.amazonaws.com
           ec2-54-206-102-208.ap-southeast-2.compute.amazonaws.com
           ec2-54-207-73-134.sa-east-1.compute.amazonaws.com)

# Command line arguments
DNSUSERNAME=""
EC2USERNAME=""
KEYFILEPATH=""

# usage function
function usage() {
    cat<<HELP
DESCRIPTION: A script for stopping the CDN.
USAGE: ./runCDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile> [ -du <dnsusename> ]
HELP
exit 0
}

# command line arguments checking function
function check_args() {
    # check required arguments
    if [ ! "$EC2USERNAME" ] || [ ! "$KEYFILEPATH" ]; then
        usage
    fi

    # check optional arguments
    if [ ! "$DNSUSERNAME" ]; then
        DNSUSERNAME=$EC2USERNAME
    fi
}

# debugging function
function verbose_print() {
    echo "username: $EC2USERNAME, dnsusername: $DNSUSERNAME, identity: $KEYFILEPATH"
}

# parse command line arguments
while [ $# -gt 0 ]
do
    case $1 in
        --origin | -o)
            shift;;
        --name | -n)
            shift;;
        --port | -p)
            shift;;
        --username | -u)
            shift; EC2USERNAME=$1;;
        --dnsusername | -du)
            shift; DNSUSERNAME=$1;;
        --identity | -i)
            shift; KEYFILEPATH=$1;;
        *)
            usage;;
    esac
    shift
done

# check command line arguments
check_args
# verbose_print

# kick off the DNS server
echo "Killing the DNS server, Location: CCIS"
pid=`ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST "ps aux | grep $DNSUSERNAME.*dnsserver | grep -v grep" | awk '{ print $2 }' | head -1`
ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST "kill -9 $pid && ps aux | grep $DNSUSERNAME.*dnsserver"
echo ''

# kick off each HTTP server
for host in ${HTTPHOSTS[@]};
do
    echo "Killing the HTTP server $host"
    pid=`ssh -i $KEYFILEPATH $EC2USERNAME@$host "ps aux | grep $EC2USERNAME.*httpserver | grep -v grep" | awk '{ print $2 }' | head -1`
    ssh -i $KEYFILEPATH $EC2USERNAME@$host "kill -9 $pid && ps aux | grep $EC2USERNAME.*httpserver"
    echo ''
done
