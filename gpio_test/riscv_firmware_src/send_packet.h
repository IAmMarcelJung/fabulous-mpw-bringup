#ifndef SEND_PACKET_H
#define SEND_PACKET_H

#define PULSE_WIDTH 250000

void count_down(const int d);

void send_pulse_io37();

void send_packet_io37(int num_pulses);

int receive_io0();

#endif /* SEND_PACKET_H */
