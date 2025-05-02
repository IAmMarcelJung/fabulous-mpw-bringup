#!/usr/bin/env python3

from pyftdi.ftdi import Ftdi
import time
import sys, os
from pyftdi.spi import SpiController, SpiGpioPort
import binascii
import asyncio
from log import setup_logger
from loguru import logger
from asyncio import Event
from io import StringIO
from typing import Callable, Any, Coroutine


SR_WIP = 0b00000001  # Busy/Work-in-progress bit
SR_WEL = 0b00000010  # Write enable bit
SR_BP0 = 0b00000100  # bit protect #0
SR_BP1 = 0b00001000  # bit protect #1
SR_BP2 = 0b00010000  # bit protect #2
SR_BP3 = 0b00100000  # bit protect #3
SR_TBP = SR_BP3  # top-bottom protect bit
SR_SP = 0b01000000
SR_BPL = 0b10000000
SR_PROTECT_NONE = 0  # BP[0..2] = 0
SR_PROTECT_ALL = 0b00011100  # BP[0..2] = 1
SR_LOCK_PROTECT = SR_BPL
SR_UNLOCK_PROTECT = 0
SR_BPL_SHIFT = 2

CMD_READ_STATUS = 0x05  # Read status register
CMD_WRITE_ENABLE = 0x06  # Write enable
CMD_WRITE_DISABLE = 0x04  # Write disable
CMD_PROGRAM_PAGE = 0x02  # Write page
CMD_EWSR = 0x50  # Enable write status register
CMD_WRSR = 0x01  # Write status register
CMD_ERASE_SUBSECTOR = 0x20
CMD_ERASE_HSECTOR = 0x52
CMD_ERASE_SECTOR = 0xD8
CMD_ERASE_CHIP = 0x60
CMD_RESET_CHIP = 0x99
CMD_JEDEC_DATA = 0x9F

CMD_READ_LO_SPEED = 0x03  # Read @ low speed
CMD_READ_HI_SPEED = 0x0B  # Read @ high speed
ADDRESS_WIDTH = 3

JEDEC_ID = 0xEF
SPI_FREQ_MAX = 104  # MHz
CMD_READ_UID = 0x4B
UID_LEN = 0x8  # 64 bits
READ_UID_WIDTH = 4  # 4 dummy bytes

CARAVEL_PASSTHRU = 0xC4
CARAVEL_STREAM_READ = 0x40
CARAVEL_STREAM_WRITE = 0x80
CARAVEL_REG_READ = 0x48
CARAVEL_REG_WRITE = 0x88

FIRMWARE_WRITE = True
FIRMWARE_VERIFY = False

GPIO_UART_EN_POS = 8
GPIO_RX_LED_POS = 10
GPIO_TX_LED_POS = 11


class Led:
    """Class definition for the LED connected to the FTDI chip."""

    def __init__(self, gpio: SpiGpioPort) -> None:
        """Initialize an Led object.
        :param gpio: The GPIO connected to the LED.
        :type gpio: SpiGpioPort
        """

        self.gpio = gpio
        self.led = False
        self.gpio_reg = 0b000100000000

    async def toggle(self, delay: float):
        """Toggle the led once and wait for the specified delay.

        :param delay: The delay in seconds to wait after toggling the LED.
        :type delay: float
        """
        self.led = not self.led
        self.set_value(GPIO_TX_LED_POS, self.led)
        await asyncio.sleep(delay)

    def set_value(self, led_pos: int, value: bool):
        """Set the LED to the specified value.

        :param led_pos: The bit position of the LED.
        :type led_pos:
        :param value: The value to which the LED is set
        :type value: bool
        """
        if not value:
            self.gpio_reg |= 1 << led_pos
        else:
            self.gpio_reg &= ~(1 << led_pos)
        if self.gpio:
            self.gpio.write(self.gpio_reg)

    async def toggle_until_stop_event(self, delay: float, stop_event: Event):
        """Toggle the led until the stop event is set.

        :param stop_event: The stop event for which to check.
        :type stop_event: Event
        """
        while not stop_event.is_set():
            await self.toggle(delay)


class UartEnablePin:
    """Class definition for the UART enable pin"""

    def __init__(self, gpio):
        self.gpio = gpio

    def set_value(self, value):
        output = value << GPIO_UART_EN_POS
        if self.gpio:
            self.gpio.write(output)


class Memory:
    """Class defintion for interacting with the memory."""

    def __init__(self, slave) -> None:
        """Initialize a Memory object."""
        self.slave = slave

    def write_passthrough_command(self, command_id: int) -> None:
        """Write the command in passthrough mode to the HKSPI.

        :param command_id: The ID of the command.
        :type command_id: int
        """
        self.slave.write([CARAVEL_PASSTHRU, command_id])

    async def erase(self, stop_event: asyncio.Event) -> None:
        """Erase the flash memory.

        :param stop_event: The stop event to set when erasing is done.
        :type stop_event: asyncio.Event
        """
        logger.info("Resetting Flash...")
        self.slave.write([CARAVEL_PASSTHRU, CMD_RESET_CHIP])

        logger.info(f"Status = 0x{self.get_status():02x}")

        jedec = self.slave.exchange([CARAVEL_PASSTHRU, CMD_JEDEC_DATA], 3)
        logger.info(f"JEDEC = {binascii.hexlify(jedec)}")

        if jedec[0:1] != bytes.fromhex("ef"):
            logger.error("Winbond flash not found")
            stop_event.set()
            raise MemoryError
        else:
            logger.success("JEDEC info correct")

        logger.info("Erasing chip...")
        self.write_passthrough_command(CMD_WRITE_ENABLE)
        self.write_passthrough_command(CMD_ERASE_CHIP)

        while self.is_busy():
            await asyncio.sleep(0.1)

        logger.success("Done")
        logger.info(f"Status = {hex(self.get_status())}")
        stop_event.set()

    def is_busy(self) -> bool:
        """Check if the memory is busy.

        :returns: True if the memory is busy, else False.
        :rtype: bool
        """
        return bool(self.get_status() & SR_WIP)

    def get_status(self) -> int:
        """Get the memory status.

        :returns: The memory status.
        :rtype: int
        """
        return int.from_bytes(
            self.slave.exchange([CARAVEL_PASSTHRU, CMD_READ_STATUS], 1),
            byteorder="big",
        )

    async def firmware_action(
        self, file_path: str, write: bool, stop_event: Event
    ) -> None:
        """Executes a memory action depending on the write flag.
        If the write flag is set, the firmware will be written into memory.
        Else the memory content will be compared to the firmware file.

        :param file_path: The path to the firmware file.
        :type file_path: str
        :param write: A flag
        :type file_path: str
        :param stop_event: The stop event to set when the action is done.
        :type stop_event: Event

        """
        if not write:
            logger.info("************************************")
            logger.info("Verifying...")
            logger.info("************************************")

        addr = 0
        total_bytes = 0
        buf = bytearray()
        nbytes = 0

        with open(file_path, mode="r") as f:
            for line in f:
                if line.startswith("@"):
                    addr = int(line[1:], 16)
                    logger.info(f"setting address to {hex(addr)}")
                else:
                    values = bytearray.fromhex(line.rstrip())
                    buf.extend(values)
                    nbytes += len(values)

                if nbytes >= 256 or (line and line.startswith("@") and nbytes > 0):
                    total_bytes += nbytes
                    await self.__transfer_sequence(write, nbytes, buf, addr)

                    if nbytes > 256:
                        buf = buf[256:]
                        addr += 256
                        nbytes -= 256
                        logger.warning("*** over 256 hit")
                    else:
                        buf = bytearray()
                        addr += 256
                        nbytes = 0

            if nbytes > 0:
                total_bytes += nbytes
                await self.__transfer_sequence(write, nbytes, buf, addr)

        logger.info(f"total_bytes = {total_bytes}")
        stop_event.set()

    async def __compare_buffers(
        self, rcmd: bytearray, nbytes: int, buf: bytearray, addr: int
    ) -> None:
        """Compare the given buffer the buffer read from the memory.

        :param rcmd: The read command to be executed for the transfer.
        :type rcmd: bytearray
        :param nbytes: The number of bytes to be read.
        :type nbytes: int
        :param buf: The buffer to compare to the buffer read.
        :type nbytes: int
        :param addr: The addr at which the buffers are compared.
        :type addr: int

        """
        buf2 = self.slave.exchange(rcmd, nbytes)
        while self.is_busy():
            await asyncio.sleep(0.1)
        if buf == buf2:
            logger.info(f"addr {hex(addr)}: read compare successful")
        else:
            logger.error(f"addr {hex(addr)}: *** read compare FAILED ***")
            print(binascii.hexlify(buf))
            print("<----->")
            print(binascii.hexlify(buf2))

    async def __write_actions(self, wcmd, buf, addr) -> None:
        """The action to execute for a write transfer.

        :param wcmd: The write command to be executed for the transfer.
        :param addr: The address where the buffer will be written.
        """
        wcmd.extend(buf)
        self.slave.exchange(wcmd)
        while self.is_busy():
            await asyncio.sleep(0.1)

        logger.info(f"addr {hex(addr)}: flash page write successful")

    async def __transfer_sequence(
        self, write: bool, nbytes: int, buf: bytearray, addr: int
    ) -> None:
        """Defines the sequence to transfer data. Depending on the write flag it can be read or write.

        :param write: A flag to signalize whether the transfer should be read or write.
        :type write: bool
        :param nbytes: The number of bytes to transfer.
        :type write: int
        :param buf: The buffer to be transferred.
        :type buf: bytearray
        :param addr: The address where to access the data.
        :type buf: int
        """
        if write:
            self.slave.write([CARAVEL_PASSTHRU, CMD_WRITE_ENABLE])
            memory_command = CMD_PROGRAM_PAGE
        else:
            memory_command = CMD_READ_LO_SPEED

        cmd = bytearray(
            (
                CARAVEL_PASSTHRU,
                memory_command,
                (addr >> 16) & 0xFF,
                (addr >> 8) & 0xFF,
                addr & 0xFF,
            )
        )
        if write:
            await self.__write_actions(cmd, buf, addr)
        else:
            await self.__compare_buffers(cmd, nbytes, buf, addr)


class MyFtdi(Ftdi):
    """Represents the FTDI object, inherits from the Ftdi class defined in pyftdi."""

    def __init__(self) -> None:
        """Initialize a MyFtdi object."""
        super().__init__()
        self.device = self.__read_device_url()
        self.spi = SpiController(cs_count=2)
        self.spi.configure(self.device)
        self.slave = self.spi.get_port(cs=0, freq=12e6, mode=0)
        self.led = self.__assign_led_to_gpio()
        self.memory = Memory(self.slave)
        self.mfg_id = bytes(0)

    def enable_cpu_reset(self) -> None:
        """Reset the CPU over an SPI command."""
        self.slave.write([CARAVEL_REG_WRITE, 0x0B, 0x01])

    def disable_cpu_reset(self) -> None:
        """Reset the CPU over an SPI command."""
        self.slave.write([CARAVEL_REG_WRITE, 0x0B, 0x00])

    def print_manufacturer_product_and_project_id(self) -> None:
        """Print the manufacturer and product ID."""
        logger.info("Caravel data:")
        self.mfg_id = self.slave.exchange([CARAVEL_STREAM_READ, 0x01], 2)
        mfg_id_int = int.from_bytes(self.mfg_id, byteorder="big")
        logger.info(f"   Manufacturer ID = 0x{mfg_id_int:04x}")

        product = self.slave.exchange([CARAVEL_REG_READ, 0x03], 1)
        product_int = int.from_bytes(product, byteorder="big")
        logger.info(f"   Product ID      = 0x{product_int:02x}")

    def check_manufacturer_id(self) -> None:
        """Check the manufacturer ID of the chip."""
        mfg_int = int.from_bytes(self.mfg_id, byteorder="big")
        if mfg_int != 0x0456:
            logger.error(
                f"Manufacturer ID does not does not match! Expected 0x0456, got {hex(mfg_int)}."
            )
            logger.warning(
                "You might want to power cycle the board and start flashing before the firmware configures the GPIOs."
            )
            exit(2)

    def __read_device_url(self) -> str:
        """Sets the URL of the connected FTDI device.
        :returns: The device URL of the connected FTDI device.
        :rtype: str
        """

        s = StringIO()
        self.show_devices(out=s)
        devlist = s.getvalue().splitlines()[1:-1]
        ftdi_devices = []
        for dev in devlist:
            url = dev.split("(")[0].strip()
            name = "(" + dev.split("(")[1]
            if name == "(Single RS232-HS)":
                ftdi_devices.append(url)
        if len(ftdi_devices) == 0:
            logger.error("Error: No matching FTDI devices on USB bus!")
            sys.exit(1)
        elif len(ftdi_devices) > 1:
            logger.error("Error: Too many matching FTDI devices on USB bus!")
            self.show_devices()
            sys.exit(1)
        else:
            logger.success("Found one matching FTDI device at " + ftdi_devices[0])
        return ftdi_devices[0]

    def __assign_led_to_gpio(self) -> Led:
        """Assign the LED to the correct GPIO.
        :returns: The LED associatied to the GPIO.
        :rtype: Led
        """

        gpio = self.spi.get_gpio()
        gpio.set_direction(0b110100000000, 0b110100000000)  # (mask, dir)
        return Led(gpio)


def get_file_path_from_args(args: list[str]) -> str:
    """Gets the file path from the given command line arguments.

    :param args: The given command line arguments.
    :type args: list[str]
    :returns: The file path.
    :rtype: str
    """
    if len(args) < 2:
        logger.warning(f"Usage: {os.path.basename(__file__)} <file>")
        sys.exit()

    file_path = args[1]

    if not os.path.isfile(file_path):
        logger.error("File not found.")
        sys.exit()
    return file_path


async def toggle_led_during_ftdi_action(
    action: Callable[..., Coroutine[Any, Any, None]],
    ftdi: MyFtdi,
    delay: float,
    *args: Any,
) -> None:
    """Toggle the FTDI LED when an FTDI action is in progress.

    :param action: The action to be executed.
    :type action: Callable[..., Coroutine[Any, Any, None]]
    :param ftdi: The ftdi device to perform the action on.
    :type ftdi: MyFtdi
    :param delay: The delay to use for the LED toggling.
    :type delay: float
    :param args: Any number of positional arugments
    :type args: Any
    """
    stop_event = asyncio.Event()

    toggle_task = asyncio.create_task(
        ftdi.led.toggle_until_stop_event(delay, stop_event)
    )
    action_task = asyncio.create_task(action(*args, stop_event))
    await toggle_task
    await action_task


async def main() -> None:
    """The main function of this module"""
    file_path = get_file_path_from_args(sys.argv)

    ftdi = MyFtdi()
    ftdi.led.set_value(GPIO_RX_LED_POS, False)
    ftdi.enable_cpu_reset()
    ftdi.print_manufacturer_product_and_project_id()
    try:
        await toggle_led_during_ftdi_action(ftdi.memory.erase, ftdi, 0.5)
    except MemoryError:
        logger.warning(
            "Please power cycle the board and try flashing again"
            + " immediately! Also check that the UART_EN jumper is not set.",
        )
        ftdi.led.set_value(GPIO_TX_LED_POS, False)
        exit(1)

    await toggle_led_during_ftdi_action(
        ftdi.memory.firmware_action, ftdi, 0.025, file_path, FIRMWARE_WRITE
    )

    # This won't take long and might not even loop once but should still be there to be sure.
    while ftdi.memory.is_busy():
        time.sleep(0.5)

    # This will finish almost instantly, no need to toggle the LED.
    stop_event = asyncio.Event()
    await ftdi.memory.firmware_action(file_path, FIRMWARE_VERIFY, stop_event)
    ftdi.led.set_value(GPIO_TX_LED_POS, False)

    ftdi.disable_cpu_reset()
    ftdi.spi.close(True)


if __name__ == "__main__":
    setup_logger(0)
    asyncio.run(main())
