#컴퓨터네트워크 HW#3
#TCP 기반 소켓 프로그래밍 작성 후 GO-BACK-N 동작 구현하기
#소프트웨어학부 20181702 최혁태

#파일은 총 3개입니다.
#패킷을 보내는 GBN_sender.py 파일과, 패킷을 받는 GBN_receiver.py 파일과, sender에서 receiver로 보내는 test.txt 파일이 있습니다.
#GBN_sender.py, 즉 현재 파일은 AWS EC2 instance를 활용한 Ubuntu 18.04 클라우드 환경에서 실행됩니다.
#GBN_receiver.py 파일은 제 컴퓨터(로컬환경)에서 실행됩니다.


#프로그램 동작에 필요한 모듈을 import 합니다.
import socket
import time
import os
import hashlib
import random


#AWS EC2 instance의 외부 허용 IP를 0.0.0.0으로 설정해 놓았습니다.
host = "0.0.0.0"
#11000번 포트를 통해 연결합니다.
port = 11000


#checksum을 계산하는 함수입니다.
def check_sum(data):
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()


#Sender 클래스입니다.
class Sender:

    #초기 변수들을 선언하고, 초기화해줍니다.
    def __init__(self, window_size, timeout, num_packets):
        self.w = window_size    #window size를 담는 변수입니다.
        self.t = timeout    #timeout을 담는 변수입니다.
        self.n = num_packets    #패킷의 개수를 담는 변수입니다.
        self.filename = "test.txt"  #sender -> receiver로 보낼 파일 이름을 미리 선언해줍니다.
        self.cur_seq = 0    #현재 패킷의 번호를 담을 변수입니다.
        self.active_spaces = self.w     #Window size만큼의 공간을 만들어놓습니다.
        self.window = window_size * [None]  #window변수를 window size로 초기화합니다.
        self.soc = socket.socket()
        self.last_sent_seqnum = -1  #마지막으로 보낸 패킷의 번호를 담을 변수입니다.
        self.last_ack_seqnum = -1   #마지막으로 ACK를 받은 패킷의 번호를 담을 변수입니다.
        self.logfile = 'servlog.txt'   #log를 기록할 logfile 입니다.


    #패킷이 send window에 추가될 수 있는지 체크합니다.
    def canAdd(self):
        if self.active_spaces == 0:
            return False
        else:
            return True



    #소켓을 통해 패킷을 보내는 함수입니다.
    def sendPack(self, pack):
        time.sleep(1.5)
        conn.send(pack) #패킷을 보냅니다.
        print "Sending Packet Number: ", int(pack.split('/////')[1])    #현재 보낸 패킷의 번호를 출력합니다.
        # logfile에 패킷을 보낸 시간과, 패킷의 번호를 작성합니다.
        self.logfile.write(time.ctime(time.time()) + "\t" + str(pack.split('/////')[1]) + "Sending\n")



    #패킷을 send window에 추가합니다.
    def add(self, pack):
        self.last_sent_seqnum = self.cur_seq    #마지막으로 보낸 패킷의 번호를 현재 패킷번호(0)으로 초기화해줍니다.
        self.cur_seq += 1   #현재 패킷 번호에 1을 더해서 다음 패킷을 가리키게 합니다.
        self.window[self.w - self.active_spaces] = pack
        self.active_spaces -= 1
        self.sendPack(pack) #패킷을 보냅니다.



    #패킷이 손실되면 다시 보내는 함수입니다.
    def resend(self):
        current_num = 0     #현재 패킷 번호를 담는 변수입니다.

        # 현재 패킷번호가 window size - active space보다 작은 경우, 즉 패킷이 안보내진 경우
        while current_num < self.w - self.active_spaces:
            print "Resending: ", str(self.window[current_num].split('/////')[1])    #패킷을 다시 보냅니다.

            #logfile을 작성합니다.
            self.logfile.write(time.ctime(time.time()) + "\t" + str(self.window[current_num].split('/////')[1]) + "Re-sending\n")
            time.sleep(1.4)
            temp = self.window[current_num].split('/////')
            self.window[current_num] = temp[0] + '/////' + temp[1] + '/////' + temp[2] + '/////' + temp[3] + '/////' + str(random.randint(70, 100))
            print self.window[current_num].split('/////')

            conn.send(self.window[current_num])
            current_num += 1



    #패킷을 만드는 함수입니다.
    def makePack(self, num, pac):
        sequence_number = num
        file_check_sum = check_sum(pac)
        pack_size = len(pac)
        prob = random.randint(0, 100)
        packet = str(file_check_sum) + '/////' + str(sequence_number) + \
                 '/////' + str(pack_size) + '/////' + \
                 str(pac) + '/////' + str(prob)
        return packet



    #코드 아래 부분에 [run] 함수에서 사용하는 함수로,
    #txt 파일을 패킷의 개수만큼 나누는 역할을 합니다.
    def divide(self, data, num):
        list = []
        while data:
            list.append(data[:num])
            data = data[num:]
        return list



    #receiver에게 보낸 모든 패킷이 ACK되었는지 확인하는 함수입니다.
    def acc_Acks(self):
        try:
            packet = conn.recv(1024)    #connection을 통해서 받은 값을 packet에 저장합니다.
            print packet.split('/////')  #packet에서 필요한 값들을 뽑아내기 위해 '/////'를 기준으로 분리해줍니다.
        except:
            print 'Connection lost due to timeout!'     #timeout으로 연결이 끊긴 경우 출력해줍니다.
            #logfile에 timeout을 표시해줍니다.
            self.logfile.write(time.ctime(time.time()) + "\t" + str(self.last_ack_seqnum + 1) + "Lost TImeout")
            return 0


        #NAK을 받은 경우
        if packet.split('/////')[2] == "NAK":
            return 0

        #ACK를 받은 패킷 번호를 출력해줍니다.
        print "Recieved Ack number: ", packet.split('/////')[1]
        print "\n"

        #패킷을 쪼개보았을 때 제일 마지막에 보낸 패킷의 번호와 똑같은지 확인합니다.
        if int(packet.split('/////')[1]) == self.last_ack_seqnum + 1:
            self.last_ack_seqnum = int(packet.split('/////')[1])
            self.window.pop(0)  #성공적으로 보낸 패킷을 window에서 제거합니다.
            self.window.append(None)
            self.active_spaces += 1 #한칸 늘려줍니다.
            return 1

        #
        elif int(packet.split('/////')[1]) > self.last_ack_seqnum + 1:
            k = self.last_ack_seqnum
            while (k < int(packet.split('/////')[1])):
                self.window.pop(0)
                self.window.append(None)
                self.active_spaces += 1
                k = k + 1
            self.last_ack_seqnum = int(packet.split('/////')[1])
            return 1

        else:
            return 0




    #모든 패킷이 보내질 때 까지 메시지를 보냅니다.
    def sendmess(self, pack_list, length):
        current_pack = 0    #현재 패킷을 0번이라고 가정합니다.

        #현재 패킷이 length보다 작거나, 마지막으로 ACK를 받은 패킷의 번호가 length-1 보다 작은 경우 while문이 실행됩니다.
        while (current_pack < length or self.last_ack_seqnum != length - 1):

            #
            while self.canAdd() and current_pack != length:
                pack = self.makePack(current_pack, pack_list[current_pack])
                current_pack = current_pack + 1
                print pack.split('/////')
                self.add(pack)
            print "\n"

            if self.acc_Acks() == 0:
                time.sleep(1)
                self.resend()
        print "END"
        time.sleep(1)
        conn.send("$$$$$$$")




    #test.txt 파일을 열어서 안의 내용을 패킷으로 보내는 함수입니다.
    def run(self):
        try:
            fil = open(self.filename, 'rb')     #파일을 엽니다.
            data = fil.read()       #파일을 읽은 내용을 data에 넣어줍니다.
            pack_list = self.divide(data, numpac)    #data를 패킷 개만큼으로 나누어 패킷 리스트를 구성합니다.
            fil.close()     #파일을 닫아줍니다.
        except IOError:     #파일이 존재하지 않는 경우 파일이 없다고 출력해줍니다.
            print "No such file exists"
        fname = "servlog.txt"
        self.logfile = open(os.curdir + "/" + fname, "w+")
        l = len(pack_list)
        self.sendmess(pack_list, l)     #


#window size, 패킷 개수, 타임아웃이 걸리는 초를 입력받습니다.
win = raw_input("Enter window size: ")
numpac = raw_input("Enter the number of packets: ")
tim = raw_input("Enter the timeout: ")


#Sender 클래스를 호출하여 서버에 연결합니다.
server = Sender(int(win), float(tim), int(numpac))
server.soc.bind((host, port))
server.soc.listen(5)
conn, addr = server.soc.accept()


#data를 받아오면 연결이 되었다는 것을 출력해줍니다.
data = conn.recv(1024)
print "recieved connection"


#연결된 상태에서 window size와 time out 시간과 입력 파일을 보내줍니다.
conn.send(str(win) + "/////" + str(tim) + "/////" + "test.txt")

#통신이 끝나면 연결을 끊어줍니다.
conn.close()

#timeout 시간을 정해줍니다.
server.soc.settimeout(int(tim))
conn, addr = server.soc.accept()
data = conn.recv(1024)
server.run()
conn.close()
