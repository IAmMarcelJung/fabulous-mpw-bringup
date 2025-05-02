#include "gpio_config_io.h"
#include "../riscv_firmware_src/defs.h"
#include <csr.h>

void delay(const int clock_cycles) {

    /* Configure timer for a single-shot countdown */
    reg_timer0_config = 0;
    reg_timer0_data = clock_cycles;
    reg_timer0_config = 1;

    // Loop, waiting for value to reach zero
    reg_timer0_update = 1; // latch current value
    while (reg_timer0_value > 0) {
        reg_timer0_update = 1;
    }
}

void bb_mode() {
    // Enable bit-bang mode
    reg_mprj_xfer = 0x06; // Enable bit-bang mode
    reg_mprj_xfer = 0x02; // Pulse reset
    reg_mprj_xfer = 0x06;
}

void load() {
    reg_mprj_xfer = 0x06;
    delay(WAIT);
    reg_mprj_xfer = 0x0e; // Apply load
    delay(WAIT);
    reg_mprj_xfer = 0x06;
    delay(WAIT);
}

void clear_registers() {
    // clear shift register with zeros and load before starting test
    for (int i = 0; i < 250; i++) {
        reg_mprj_xfer = 0x06;
        delay(WAIT);
        reg_mprj_xfer = 0x16;
        delay(WAIT);
    }
    load();
}

void gpio_config_io(char const *const config_stream) {
    char n_bits = config_stream[0];
    // start at  offset 1, first value is n_bits
    for (char i = 1u; i < n_bits; i++) {
        reg_mprj_xfer = config_stream[i];
        delay(WAIT);
        reg_mprj_xfer = config_stream[i] + 0x10;
        delay(WAIT);
    }
    load();
}
