#컴퓨터네트워크 HW#3
#TCP 기반 소켓 프로그래밍 작성 후 GO-BACK-N 동작 구현하기
#소프트웨어학부 20181702 최혁태

#파일은 총 3개입니다.
#패킷을 보내는 GBN_sender.py 파일과, 패킷을 받는 GBN_receiver.py 파일과, sender에서 receiver로 보내는 test.txt 파일이 있습니다.
#GBN_receiver.py, 즉 현재 파일은 제 컴퓨터(로컬환경)에서 실행됩니다.
#GBN_sender.py 파일은 AWS EC2 instance를 활용한 Ubuntu 18.04 클라우드 환경에서 실행됩니다.


#프로그램 동작에 필요한 모듈을 import 합니다.
import socket
import time
import os
import hashlib
import random


#AWS EC2 instance의 public ip로 설정해줍니다.
host = "13.209.3.116"
#11000번 포트를 통해 연결합니다.
port = 11000


#checksum을 계산하는 함수입니다.
def check_sum(data):
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()


#Receiver 클래입니다.
class Receiver:

    # 초기 변수들을 선언하고, 초기화해줍니다.
    def __init__(self,win_size, timeout, filename):
        self.w = win_size    #window size를 담는 변수입니다.
        self.completeData = ''
        self.t = timeout     #timeout을 담는 변수입니다.
        self.rec_file = ''
        self.base = 0   #패킷의 첫번째(base 패킷)를 담는 변수입니다.
        self.expec_seqnum = 0   #receiver가 sender에게 받을 것으로 예상하고 있는 패킷의 번호를 담는 변수입니다.
        self.last_ack_sent = -1 #마지막으로 ack를 보냈던 패킷의 번호를 담는 변수입니다.
        self.soc = socket.socket()
        self.window = [None] * self.w
        self.active_win_packets = self.w
        self.fileclone = filename
        self.logfile = ''
        self.filepointer = 0


    # 패킷이 send window에 추가될 수 있는지 체크합니다.
    def canAdd(self):
        if self.active_win_packets == 0:
            return False
        else:
            return True


    #Response Message를 만드는 함수입니다.
    def createResponse(self, seq_num, typ):
        mess_check_sum = check_sum(str(seq_num))
        return str(mess_check_sum) + "/////" + str(seq_num) + "/////" + typ



    #ACK를 보내는 함수입니다.
    def sendAcks(self, packet, counter):

        #counter가 -1인 경우 NAK를 보냅니다.
        if counter == -1:
            #로그파일에 시간과, 받은 패킷을 기록합니다.
            self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving\n")
            time.sleep(1.7)
            #소켓을 통해 NAK를 보내줍니다.
            self.soc.send(packet)
            print "Sending ack: ", str(packet.split('/////')[1]) + "NAK\n"
            return

        #counter가 -1이 아닌 경우 ACK를 보냅니다.
        self.last_ack_sent = int(packet.split("/////")[1]) + counter
        time.sleep(1.7)
        self.soc.send(packet)
        self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving\n")
        print "Sending ack: ", str(packet.split('/////')[1]) + "ACK\n"




    #remove함수는 아래 아래 appData에서 사용되는 함수입니다.
    #window에서 [filepointer-1] 인덱스 위치에 있는 값을 None으로 바꿔주는, 즉 값을 제거해주는 함수입니다.
    def remove(self, point):
        self.window[self.window.index(point)] = None
        self.active_win_packets += 1




    def add(self, packet):

        #패킷을 분리한 내용중 세번째 인덱스를 pack에, 첫번째 인덱스를 seqnum에 넣어줍니다.
        pack = packet.split('/////')[3]
        seqnum = int(packet.split('/////')[1])


        #seqnum을 window size로 나눈 나머지를 계산해서 window에서 인덱스로 사용합니다.
        #그 인덱스에 값이 아무것도 없는 경우
        if self.window[seqnum % self.w] == None:

            #seqnum이 receiver가 예상한 값인 경우
            if seqnum == self.expec_seqnum:
                #logfile을 작성하고, window size만큼의 active_win_packets를 1 감소시킵니다.
                self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieve\n")
                self.active_win_packets -= 1
                self.window[seqnum % self.w] = packet

            #seqnum이 receiver가 예상한 값보다 큰 경우
            elif seqnum > self.expec_seqnum:
                #logfile을 작성하고, window size만큼의 active_win_packets를 1 감소시킵니다.
                self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving buffer\n")
                self.active_win_packets -= 1
                self.window[seqnum % self.w] = packet

        #그 인덱스에 값이 아무것도 없지 않은 경우
        else:
            print "In buffer: ", packet.split('/////')[1]   #그 값을 출력합니다.


    #window에서 remove하고 싶은 부분 골라냅니다.
    #초기 filepointer는 0으로 설정되어있습니다.
    def appData(self):
        self.completeData += self.window[self.filepointer].split('/////')[3]
        self.filepointer += 1
        self.remove(self.window[self.filepointer - 1])
        if self.filepointer >= self.w:
            self.filepointer = 0


    #
    def rMessage(self):
        while True:
            pack = self.soc.recv(1024)  #pack 변수에는 소켓을 통해 받은 정보가 들어갑니다.
            count = 0
            print (pack.split('/////')) #pack에 들어간 내용을 '/////'을 기준으로 나눠줍니다.
            if pack == '$$$$$$$':       #pack에 '$$$$$$$'가 들어가있는 경우

                #파일을 열고 씁니다.
                f = open(self.fileclone, 'wb')
                f.write(self.completeData)
                f.close()
                break

            #pack에 receiver가 받기로 예측한 패킷이 들어가있는 경우
            elif int(pack.split('/////')[1]) == self.expec_seqnum:
                next = 0    #next변수를 0으로 초기화해줍니다.
                if self.canAdd():   #패킷을 window에 추가할 수 있는지 확인합니다.
                    try:
                        k = int(pack.split("/////")[4])     #패킷을 분리하여 k에 넣어줍니다.
                    except:
                        next = 1    #next 변수를 1로 초기화해줍니다.
                    if not next:    #next가 0이 아닌 경우
                        if int(pack.split("/////")[4]) > 70:    #패킷을 분리한 것의 길이가 70이 넘을 경우
                            self.add(pack)  #packet
                            packet = self.createResponse(self.expec_seqnum + count, "ACK")
                            while self.window[(int(pack.split('/////')[1]) + count) % self.w] != None:
                                self.appData()
                                count = count + 1
                        else:
                            packet = self.createResponse(self.expec_seqnum + count, "NAK")
                    else:
                        packet = self.createResponse(self.expec_seqnum + count, "NAK")

                    self.sendAcks(packet, count - 1)     #sender에게 ACK를 보내줍니다.
                    self.expec_seqnum = self.expec_seqnum + count    #receiver가 받기로 예상하고 있던 패킷 번호에 count를 더해줍니다.
            else:
                #패킷이 window에 추가될 수 있는지 확인한 후, 패킷을 추가합니다.
                if self.canAdd():
                    self.add(pack)


    #logfile에 내용을 작성하는 함수입니다.
    def recieve(self):
        self.logfile = open(os.curdir + '/' + "clientlog.txt", 'wb')
        self.rMessage()
        self.logfile.close()


#소켓을 통해 sender와 연결합니다.
s = socket.socket()
s.connect((host, port))


#sender와 연결이 되면 mess 변수에 정보를 받아옵니다.
s.send("Hello Server")
mess = s.recv(1024)
args = mess.split("/////")

#통신이 끝나면 소켓을 닫아줍니다.
s.close()
client = Receiver(int(args[0]), float(args[1]), args[2])
print "recieved arguments"
client.soc.connect((host, port))
client.soc.send("Hello server")
client.recieve()
client.soc.close()
