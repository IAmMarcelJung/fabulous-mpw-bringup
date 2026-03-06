#include <defs.h>
#include <global_defs.h>
#include <gpio_config_data.h>
#include <gpio_config_io.h>
#include <helpers.h>
#include <register_actions.h>
#include <stub.h>

int main() {
  reg_gpio_mode1 = 1;
  reg_gpio_mode0 = 0;
  reg_gpio_ien = 1;
  reg_gpio_oe = 1;
  reg_gpio_out = 1;

  blink(6, 2500000);

  // Configure the IOs so the eFPGA has access to them
  reg_gpio_out = 1;
  gpio_config_io(config_stream);

  blink(3, 2500000);
  reg_gpio_out = 0;

  while (1) {
  }

  return 0;
}
