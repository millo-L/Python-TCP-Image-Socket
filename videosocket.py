import socket
import cv2
import numpy
import time
import base64
import sys
from datetime import datetime

class ClientSocket:
    def __init__(self, ip, port, video_path):
        self.TCP_SERVER_IP = ip
        self.TCP_SERVER_PORT = port
        self.video_path = video_path
        self.connectCount = 0
        self.connectServer()

    def connectServer(self):
        try:
            self.sock = socket.socket()
            self.sock.connect((self.TCP_SERVER_IP, self.TCP_SERVER_PORT))
            print(u'Client socket is connected with Server socket [ TCP_SERVER_IP: ' + self.TCP_SERVER_IP + ', TCP_SERVER_PORT: ' + str(self.TCP_SERVER_PORT) + ' ]')
            self.connectCount = 0
            self.sendImages()
        except Exception as e:
            print(e)
            self.connectCount += 1
            if self.connectCount == 10:
                print(u'Connect fail %d times. exit program'%(self.connectCount))
                sys.exit()
            print(u'%d times try to connect with server'%(self.connectCount))
            self.connectServer()

    def sendImages(self):
        cnt = 0
        capture = cv2.VideoCapture(self.video_path)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 315)
        try:
            while capture.isOpened():
                    ret, fra = capture.read()
                    frame = cv2.resize(fra, dsize=(480, 315), interpolation=cv2.INTER_AREA)

                    now = time.localtime()
                    stime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
                    result, imgencode = cv2.imencode('.jpg', frame, encode_param)
                    data = numpy.array(imgencode)
                    stringData = base64.b64encode(data)
                    length = str(len(stringData))
                    self.sock.sendall(length.encode('utf-8').ljust(64))
                    self.sock.send(stringData)
                    self.sock.send(stime.encode('utf-8').ljust(64))
                    print(u'send images %d'%(cnt))
                    cnt+=1
                    time.sleep(0.095)
        except Exception as e:
            print(e)
        self.sendImages()

def main():
    TCP_IP = 'localhost' 
    #TCP_IP = 'bic4907.diskstation.me' 
    #TCP_PORT = 8080 
    TCP_PORT = 4444
    video_path = './project(15h54m37s).mp4'
    client = ClientSocket(TCP_IP, TCP_PORT, video_path)

if __name__ == "__main__":
    main()