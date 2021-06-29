#!/usr/bin/env python3
"""
Restful web server for sending and receiving IR signals from LearnIR USB device.
Usage::
    ./RestfulLearnIR.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import queue
import serial
import ssl
import threading
import time

LIR_CMD_SIZE = 10

KeepRunning = True

ReceivedIRSignal = ""
WaitingForIRSignal = False # True - waiting, False - not waiting

#SendIRSignal = ""

SendIRSignalQueue = queue.LifoQueue()
WaitingToSend = False # False - not waiting, True - waiting

global ser
#ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
#ser.flush()

ReceiveLock = threading.Lock()

def sendLIR(command):
    tmpList = list(command[0:(LIR_CMD_SIZE - 1)])
    theLength = len(tmpList)
    if theLength < LIR_CMD_SIZE - 1:
        for x in range(theLength, LIR_CMD_SIZE - 1):
            tmpList.append('_')
    checksum = ord(tmpList[0]) 
    logging.debug("sendLIR: DEBUG: checksum=" + "ord(" + str(tmpList[0]) + ")=" + str(checksum))
    for x in range(1, LIR_CMD_SIZE - 1):
        checksum1 = checksum ^ ord(tmpList[x])
        logging.debug("sendLIR: DEBUG: " + str(checksum) + " xor " + str(tmpList[x]) + "=" + str(checksum1))
        checksum = checksum1
    tmpList.append(chr(checksum))
    tmpStr1=""
    tmpStr=tmpStr1.join(tmpList)
    ser.write(tmpStr.encode())
    logging.debug("sendLIR: DEBUG command=" + tmpStr + " checksum=" + str(checksum) + " chr(" + str(checksum) + ")=" + str(chr(checksum)) +"\n")

class httpServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        '''Get IR Signal via LearnIR and return via HTTP'''
        global ReceivedIRSignal
        global WaitingForIRSignal

        WaitingForIRSignal = True 

        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_headers()
        self.wfile.write(bytes("<html><head><title>RestfulLearnIR</title></head>", "utf-8"))
        #self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        x = 0
        while (x < 5) and (ReceivedIRSignal == ""):
            x+=0.5
            time.sleep(0.5)
        ReceiveLock.acquire()
        if ReceivedIRSignal != "": 
            self.wfile.write(bytes(ReceivedIRSignal, "utf-8"))
        else:
            self.wfile.write(bytes("error", "utf-8"))
        ReceivedIRSignal = ""
        ReceiveLock.release()
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_POST(self):
        '''Add IR signal contained in post request body to queue to be sent via LearnIR during next send window'''
        global SendIRSignalQueue
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), post_data.decode('utf-8'))
        #SendIRSignal = post_data
        SendIRSignalQueue.put(post_data)
        #sendLIR("I")
        self._set_headers()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        #self.wfile.write(bytes("received post request:<br>{}".format(post_data), "utf-8"))
    

    def do_PUT(self):
        self.do_POST()

def run(server_class=HTTPServer, handler_class=httpServer, port=8080):
    global KeepRunning

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket (httpd.socket, 
        keyfile="./key.pem", 
        certfile='./cert.pem', server_side=True)

    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    KeepRunning = False
    httpd.server_close()
    logging.info('Stopping httpd...\n')

### Start: thread to handle LearnIR device I/O
def sendLIRSignal():
    global SendIRSignalQueue
    global ser

    tmpBytes = SendIRSignalQueue.get() + bytes(" FF ", "utf-8")
    ser.write(tmpBytes)
    logging.debug(b"sendLIRSignal: Sent: " + tmpBytes)


class handle_LearnIR_IO_thread (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
       logging.info("handle_LearnIR_IO_thread %s: starting", self.name)
       global KeepRunning
       global ReceivedIRSignal
       global WaitingForIRSignal
       global SendIRSignalQueue
       global WaitingToSend
       global ser

       while KeepRunning:  # Alternate between reading/writing LearnIR serial port
          line = ser.readline().decode('utf-8').rstrip()
          if line != "": # read/print/process anything coming from Serial port
              logging.info("from LearnIR: " + line)
              if line.startswith("LIR: "):
                  if WaitingForIRSignal: # Only keep signal if we were expecting one
                      logging.info("IR signal from LearnIR: " + line)
                      ReceiveLock.acquire()
                      ReceivedIRSignal = line[len("LIR: "):] 
                      WaitingForIRSignal = False 
                      ReceiveLock.release()
              elif line.startswith("I>"):
                  logging.info("LearnIR ready to receive IR signal")
                  WaitingToSend = False
                  sendLIRSignal()
          elif (not SendIRSignalQueue.empty()) and (not WaitingToSend):
              logging.info("Request permission from LearnIR to send IR signal")
              WaitingToSend = True
              sendLIR("I")
          else:
              #logging.debug("sleeping...")
              time.sleep(0.5)

### End: thread to handle LearnIR device I/O

if __name__ == '__main__':
    from sys import argv

    format = "%(asctime)s: RestfulLearnIR: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    thread1 = handle_LearnIR_IO_thread(1, "handle_LearnIR_IO_thread")
    thread1.start()


    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    ser.flush()

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
