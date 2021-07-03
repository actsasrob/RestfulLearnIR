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

groupadd -f "$rlir_group"

grep "$rlir_user" /etc/passwd > /dev/null 2>&1
if [ "$?" -ne "0" ]; then
	useradd -c "RestfulLearnIR User" --system --gid "$rlir_group" -s "/bin/bash" "$rlir_user"
fi

cp -f $SCRIPT_DIR/RestfulLearnIR.py /usr/bin/
chmod 755 /usr/bin/RestfulLearnIR.py

cp -f $SCRIPT_DIR/restfullearnir.service /lib/systemd/system/
chmod 644 /lib/systemd/system/restfullearnir.service

mkdir -p /etc/default/RestfulLearnIR

USETLS=""
if [ "$rlir_useTLS" == "true" ]; then
   USETLS="--useTLS --cert $rlir_cert_path --key $rlir_key_path"
fi

startcommand="ExecStart=/usr/bin/RestfulLearnIR.py --userID=$rlir_user --groupID=$rlir_group --port=$rlir_port --device=$rlir_learnIRDevice $USETLS"

sed -i "s|^ExecStart.*$|$startcommand|" /lib/systemd/system/restfullearnir.service

systemctl daemon-reload
