컴퓨터네트워크 HW#3
TCP 기반 소켓 프로그래밍 작성 후 GO-BACK-N 동작 구현하기
소프트웨어학부 20181702 최혁태


파일은 총 3개입니다.
패킷을 보내는 GBN_sender.py 파일, 패킷을 받는 GBN_receiver.py 파일, sender에서 receiver로 보내는 test.txt 파일이 있습니다.

GBN_sender.py를 실행하면 window size, packet 개수, time out 초를 설정할 수 있습니다.
test.txt 파일은 sender파일을 실행했을 때 지정해놓은 패킷의 개수로 나누어 sender → receiver로 보냅니다.


GBN_sender.py 파일은 AWS EC2 instance를 활용한 Ubuntu 18.04 클라우드 환경에서 실행됩니다.
GBN_receiver.py 파일은 제 컴퓨터(로컬환경)에서 실행됩니다.

감사합니다.