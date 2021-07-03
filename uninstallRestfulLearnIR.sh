#!/bin/bash +x

UMASK=022

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source $SCRIPT_DIR/RestfulLearnIR.conf

if [ -z "$rlir_user" ]; then
	echo "error: rlir_user is not set. exiting..."
	exit 1
fi

if [ -z "$rlir_group" ]; then
	echo "error: rlir_group is not set. exiting..."
	exit 1
fi

systemctl stop restfullearnir
systemctl disable restfullearnir

grep "$rlir_user" /etc/passwd > /dev/null 2>&1
if [ "$?" -eq "0" ]; then
	userdel -f "$rlir_user"
fi

groupdel -f "$rlir_group"

rm -f /usr/bin/RestfulLearnIR.py

rm -f /lib/systemd/system/restfullearnir.service

rm -rf /etc/default/RestfulLearnIR
