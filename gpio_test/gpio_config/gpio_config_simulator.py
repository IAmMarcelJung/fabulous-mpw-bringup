#!/bin/env python3
#
# gpio_reg_simulator.py ---  Simulate GPIO configuration based on data independent
# and dependent hold violations for MPW-2 to MPW-5
#
# Input:   Hold violations between each GPIO and input pattern for configuration
# Output:  Actual GPIO data in the GPIO register
#

import os, sys

sys.path.append(os.getcwd())

from bitstring import BitArray
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "util"))
from log import setup_logger
from loguru import logger

from gpio_config_data import config_data_h, config_data_l
from config_utils import load_gpio_def_config


NUM_IO = 19
MAX_IO_NUM = 37
NUM_CONFIG_BITS = 13


def print_regs(chain, is_high_chain):
    print()
    for i, reg in enumerate(chain):
        if is_high_chain:
            reg_num = MAX_IO_NUM - i
        else:
            reg_num = i

        print(f"{reg_num:02d}: {reg.bin}")


# gpio shift registers
gpio_chain_l = [
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
]

del gpio_chain_l[NUM_IO:]

gpio_chain_l = [
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
    BitArray(length=NUM_CONFIG_BITS),
]

del gpio_chain_l[NUM_IO:]

# ------------------------------------------


def simulate_chain_htvs(
    gpio_chain: List[BitArray], config_data, gpio_violations, is_high_chain
):
    """Simulate the hold time violations for the given chain

    :param gpio_chain: The gpio register
    """

    for bit in config_data:
        # shift based on the number of bits in the config stream for that register
        # from MSB to LSB
        current_shifted_out = previous_shifted_out = previous_reg_last_bit = False

        # iterate through each gpio
        for current_gpio_reg_num, current_gpio_reg in enumerate(gpio_chain):
            # store bit to be shifted off
            current_shifted_out = current_gpio_reg[-1]

            # right shift all bits in the register
            current_gpio_reg.ror(1)

            if gpio_violations[current_gpio_reg_num] == gpio_config_def.H_INDEPENDENT:
                # shift in bit from previous gpio register, skipping the first bit
                current_gpio_reg[1] = previous_shifted_out
                current_gpio_reg[0] = previous_reg_last_bit

            elif (
                gpio_violations[current_gpio_reg_num] == gpio_config_def.H_DEPENDENT
                and previous_reg_last_bit == False
            ):
                current_gpio_reg[0] = False

            # effectively H_NONE
            else:
                # shift in bit from previous gpio register
                current_gpio_reg[0] = bool(previous_shifted_out)

            previous_shifted_out = current_shifted_out
            previous_reg_last_bit = current_gpio_reg[-1]

        # shift in next bit from configuration stream
        gpio_chain[0][0] = bool(int(bit))

    print_regs(gpio_chain, is_high_chain)


if __name__ == "__main__":
    setup_logger(0)
    try:
        gpio_def = load_gpio_def_config()
    except FileNotFoundError as e:
        logger.error(f"{e}\nDoes the file for the specified part and voltage exist?")
        exit(1)
    except Exception as e:
        logger.exception("Unexpected error while loading config.")
        exit(1)
    gpio_config_def = load_gpio_def_config()
    violations_l = [violation[1] for violation in gpio_config_def.gpio_l]
    violations_h = [violation[1] for violation in gpio_config_def.gpio_h]
    simulate_chain_htvs(gpio_chain_l, config_data_h, violations_h, True)
    simulate_chain_htvs(gpio_chain_l, config_data_l, violations_l, False)
