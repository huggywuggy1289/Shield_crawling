#include <stdio.h>
#include <stdlib.h>
#include <pcap.h>

// 패킷 핸들러 함수
void packetHandler(unsigned char *userData, const struct pcap_pkthdr *pkthdr, const unsigned char *packet) {
    // 패킷 크기 출력
    printf("Packet size: %d bytes\n", pkthdr->len);
    
    // 패킷 데이터를 16진수로 출력
    for (int i = 0; i < pkthdr->len; ++i) {
        printf("%02x ", packet[i]);
        if ((i + 1) % 16 == 0)
            printf("\n");
    }
    printf("\n");
}

int main() {
    pcap_t *handle;             // pcap 핸들러
    char errbuf[PCAP_ERRBUF_SIZE]; // 오류 버퍼

    // 네트워크 인터페이스 찾기
    char *dev = pcap_lookupdev(errbuf);
    if (dev == NULL) {
        fprintf(stderr, "Couldn't find default device: %s\n", errbuf);
        return 1;
    }
    printf("Device: %s\n", dev);

    // 네트워크 인터페이스 열기
    handle = pcap_open_live(dev, BUFSIZ, 1, 1000, errbuf);
    if (handle == NULL) {
        fprintf(stderr, "Couldn't open device %s: %s\n", dev, errbuf);
        return 1;
    }

    // 패킷 캡처 및 처리 루프
    pcap_loop(handle, -1, packetHandler, NULL);

    // 핸들 닫기
    pcap_close(handle);
    return 0;
}
