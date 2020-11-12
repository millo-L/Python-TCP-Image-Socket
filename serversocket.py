import os
import socket
import cv2
import numpy
import base64
import glob
import sys
import time
import threading
from datetime import datetime
import pymysql

class ServerSocket:

    def __init__(self, ip, port):
        self.TCP_IP = ip
        self.TCP_PORT = port
        self.createImageDir()
        self.folder_num = 0
        self.cursor = self.dbConnect()
        self.socketOpen()
        self.receiveThread = threading.Thread(target=self.receiveImages)
        self.receiveThread.start()

    def socketClose(self):
        self.dbClose()
        self.sock.close()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is close')

    def socketOpen(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.TCP_IP, self.TCP_PORT))
        self.sock.listen(1)
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is open')
        self.conn, self.addr = self.sock.accept()
        print(u'Server socket [ TCP_IP: ' + self.TCP_IP + ', TCP_PORT: ' + str(self.TCP_PORT) + ' ] is connected with client')

    def receiveImages(self):
        cnt_str = ''
        cnt = 0

        try:
            while True:
                if (cnt < 10):
                    cnt_str = '000' + str(cnt)
                elif (cnt < 100):
                    cnt_str = '00' + str(cnt)
                elif (cnt < 1000):
                    cnt_str = '0' + str(cnt)
                else:
                    cnt_str = str(cnt)
                if cnt == 0: startTime = time.localtime()
                cnt += 1
                length = self.recvall(self.conn, 64)
                length1 = length.decode('utf-8')
                stringData = self.recvall(self.conn, int(length1))
                stime = self.recvall(self.conn, 64)
                print('send time: ' + stime.decode('utf-8'))
                now = time.localtime()
                print('receive time: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))
                data = numpy.frombuffer(base64.b64decode(stringData), numpy.uint8)
                decimg = cv2.imdecode(data, 1)
                cv2.imshow("image", decimg)
                cv2.imwrite('./' + str(self.TCP_PORT) + '_images' + str(self.folder_num) + '/img' + cnt_str + '.jpg', decimg)
                cv2.waitKey(1)
                if (cnt == 60 * 10):
                    cnt = 0
                    convertThread = threading.Thread(target=self.convertImage(str(self.folder_num), 6000, startTime))
                    convertThread.start()
                    self.folder_num = (self.folder_num + 1) % 2
        except Exception as e:
            print(e)
            self.convertImage(str(self.folder_num), cnt, startTime)
            self.socketClose()

    def createImageDir(self):
        folder_name = str(self.TCP_PORT) + "_images0"
        try:
            if not os.path.exists(folder_name):
                os.makedirs(os.path.join(folder_name))
        except OSError as e:
            if e.errno != errno.EEXIST:
                print("Failed to create " + folder_name +  " directory")
                raise
        folder_name = str(self.TCP_PORT) + "_images1"
        try:
            if not os.path.exists(folder_name):
                os.makedirs(os.path.join(folder_name))
        except OSError as e:
            if e.errno != errno.EEXIST:
                print("Failed to create " + folder_name + " directory")
                raise

        try:
            if not os.path.exists("../videos"):
                os.makedirs(os.path.join("../videos"))
        except OSError as e:
            if e.errno != errno.EEXIST:
                print("Failed to create ../videos directory")
                raise
        
    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf    

    def convertImage(self, fnum, count, now):
        img_array = []
        cnt = 0
        for filename in glob.glob('./' + str(self.TCP_PORT) + '_images' + fnum + '/*.jpg'):
            if (cnt == count):
                break
            cnt = cnt + 1
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)
        
        file_date = self.getDate(now)
        file_time = self.getTime(now)
        name = 'project(' + file_time + ').mp4'
        file_path = '../server/public/videos/' + name
        out = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*'.mp4'), 10, size)

        for i in range(len(img_array)):
            out.write(img_array[i])
        out.release()
        self.insertDB(name, file_date)
        print(u'complete')

    def dbConnect(self):
        DBUSER = 'capston'
        DBPW = 'ya5O3o3IB1X1ToMA1uVo4Eq4Giy51E'
        HOST = 'test.inchang.dev'
        DB = 'capston'

        self.video_db = pymysql.connect(
            user = DBUSER,
            passwd = DBPW,
            host = HOST,
            db = DB,
            charset = 'utf8'
        )
        print(u'VideoDB is connected')
        cursor = self.video_db.cursor()
        return cursor

    def dbClose(self):
        self.cursor.close()
        self.video_db.close()
        print(u'VideoDB is closed')

    def insertDB(self, file_name, file_date):
        file_path = './videos/' + file_name
        print(file_path)
        sql = """insert into video (name, date, frame, path) values ("%s", "%s", "%d", "%s")""" % (file_name, file_date, 10, file_path)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            print(e)
        finally:
            self.video_db.commit()

    def getDate(self, now):
        year = str(now.tm_year)
        month = str(now.tm_mon)
        day = str(now.tm_mday)

        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        return (year + '-' + month + '-' + day)

    def getTime(self, now):
        file_time = (str(now.tm_hour) + 'h' + str(now.tm_min) + 'm' + str(now.tm_sec) + 's')
        return file_time

def main():
    server = ServerSocket('localhost', 8080)

if __name__ == "__main__":
    main()