#include "send_packet.h"
#include "../../riscv_firmware_src/defs.h"

void count_down(const int d) {
    /* Configure timer for a single-shot countdown */
    reg_timer0_config = 0;
    reg_timer0_data = d;
    reg_timer0_config = 1; /* Enabled, one-shot, down count */

    // Loop, waiting for value to reach zero
    reg_timer0_update = 1; // latch current value
    while (reg_timer0_value > 0) {
        reg_timer0_update = 1;
    }
}

void send_pulse_io37() {
    int mask = 0x1F;
    int temp = reg_mprj_datah & mask;
    reg_mprj_datah = temp; // 0
    count_down(PULSE_WIDTH);
    temp = reg_mprj_datah;
    reg_mprj_datah = temp | 0x20; // 1
    count_down(PULSE_WIDTH);
}

void send_packet_io37(int num_pulses) {
    // send pulses
    for (int i = 0; i < num_pulses + 1; i++) {
        send_pulse_io37();
    }
    // end of packet
    count_down(PULSE_WIDTH * 10);
}

int receive_io0() {
    int mask = 0x1;
    int old_received;
    int received;
    int pulse = 0;
    int timeout_count = 0;
    int timeout = 5000;
    /*
        flag == 1 --> increment
        flag == 2 --> reset
    */
    int flag = 0;
    old_received = reg_mprj_datal & mask;
    send_packet_io37(2);
    while (1) {
        received = reg_mprj_datal & mask;
        if (received != old_received) {
            pulse++;
            old_received = received;
        }
        if (pulse == 8) {
            flag = 1;
            return flag;
        }
    }
}
