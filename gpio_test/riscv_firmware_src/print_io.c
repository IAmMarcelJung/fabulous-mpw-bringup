#include "print_io.h"

void uart_putchar(uint32_t c) {
  if (c == '\n')
    uart_putchar('\r');
  while (reg_uart_txfull == 1)
    ;
  reg_uart_data = c;
}

void print(const char *p) {
  while (*p) {
    uart_putchar(*(p++));
    delay(1000);
  }
}

void print_hex(uint32_t v, int digits) {
  for (int i = digits - 1; i >= 0; i--) {
    char c = "0123456789abcdef"[(v >> (4 * i)) & 15];
    uart_putchar(c);
  }
}

void print_dec(uint32_t v) {
  if (v >= 2000) {
    print("OVER");
    return;
  } else if (v >= 1000) {
    uart_putchar('1');
    v -= 1000;
  } else
    uart_putchar(' ');

  if (v >= 900) {
    uart_putchar('9');
    v -= 900;
  } else if (v >= 800) {
    uart_putchar('8');
    v -= 800;
  } else if (v >= 700) {
    uart_putchar('7');
    v -= 700;
  } else if (v >= 600) {
    uart_putchar('6');
    v -= 600;
  } else if (v >= 500) {
    uart_putchar('5');
    v -= 500;
  } else if (v >= 400) {
    uart_putchar('4');
    v -= 400;
  } else if (v >= 300) {
    uart_putchar('3');
    v -= 300;
  } else if (v >= 200) {
    uart_putchar('2');
    v -= 200;
  } else if (v >= 100) {
    uart_putchar('1');
    v -= 100;
  } else
    uart_putchar('0');

  if (v >= 90) {
    uart_putchar('9');
    v -= 90;
  } else if (v >= 80) {
    uart_putchar('8');
    v -= 80;
  } else if (v >= 70) {
    uart_putchar('7');
    v -= 70;
  } else if (v >= 60) {
    uart_putchar('6');
    v -= 60;
  } else if (v >= 50) {
    uart_putchar('5');
    v -= 50;
  } else if (v >= 40) {
    uart_putchar('4');
    v -= 40;
  } else if (v >= 30) {
    uart_putchar('3');
    v -= 30;
  } else if (v >= 20) {
    uart_putchar('2');
    v -= 20;
  } else if (v >= 10) {
    uart_putchar('1');
    v -= 10;
  } else
    uart_putchar('0');

  if (v >= 9) {
    uart_putchar('9');
    v -= 9;
  } else if (v >= 8) {
    uart_putchar('8');
    v -= 8;
  } else if (v >= 7) {
    uart_putchar('7');
    v -= 7;
  } else if (v >= 6) {
    uart_putchar('6');
    v -= 6;
  } else if (v >= 5) {
    uart_putchar('5');
    v -= 5;
  } else if (v >= 4) {
    uart_putchar('4');
    v -= 4;
  } else if (v >= 3) {
    uart_putchar('3');
    v -= 3;
  } else if (v >= 2) {
    uart_putchar('2');
    v -= 2;
  } else if (v >= 1) {
    uart_putchar('1');
    v -= 1;
  } else
    uart_putchar('0');
}

void print_digit(uint32_t v) {
  v &= (uint32_t)0x000F;

  if (v == 9) {
    uart_putchar('9');
  } else if (v == 8) {
    uart_putchar('8');
  } else if (v == 7) {
    uart_putchar('7');
  } else if (v == 6) {
    uart_putchar('6');
  } else if (v == 5) {
    uart_putchar('5');
  } else if (v == 4) {
    uart_putchar('4');
  } else if (v == 3) {
    uart_putchar('3');
  } else if (v == 2) {
    uart_putchar('2');
  } else if (v == 1) {
    uart_putchar('1');
  } else if (v == 0) {
    uart_putchar('0');
  } else if (v == 10) {
    uart_putchar('a');
  } else if (v == 11) {
    uart_putchar('b');
  } else if (v == 12) {
    uart_putchar('c');
  } else if (v == 13) {
    uart_putchar('d');
  } else if (v == 14) {
    uart_putchar('e');
  } else if (v == 15) {
    uart_putchar('f');
  } else
    uart_putchar('*');
}
