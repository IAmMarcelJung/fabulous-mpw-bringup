#!/bin/env python3

# gpio_config_builder.py
#          Build a pair of configuration bit streams for GPIO on MPW-2 to MPW-5
#          accounting for hold violations between gpio blocks.
#
# Input:   Hold violations between each GPIO and desired configuration
# Output:  Configuration bitsteams for upper and lower gpio chains

import os
import sys
import datetime
from typing import Tuple, List, TextIO
from pathlib import Path

sys.path.append(os.getcwd())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "util"))
from log import setup_logger
from loguru import logger

from config_utils import load_gpio_configs

"""
reg_mprj_xfer bit explanation:
gpio xfer controls (7 bits) bit fields:
    Bit     Function                Details
-------------------------------------------------------------------------------------------------------------------------------
    0       serial xfer/busy        Write 1 to apply configuration values to GPIO. Auto-zeroing. Read back value 1 = busy, 0 = idle
    1       bitbang enable          1 = seral transfer bitbang mode enabled; 0 = bitbang mode disabled
    2       bitbang resetn          0 = bit bang mode reset; 7 = bithang mode normal operation
    3       bitbang load            0 = bit bang mode normal operation; 1 = latch configuration values
    4       bitbang clock           0 -> 1 transition: Advance data in senal shift register by 1 bit in bitbang mode
    5       bitbang data right      Value = data to apply to serial data right side shift register (GPIO 0 to 18) on next bitbang clock
    6       bitbang data left       Value = data to apply to serial data left side shift register (GPIO 19 to 37) on next bitbang clock
"""

NUM_CONFIG_BITS = 13
REG_MPRJ_XFER_DATA_LOW_CHAIN_POS = 5
REG_MPRJ_XFER_DATA_HIGH_CHAIN_POS = 6


def add_config_to_stream(stream: str, config: int, htv_type: int) -> str:
    """Add the intended config to the stream. Some preparations for correcting
    the hold time violation pattern are also done here.

    :param stream: The configuration stream where the config is added to.
    :type stream: str
    :param config: The intended config for the current pin.
    :type config: int
    :param htv_type: The type of hold time violation to consider.
    :type htv_type: int
    :return: The created configuration stream.
    :rtype: str
    """
    next_reg_stream = ""
    if config == gpio_config_io.C_MGMT_OUT:
        # Input is not disabled so that there is no additional
        # transition from 1 to 0
        next_reg_stream = "1100000000001"
    elif config == gpio_config_io.C_MGMT_IN:
        # TODO: Check which value is correct
        # next_reg_stream = "0010000000011"
        next_reg_stream = "1000000000011"
    elif config == gpio_config_io.C_DISABLE:
        next_reg_stream = "0000000000000"
    elif config == gpio_config_io.C_ALL_ONES:
        next_reg_stream = "1111111111111"
    elif config == gpio_config_io.C_USER_BIDIR_WPU:
        next_reg_stream = "0100000000000"
    elif config == gpio_config_io.C_USER_BIDIR_WPD:
        next_reg_stream = "0110000000000"
    elif config == gpio_config_io.C_USER_IN_NOPULL:
        if htv_type == gpio_config_def.H_DEPENDENT:
            # Add another 1 since the input is connected anyway
            # The added one reduces the number of 1 to 0 transitions
            next_reg_stream = "0010000000011"
        else:
            next_reg_stream = "0010000000010"
    elif config == gpio_config_io.C_USER_OUT:
        # Input is not disabled here so that there is no additional
        # transition from 1 to 0
        next_reg_stream = "1100000000000"
    elif config == gpio_config_io.C_MGMT_HIGH_Z_STRONG_0_DISABLE_OUTPUT:
        next_reg_stream = "1000000000011"
    elif config == gpio_config_io.C_MGMT_HIGH_Z_STRONG_0:
        next_reg_stream = "1000000000001"
    elif config == gpio_config_io.C_SPECIAL:
        next_reg_stream = "1000000000000"
    else:
        next_reg_stream = "1100000000000"
    if htv_type == gpio_config_def.H_INDEPENDENT:
        next_reg_stream = next_reg_stream[:-1]

    return stream + next_reg_stream


def compensate_dependent_htv(stream: str, bpos: int) -> str:
    """Compensate for one dependent hold time violation (DHTV).

    This is done by replacing the 0 of a 1 to 0 transition by a 1.
    The reason is that the last 1 before a transition will get lost
    when there is a dependent hold time violation

    :param stream: The stream in which to compensate for a DHTV.
    :type stream: string
    :param bpos: The bit position until which to compensate for a DHTV.
    :type bpos: int
    :return: The resulting configuration stream after compensating for the DHTV.
    :rtype: str
    """
    skip = False
    bits = list(stream)
    for current_bit_pos in range(1, bpos):
        # Replace a 0 by a one after a transition from 1 to 0
        # Since the replacement creates a potential new transition,
        # the next bit after a replacement will be skipped and not replaced
        if (
            bits[current_bit_pos] == "0"
            and bits[current_bit_pos - 1] == "1"
            and not skip
        ):
            bits[current_bit_pos] = "1"
            skip = True
        else:
            skip = False
    return "".join(bits)


def build_streams(
    config_l: List[int],
    config_h: List[int],
    violations_l: List[int],
    violations_h: List[int],
) -> Tuple[str, str]:
    """Build the configuration streams for the high and the low chain.

    :param config_l: Intended configuration for the low chain.
    :type config_l: List[int]
    :param config_h: Intended configuration for the high chain.
    :type config_l: List[int]
    :param violations_l: The violation types of the low chain.
    :type violations_l: List[int]
    :param violations_l: The violation types of the high chain.
    :type violations_h: List[int]
    :return: The high and low configuration streams that were built.
    :rtype: (str, str)
    """
    stream_l = ""
    stream_h = ""
    for k in reversed(range(gpio_config_io.NUM_IO)):
        stream_l = add_config_to_stream(stream_l, config_l[k], violations_l[k])
        stream_h = add_config_to_stream(stream_h, config_h[k], violations_h[k])
    return stream_l, stream_h


def extend_stream_to_n_bits(stream: str, n_bits: int) -> str:
    """Extend a stream to the given amount of bits by prepending a zero.

    :param stream: The stream to be extended.
    :type stream: str
    :param n_bits: The number of bits to which the stream will be extended.
    :type n_bits: int
    :return: The extended stream.
    :rtype: str
    """
    while len(stream) < n_bits:
        stream = "0" + stream
    return stream


def compensate_hold_time_violations(
    bpos: int, stream: str, violation_types: List[int]
) -> str:
    """Compensate for the hold time violations (HTVs) for every IO.

    :param bpos: The bit position until which to compensate for dependent hold
    time violations (DHTVs).
    :type bpos: int
    :param stream: The stream to be compensated for HTVs.
    :type stream: str
    :param violations_types: A list of the types of hold time violations.
    :type violations_types: List[List[Union[str, int]]]
    :return: The stream which is compensated for all HTVs.
    :rtype: str
    """
    for gpio in range(gpio_config_io.NUM_IO):
        if violation_types[gpio] == gpio_config_def.H_DEPENDENT:
            stream = compensate_dependent_htv(stream, bpos)

        if violation_types[gpio] == gpio_config_def.H_INDEPENDENT:
            bpos -= NUM_CONFIG_BITS - 1
        else:
            bpos -= NUM_CONFIG_BITS
    return stream


def print_streams(stream_l: str, stream_h: str) -> None:
    """Print the streams for the low and the high IO chain.

    :param stream_l: The configuration stream for the low IO chain.
    :type stream_l:
    :param stream_h: The configuration stream for the high IO chain.
    :type stream_h:
    """
    print("stream_l:")
    print(stream_l)
    print()
    print("stream_h:")
    print(stream_h)
    print()


def add_file_header(f: TextIO, comment_sequence: str) -> None:
    """Add a header to a given file.

    :param f: The file to which the header is added.
    :type TextIO:
    :param comment_sequence: The comment sequence to use in the file.
    :type comment_sequence: str

    """
    f.write(
        f"{comment_sequence} Generated by gpio_config_builder.py for part"
        + f" {gpio_config_def.part} and voltage {gpio_config_def.voltage}V.\n"
    )
    f.write(f"{comment_sequence} Time: {datetime.datetime.now()}\n")
    f.write("\n")


def create_python_config_data_file(stream_l: str, stream_h: str) -> None:
    """Create a python file containing the configuration data.

    :param stream_l: The configuration stream for the low IO chain.
    :type stream_l:
    :param stream_h: The configuration stream for the high IO chain.
    :type stream_h:
    """
    f = open("gpio_config_data.py", "w")
    add_file_header(f, "#")
    f.write("config_data_h = '" + stream_h + "'\n")
    f.write("config_data_l = '" + stream_l + "'\n")
    f.close()


def create_config_data_header_file(config_stream: List[int], n_bits: int) -> None:
    """Create a C header file containing the configuration data.

    :param config_stream: The configuration stream containing the configuration
    data.
    :type config_stream: List[int]
    :param n_bits: The number of bits in the configuration stream.
    :type n_bits: int

    :param n_bits:
    :type n_bits: int
    """
    f = open("gpio_config_data.h", "w")
    add_file_header(f, "//")

    f.write("char config_stream[] = {\n")
    f.write("    0x{:02x}".format(n_bits))
    for bytenum, byte in enumerate(config_stream):
        # Add a newline after every 12th byte, considering that the first byte
        # is already added
        if ((bytenum + 1) % 12) == 0:
            f.write(",\n    0x{:02x}".format(byte))
        else:
            f.write(", 0x{:02x}".format(byte))

    f.write("};\n")
    f.close()


def build_config_byte_stream(stream_l: str, stream_h: str, n_bits: int) -> List[int]:
    """Build the config stream as a byte stream

    :param n_bits: The number of bits the bit config stream has.
    :type n_bits:
    :return: The built byte config stream.
    :rtype: List[int]
    """
    config_stream = []
    for bit_pos in range(n_bits):
        value = (int(stream_l[bit_pos]) << REG_MPRJ_XFER_DATA_LOW_CHAIN_POS) + (
            int(stream_h[bit_pos]) << REG_MPRJ_XFER_DATA_HIGH_CHAIN_POS
        )
        config_stream.append(0x06 + value)

    # Add zeros at the end of the stream to compensate for the IHTVs
    config_stream += [0x00] * (CONFIG_STREAM_TARGET_LEN - n_bits)
    return config_stream


if __name__ == "__main__":
    setup_logger(0)
    try:
        gpio_config_io, gpio_config_def = load_gpio_configs()
    except FileNotFoundError as e:
        logger.error(f"{e}\nDoes the file for the specified part and voltage exist?")
        exit(1)
    except Exception as e:
        logger.exception("Unexpected error while loading config.")
        exit(1)
    print(
        f"Creating config data for part {gpio_config_def.part} using {gpio_config_def.voltage}V."
    )
    CONFIG_STREAM_TARGET_LEN = gpio_config_io.NUM_IO * NUM_CONFIG_BITS

    # Extract the violations
    violations_l = [violation[1] for violation in gpio_config_def.gpio_l]
    violations_h = [violation[1] for violation in gpio_config_def.gpio_h]

    stream_l, stream_h = build_streams(
        gpio_config_io.config_l, gpio_config_io.config_h, violations_l, violations_h
    )

    longest_stream_len = max(len(stream_h), len(stream_l))
    stream_l = extend_stream_to_n_bits(stream_l, longest_stream_len)
    stream_h = extend_stream_to_n_bits(stream_h, longest_stream_len)

    longest_stream_len = max(len(stream_h), len(stream_l))

    bpos_h = len(stream_h)
    bpos_l = len(stream_l)

    stream_l = compensate_hold_time_violations(bpos_l, stream_l, violations_l)
    stream_h = compensate_hold_time_violations(bpos_h, stream_h, violations_h)

    config_stream = build_config_byte_stream(stream_l, stream_h, longest_stream_len)
    len_config_stream = len(config_stream)

    create_python_config_data_file(stream_l, stream_h)
    create_config_data_header_file(config_stream, len_config_stream)
    print(f"Length of config stream: {len_config_stream}")
