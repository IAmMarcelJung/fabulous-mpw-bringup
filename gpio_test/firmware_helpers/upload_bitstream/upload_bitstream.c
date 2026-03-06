#include <defs.h>
#include <global_defs.h>
#include <upload_bitstream.h>
#ifndef GTEST
#include <register_actions.h>
#endif

#ifdef GTEST
#define USE_FUNCTIONS
#endif

#include <gpio_config_io.h>

#define PIN_RESET GPIO_35

// Use Gpio 36 and 37 since the probality that they can be configured as
// management output pins is high
#define PIN_SCLK GPIO_37
#define PIN_SDATA GPIO_36

#define CTRL_WORD_DISABLE_BITBANG 0x0000FAB0u
#define CTRL_WORD_ENABLE_BITBANG 0x0000FAB1u

#define EXTRACT_BYTE_FROM_WORD(word, byte_index)                               \
  (((word) >> (BITS_IN_BYTE * byte_index)) & 0xFFu)
#define GET_BIT_AS_BOOL_FROM_BYTE(byte, index)                                 \
  ((bool)(((byte) >> (index)) & 0x01u))
#define MODULO_4(data)                                                         \
  (data & 0x03u) // Just using the last two bits is effectively modulo 4

#define DELAY 50u

static volatile uint32_t data_reg_shadow = 0u;

static void transmit_byte(uint8_t data_byte, uint8_t ctrl_word_byte);

#define RESET_REGISTER REGISTER_3_DATA_BIT_POS
#define S_CLK_REGISTER REGISTER_10_DATA_BIT_POS
#define S_DATA_REGISTER REGISTER_11_DATA_BIT_POS

// NOTE:
// Make sure to adjust the hardware register depending on which GPIOs are used:
//      0-31 -> reg_mprj_gpiol,
//      32-37 -> reg_mprj_gpioh
#define HARDWARE_REGISTER reg_mprj_datal

void bitstream_init(GPIO *const gpio) { gpio_init(gpio); }

/**
 * @brief Use bitbanging to upload the bitstream to the FPGA.
 * @param bitstream_data The bitstream data to be transmitted to the FPGA.
 * @param bitream_size The bitstream size in bytes.
 * @param ctrl_word The control word used to control the bitbang module.
 */
void upload_bitstream(uint8_t const *const bitstream_data,
                      uint32_t bitream_size) {
  // Reset user logic
#ifndef GTEST
  data_reg_shadow |= REGISTER_DATA_BIT(RESET_REGISTER);
  reg_mprj_datal = data_reg_shadow;
#endif

  // Loop from first to last byte. Inside the byte loop from MSB to LSB.
  for (uint8_t byte_pos = 0u; byte_pos < PREAMBLE_SIZE; byte_pos++) {
    uint8_t control_word_byte_pos =
        MODULO_4(~byte_pos); // Invert because we want to start from the
                             // most significant byte.
    uint8_t current_control_word_byte =
        EXTRACT_BYTE_FROM_WORD(CTRL_WORD_ENABLE_BITBANG, control_word_byte_pos);
    transmit_byte(0xFF, current_control_word_byte);
  }

  for (uint32_t byte_pos = 0u; byte_pos < bitream_size; byte_pos++) {
    uint8_t current_byte = bitstream_data[byte_pos];
    uint8_t control_word_byte_pos =
        MODULO_4(~byte_pos); // Invert because we want to start from the
                             // most significant byte.
    uint8_t current_control_word_byte =
        EXTRACT_BYTE_FROM_WORD(CTRL_WORD_ENABLE_BITBANG, control_word_byte_pos);

    transmit_byte(current_byte, current_control_word_byte);
  }

  for (uint8_t byte_pos = 0u; byte_pos < PREAMBLE_SIZE; byte_pos++) {
    uint8_t control_word_byte_pos =
        MODULO_4(~byte_pos); // Invert because we want to start from the
                             // most significant byte.
    uint8_t current_control_word_byte = EXTRACT_BYTE_FROM_WORD(
        CTRL_WORD_DISABLE_BITBANG, control_word_byte_pos);
    transmit_byte(0x00, current_control_word_byte);
  }

#ifndef GTEST
  clear_bit(S_CLK_REGISTER, &HARDWARE_REGISTER);
  clear_bit(S_DATA_REGISTER, &HARDWARE_REGISTER);
#endif
}

static void transmit_byte(uint8_t data_byte, uint8_t ctrl_word_byte) {
  for (int32_t bit_pos = (int32_t)MSB_IN_BYTE; bit_pos >= 0; bit_pos--) {
    bool set;

    set = GET_BIT_AS_BOOL_FROM_BYTE(data_byte, bit_pos);
#ifdef USE_FUNCTIONS
    set_or_clear_gpio(PIN_SDATA, set);
#else
    if (set)
      data_reg_shadow |= REGISTER_DATA_BIT(S_DATA_REGISTER);
    else
      data_reg_shadow &= ~(REGISTER_DATA_BIT(S_DATA_REGISTER));
    HARDWARE_REGISTER = data_reg_shadow;
#endif

#ifdef USE_FUNCTIONS
    set_gpio(PIN_SCLK);
#else
    data_reg_shadow |= REGISTER_DATA_BIT(S_CLK_REGISTER);
    HARDWARE_REGISTER = data_reg_shadow;
#endif

    set = GET_BIT_AS_BOOL_FROM_BYTE(ctrl_word_byte, bit_pos);

#ifdef USE_FUNCTIONS
    set_or_clear_gpio(PIN_SDATA, set);
#else
    if (set)
      data_reg_shadow |= REGISTER_DATA_BIT(S_DATA_REGISTER);
    else
      data_reg_shadow &= ~(REGISTER_DATA_BIT(S_DATA_REGISTER));
    HARDWARE_REGISTER = data_reg_shadow;
#endif
#ifdef USE_FUNCTIONS
    clear_gpio(PIN_SCLK);
#else
    data_reg_shadow &= ~(REGISTER_DATA_BIT(S_CLK_REGISTER));
    HARDWARE_REGISTER = data_reg_shadow;
#endif
  }
  /*
  // This is only needed when comparing the bitstream to a known good.
#ifdef GTEST
  // Used to format the printed bitstream in the test
  if ((byte_pos + 1) % 4 == 0)
  {
  set_gpio(PIN_SCLK);
  }
#endif
}*/
}
