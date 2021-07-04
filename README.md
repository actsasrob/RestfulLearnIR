# RestfulLearnIR

RestfulLearnIR is a python program that provides an HTTP REST interface for using the wonderful LearnIR device to capture/replay Infrared (IR) signals.

If you've arrived at this page and don't known what LearnIR is then please checkout [the LearnIR product page](https://www.analysir.com/blog/product/learnir-advanced-infrared-learner-module/).

At the current time python3 is required to use RestfulLearnIR.

To see a list of arguments run './RestfulLearnIR.py -h'.

For the best results you should have a LearnIR USB dongle plugged into a USB port on the server before running RestfulLearnIR.py. RestfulLearnIR will attempt to connect to the USB serial device for LearnIR when the program starts.

Before plugging in the LearnIR USB dongle you may want to run the following command to determine the device name for other USB devices plugged into the server:

```
ls /dev/ttyUSB*
```

Plug in the LearnIR USB dongle and run the above command again and look for a new USB device. NOTE: On a Raspberry Pi 4 the LearnIR will have a device name starting with /dev/ttyUSB. For other OSes the device name may differ.

RestfulLearnIR will attempt to connect to the LearnIR device at /dev/ttyUSB0 by default. You can use the --device argument to specify an alternate device name.

By passing arguments to RestfulLearnIR you can change the port the RestfulLearnIR web server binds to, whether to enable TLS, specify cert/key files to use with TLS, and specify the user/group the process runs as. To bind to ports below 1024 you sill need to start RestfulLearnIR as root. In that case it will start as root, bind the configured port, and then change its effective user/group to the configured user/group.

By default TLS is not enabled, but can be enabled with argument --useTLS.
When TLS is enabled you must provide a cert/key file. The default cert location is /etc/default/RestfulLearnIR/cert.pem. This can be changed with the --cert argument. The default key location is /etc/default/RestfulLearnIR/key.pem. This can be changed with the --key argument.
The default port is 8080 but can be changed with argument --port.
The default user/group is rlir/rlir and can be changed with the --userID/--groupID arguments.

## restfullearnir systemd service

RestfulLearnIR.py can be installed as a systemd service with name restfullearnir.service.

To install the systemd service:
* clone this git repo
* cd to the top-level RestfulLearnIR directory
* Edit the RestfulLearnIR.conf file to set desired values. The variables in the conf file should be intuitive after reading the information above.
* Execute the install script as: sudo ./installRestfulLearnIR.sh
* If you enable TLS then copy the cert/key file to the location specified in the conf file.
* Enable the restfullearnir service using: sudo systemctl enable restfullearnir
* Start the restfullearnir service using: sudo systemctl start restfullearnir
* Check the systemd service status using: sudo systemctl status restfullearnir
* View program output using: sudo journalctl -u restfullearnir -f

You can change values in the conf file and re-run the install script as needed. However when changing the user/group setting you will want to run the uninstall script before making changes to remove the old user/group. After that, update the user/group information in the conf file and run the install script again.

To uninstall the systemd service:
* cd to the top-level RestfulLearnIR directory
* Execute the uninstall script: sudo ./uninstallRestfulLearnIR.sh 


## Capturing/Replaying IR Signals

Now the fun part...once RestfulLearnIR is running and connected to a LearnIR device you can use restful HTTP/HTTPS requests to capture/replay IR signals by communicating wth RestfulLearnIR over the network.

Restful HTTP/HTTPS calls typically lower the barrier to entry for using a REST enabled service. Almost all modern programming language allow you to somewhat easily generate HTTP GET/POST requests. The examples below will using the curl command.

To capture an IR signal use an HTTP GET request. The samples below assume RestfulLearnIR is running on a server with IP 192.168.1.10 and listening on port 8443 with TLS enabled. Execute the curl command below then within 1-2 seconds point a remote control at the LearnIR dongle and press a button.

```
curl -k https://192.168.1.10:8443/
<html><head><title>RestfulLearnIR</title></head><body>28 010A 031A 00F6 074A 00F4 B200 00F4 A9B8 01 F0 7F 14 00 20 10 00 F1 4F 04 11 30 1F 07 F1 40 00</body></html>
```

The HTML output above is the response from RestfulLearnIR with the IR signal captured in LearnIR format.

If RestfulLearnIR doesn't detect an IR signal it will respond as follows:
```
curl -k https://192.168.1.10:8443/
<html><head><title>RestfulLearnIR</title></head><body>error</body></html>
```

To send an IR signal copy the text between the \<body>...\</body> tags and send it as follows:

```
echo '28 010A 031A 00F6 074A 00F4 B200 00F4 A9B8 01 F0 7F 14 00 20 10 00 F1 4F 04 11 30 1F 07 F1 40 00' | curl -k --data-binary @- https://192.168.1.10:8443/
```

RestfulLearnIR alternates between checking for available output from the LearnIR device on the serial port, incoming GET requests, and incoming POST requests. RestfulLearnIR prioritizes handling GET requests over POST requests. 

### GET Request Handling
Handling for GET requests is synchronous. Once RestfulLearnIR starts to handle a GET request it will wait short amount of time for an IR signal to become available on the serial port for the LearnIR device. If an IR signal is received it is returned via HTML as detailed above. If no IR signal is received in the receive window then processing times out and an HTML payload is returned indicating an error occurred.
 
### POST Request Handling
Post requests are not handled synchronously and may not be sent to the LearnIR serial device immediately. The IR signal sent in the HTML payload is queued. The IR signal will be written to the LearnIR serial device during the next available send window. Since POST requests are not handled synchronously there is no HTML payload returned for POST requests.
