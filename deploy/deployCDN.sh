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

# directory constants
PWD=`pwd`
CD=`basename $PWD`
DIR=`test "$CD" = "deploy" && echo .. || echo .`
SRC_DIR=src
GEOIPDB_DIR=db_geoip
DNS_PFX=dnsserver
GEOIP_PFX=geoiptool
HTTP_PFX=httpserver
TARGET_PFX=cdn-enzen
VERSION=`date +"%Y%m%d%H%M"`
TARGET_DIR=$TARGET_PFX-$VERSION
DNS_TARGET=$DNS_PFX-$VERSION
HTTP_TARGET=$HTTP_PFX-$VERSION

# Command line arguments
DNSUSERNAME=""
EC2USERNAME=""
KEYFILEPATH=""

# usage function
function usage() {
    cat<<HELP
DESCRIPTION: A script for deploying CDN.
USAGE: ./deployCDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile> [ -du <dnsusename> ]
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
    echo "Version: $VERSION"
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

# Deploy DNS server
echo "Deploying DNS server to $DNSHOST, Location: CCIS"
ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST "rm -rf ~/$TARGET_PFX-*; mkdir $TARGET_DIR"
# copy dns sources
scp -i $KEYFILEPATH -r $DIR/$SRC_DIR/$DNS_PFX $DNSUSERNAME@$DNSHOST:$TARGET_DIR/$DNS_TARGET
# copy geoip sources
scp -i $KEYFILEPATH -r $DIR/$SRC_DIR/$GEOIP_PFX $DNSUSERNAME@$DNSHOST:$TARGET_DIR/$GEOIP_PFX
# download geoip db
ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST \
    "cd $TARGET_DIR; wget -q https://www.yingquanyuan.com/static/fcn/$GEOIPDB_DIR.zip; unzip $GEOIPDB_DIR.zip; rm $GEOIPDB_DIR.zip"
# split geoip db
ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST \
    "python ~/$TARGET_DIR/$GEOIP_PFX/geoip_splitter.py -s ~/$TARGET_DIR/$GEOIPDB_DIR -d ~/$TARGET_DIR"
# linking
ssh -i $KEYFILEPATH $DNSUSERNAME@$DNSHOST \
    "ln -sf ~/$TARGET_DIR/$DNS_TARGET/$DNS_PFX.py ~/$TARGET_DIR/$DNS_PFX"
echo ''

# Deploy HTTP servers
for host in ${HTTPHOSTS[@]};
do
    hostinfo=`grep $host $DIR/deploy/ec2-hosts.txt`
    echo "Deploying HTTP replica server to $hostinfo"
    ssh -i $KEYFILEPATH $EC2USERNAME@$host "rm -rf ~/$TARGET_PFX-*; mkdir $TARGET_DIR"
    scp -i $KEYFILEPATH -r $DIR/$SRC_DIR/$HTTP_PFX $EC2USERNAME@$host:$TARGET_DIR/$HTTP_TARGET
    ssh -i $KEYFILEPATH $EC2USERNAME@$host \
        "ln -sf ~/$TARGET_DIR/$HTTP_TARGET/$HTTP_PFX.py ~/$TARGET_DIR/$HTTP_PFX"
    echo ''
done
