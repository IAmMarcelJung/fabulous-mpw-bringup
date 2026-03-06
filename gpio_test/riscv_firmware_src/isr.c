// This file is Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
// License: BSD

#include "isr.h"

uint16_t flag;

void isr(void) {
  irq_setmask(0);
  reg_timer0_irq_en = 0; // disable interrupt

  reg_timer0_update = 1;
  if (reg_timer0_value == 0)
    flag = 1;
  else
    reg_timer0_irq_en = 1;

  return;
}
