from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from random import SystemRandom
from urlparse import urlparse, parse_qs
from collections import defaultdict

import json
import re
import os
import socket
import batchtank

DIR = 'batchtank/static' 

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        self.procsoc = procsoc
        BaseHTTPRequestHandler.__init__(self, *args)

    def getData(self):
        bm = batchtank.BaseMessage()
        bm.getSensor.append(batchtank.TEMP)
        bm.getOutput.append(batchtank.COOLER)
        bm.getSensor.append(batchtank.LEVEL)
        bm.getOutput.append(batchtank.IN_PUMP_RATE)
        bm.getOutput.append(batchtank.OUT_PUMP_RATE)

        bm.SerializeToSocket(self.procsoc)

        bm = batchtank.BaseMessage()
        bm.ParseFromSocket(self.procsoc)

        data = {"Temperature" : defaultdict(list),
                "WaterLevel" : defaultdict(list)}

        for s in bm.sample:
            if s.type == batchtank.TEMP:
                data["Temperature"]["temp"].append(s.value)
            elif s.type == batchtank.LEVEL:
                data["WaterLevel"]["level"].append(s.value)

        for s in bm.signal:
            if s.type == batchtank.COOLER:
                data["Temperature"]["u"].append(s.value)
                data["Temperature"]["ref"].append(s.ref)
            elif s.type == batchtank.IN_PUMP_RATE:
                data["WaterLevel"]["in u"].append(s.value)
                data["WaterLevel"]["in ref"].append(s.ref)
            elif s.type == batchtank.OUT_PUMP_RATE:
                data["WaterLevel"]["out u"].append(s.value)
                data["WaterLevel"]["out ref"].append(s.ref)

        return data


    def do_GET(self):
        try:
            if (self.path == '/jquery.js' or self.path == '/jquery.flot.js'):
                f = open(DIR + self.path)

                self.send_response(200)
                self.send_header('Content-type', 'text/javascript')
                self.end_headers()

                self.wfile.write(f.read())
                f.close()
            elif (self.path.startswith('/data')):
                self.send_response(200)
                self.send_header('Cache-Control', 'no-cache, must-revalidate')
                self.send_header('Content-type', 'application/json;charset=utf-8')
                self.end_headers()

                out = json.dumps(self.getData())

                #print out

                self.wfile.write(out)
            elif (self.path == '/' or self.path == '/index.html' or self.path == '/index.htm'):
                # Serve index!
                f = open(DIR + '/index.htm')

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                self.wfile.write(f.read())
                f.close()
            else:
                self.send_error(404, 'Aeh naee... Di blidde 404: ' + self.path)
        except IOError:
            raise
            self.send_error(404, 'Aeh naee... Di blidde 404.')

def main():
    try:
        global procsoc
        procsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Connect with server running.
        procsoc.connect(("localhost", 54000))

        server = HTTPServer(('', 8080), RequestHandler)
        print 'Server running...'
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Stopping server!'
        server.socket.close()

if __name__ == '__main__':
    main()
