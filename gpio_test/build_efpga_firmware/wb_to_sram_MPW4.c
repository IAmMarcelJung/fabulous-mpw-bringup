#include "../gpio_config/gpio_config_io.h"
#include <stdint.h>

#include <defs.h>
#include <global_defs.h>
#include <gpio_config_data.h>
#include <helpers.h>
#include <register_actions.h>
#include <stub.h>

#define RESET_VECTOR_WORD_ADDRESS 32 // 128 / 8
#define NUM_WORDS 10
#define TEST_WORD 0xBADCAFFE

#define SRAM_2_OFFSET 0x100                    // 0x400 / 4
#define SRAM_LAST_ACCESSIBLE_WORD_ADDRESS 0x3F // 0FF / 4
#define PROGRAM_START_ADDRESS 0x20             // 0x80 / 4

int main() {
  reg_gpio_mode1 = 1;
  reg_gpio_mode0 = 0;
  reg_gpio_ien = 1;
  reg_gpio_oe = 1;
  reg_gpio_out = 1;
  reg_wb_enable = 1;
  reg_hkspi_disable = 1;

  reg_gpio_out = 0;

  // Set LA bits 0-3 as outputs
  reg_la0_oenb = reg_la0_oenb & ~0xF;
  //
  // Set Ibex control bits to zero
  reg_la0_data = 0u;

  volatile uint32_t *sram1 = (uint32_t *)&reg_mprj_slave;
  volatile uint32_t *sram2 = (uint32_t *)&reg_mprj_slave + SRAM_2_OFFSET;

  uint8_t fail;

  reg_mprj_datal = 0x1;

  while (1) {
    sram1[0] = TEST_WORD;
    sram1[0] = TEST_WORD;
    if (sram1[0] == TEST_WORD) {
      fail = 0;
    } else {
      fail = 1;
    }
    if (sram1[0] == TEST_WORD) {
      fail = 0;
    } else {
      fail = 1;
    }
    if (fail) {
      blink(3, 500000);
      reg_mprj_datal = reg_mprjdata_l = 0x2;
    } else {
      reg_mprj_datal = 0x3;
      blink(3, 100000);
    }
    delay(1000000);
  }

  return 0;
}
