#ifndef _PRINT_IO_H_
#define _PRINT_IO_H_

#include <defs.h>
#include <gpio_config_io.h>

void uart_putchar(uint32_t c);
void print(const char *p);
void print_hex(uint32_t v, int digits);
void print_dec(uint32_t v);
void print_digit(uint32_t v);
char getchar_prompt(char *prompt);
uint32_t getchar();
void cmd_echo();

#endif /* PRINT_IO_H */
