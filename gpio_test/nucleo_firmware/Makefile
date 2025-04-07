
# Definition for the directory of this Makefile
THIS_MAKEFILE_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
#

# Definitions used for device interaction
FLASH := /pyboard/flash/
DEV := $(shell mpremote connect list | grep STLink | cut -f 1 -d ' ')
COPY_CMD := rshell --port $(DEV) cp
LS_CMD := rshell --port $(DEV) ls

# Definitions related to firmware creation
INCLUDES := \
	-I../ \
	-I../riscv_firmware_src \
	-I./src \
	-I../hw \
	-I../gpio_config \
	-I../firmware_helpers/upload_bitstream \
	-I../firmware_helpers/gpio \
	-I../firmware_helpers/bitstream \
	-I../firmware_helpers/register_actions \
	-I../firmware_helpers/helpers \
	-I../firmware_helpers/global_defs

SRC_FILES := \
	$(THIS_MAKEFILE_DIR)../riscv_firmware_src/crt0_vex.S \
	$(THIS_MAKEFILE_DIR)../riscv_firmware_src/isr.c \
	$(THIS_MAKEFILE_DIR)../riscv_firmware_src/stub.c \
	$(THIS_MAKEFILE_DIR)../gpio_config/gpio_config_io.c \
	$(THIS_MAKEFILE_DIR)src/send_packet.c \
	$(THIS_MAKEFILE_DIR)../firmware_helpers/upload_bitstream/upload_bitstream.c \
	$(THIS_MAKEFILE_DIR)../firmware_helpers/gpio/gpio.c \
	$(THIS_MAKEFILE_DIR)../firmware_helpers/register_actions/register_actions.c \
	$(THIS_MAKEFILE_DIR)../firmware_helpers/helpers/helpers.c \

TOOLCHAIN_PREFIX := riscv64-unknown-elf
PATTERN ?= config_io_o

# Definitions related to the GPIO config

CONFIG_FILES_DIR := $(THIS_MAKEFILE_DIR)gpio_config_files

.PHONY: clean hex copy repl run copy_config_file

# Set VOLTAGE_STR based on whether VOLTAGE or DEFAULT_VOLTAGE is defined
ifndef VOLTAGE
  ifdef DEFAULT_VOLTAGE
	VOLTAGE_STR := $(subst .,_,$(DEFAULT_VOLTAGE))
  else
	$(error "Neither VOLTAGE nor DEFAULT_VOLTAGE is defined.")
  endif
else
  VOLTAGE_STR := $(subst .,_,$(VOLTAGE))
endif
CONFIG_FILE_PATTERN := gpio_config_def
IO_CONFIG_FILE_PATTERN := gpio_config_io
PART_OUTPUT_FILE := $(CONFIG_FILE_PATTERN)_part_$(PART)_$(VOLTAGE_STR)_V.py
PART_OUTPUT_DIR := part_$(PART)
CONFIG_FILE_TARGET = $(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)/$(PART_OUTPUT_FILE)

GPIO_CONFIG_DATA := $(THIS_MAKEFILE_DIR)../gpio_config/gpio_config_data.h


ifeq ($(wildcard ../nucleo_firmware/$(CONFIG_FILE_TARGET)), )
	PREREQUISITES_IF_CONFIG_FILE_TARGET_EXISTS := $(CONFIG_FILE_TARGET)
endif

# Definitions related to python
PYTHON_SRC := $(THIS_MAKEFILE_DIR)src/

PYTHON_FILES := $(wildcard $(PYTHON_SRC)*.py)
MPY_FILES := $(patsubst $(PYTHON_SRC)%.py,$(PYTHON_SRC)%.mpy,$(PYTHON_FILES))

# General defintions
SED_CMD :=sed -i'.orig' -e


USERNAME := $(shell whoami)
USERNAME_FILE = src/user.py
USERNAME_MPY = src/user.mpy

# Color defintions
GREEN := \033[32m
RED := \033[31m
RESET_COLOR := \033[0m

ifeq ($(strip $(DONT_STRIP_HEX_FILE)),)
	STRIP = $(SED_CMD) '1,/@00/!d' $@
endif

compile: $(MPY_FILES)

$(USERNAME_FILE):
	echo "USER = '$(USER)'" > $@

$(USERNAME_MPY): $(USERNAME_FILE)
	mpy-cross $<

$(PYTHON_SRC)%.mpy: $(PYTHON_SRC)%.py
	mpy-cross $<
	$(COPY_CMD) $@ $(FLASH)

# runs script from the local filesystem
reset: check_device
	mpremote connect $(DEV) exec "import machine; machine.reset()"

# runs script from the local filesystem
version: check_device
	mpremote connect $(DEV) exec "import io_config; io_config.version()"

# run io_config test to characterize a new part
run: check_device check_part hex F746ZG-copy
	mpremote connect $(DEV) exec "import io_config; io_config.run('$(PART)', $(VOLTAGE))"

# copy the definition file for a part after running io_config
get_config: check_device
	mpremote cp :$(CONFIG_FILE_PATTERN).py .

# run a sanity check using the gpio_config_def.py file on the nucleo
sanity_check: check_device hex
ifndef CONFIG_FILE
	$(error CONFIG_FILE is undefined, please export it before running make flash)
else
	$(COPY_CMD) $(CONFIG_FILE) $(FLASH)$(CONFIG_FILE_PATTERN).py
	$(COPY_CMD) $(THIS_MAKEFILE_DIR)config_io_o.hex $(FLASH)
	sync
	sleep 2
	mpremote connect $(DEV) exec "import io_config; io_config.run_sanity_check()"
	mpremote rm :config_io_o.hex
endif

# power up the caravel hat while mounted to Nucleo
poweron: check_device
	mpremote connect $(DEV) exec "import io_config; io_config.run_poweron($(VOLTAGE))"

change_power: check_device check_voltage
	mpremote connect $(DEV) exec "import io_config; io_config.run_change_power($(VOLTAGE))"

# flash firmware on caravel hat while mounted to Nucleo
flash: check_device
ifndef FIRMWARE_FILE
	$(error FIRMWARE_FILE is undefined, please export it before running make flash)
else
	$(COPY_CMD) $(FIRMWARE_FILE) $(FLASH)firmware.hex
	sync
	sleep 2
	mpremote connect $(DEV) exec "import io_config; io_config.run_flash_caravel()"
	# firmware will be written into the SPI flash and is not needed on the Nucleo flash anymore
	mpremote rm :firmware.hex
endif

# enter repl on nucleo
repl:
	mpremote connect $(DEV) repl

# flash micropython firmware image.  this firmware image has been rebuilt to add pins for the Caravel Nucleo HAT
F746ZG: compile
	st-flash --connect-under-reset --format ihex write $(THIS_MAKEFILE_DIR)F746ZG_firmware.hex
	make F746ZG-copy

F413ZH:
	st-flash --connect-under-reset --format ihex write $(THIS_MAKEFILE_DIR)F413ZH_firmware.hex
	sleep 7
	make F413ZH-copy

# copies scripts to nucleo
copy2 F746ZG-copy: compile check_device hex
	$(COPY_CMD) $(THIS_MAKEFILE_DIR)config_io_o.hex $(FLASH)
	sync
	$(LS_CMD) $(FLASH)
	echo "File sytem usage"
	mpremote df

copy3 F413ZH-copy: compile check_device hex
	$(COPY_CMD) $(THIS_MAKEFILE_DIR)config_io_o.hex $(FLASH)
	sync
	$(LS_CMD)
	echo "File sytem usage"
	mpremote df

check_device:
ifndef DEV
	$(error "Nucleo device file not found. Probably the board is not connected?")
endif

check_part:
ifndef PART
	$(error "PART not defined. Please add 'PART=<part_id>'")
endif

check_shuttle:
ifndef SHUTTLE
	$(error "SHUTTLE not defined. Please add 'SHUTTLE=<shuttle>'")
endif

check_voltage:
	@if [ -z "$(VOLTAGE)" ]; then \
		if [ -n "$(DEFAULT_VOLTAGE)" ]; then \
			echo "Using the default voltage of $(DEFAULT_VOLTAGE) V."; \
		else \
			echo "Error: VOLTAGE not defined and DEFAULT_VOLTAGE is also not set."; \
			exit 1; \
		fi; \
	else \
		echo "Using the specified voltage of $(VOLTAGE) V."; \
	fi

check-python:
ifeq ($(shell which python3),)
$(error Please install python 3.6+)
endif

setup: check-python
	python3 -m pip install rshell
	python3 -m pip install mpy-cross
	python3 -m pip install mpremote

copy_gpio_config_io: $(PREREQUISITES_IF_CONFIG_FILE_TARGET_EXISTS)
	cp $(IO_CONFIG_FILE_PATTERN)_$(SHUTTLE).py $(IO_CONFIG_FILE_PATTERN).py

copy_config_file: $(PREREQUISITES_IF_CONFIG_FILE_TARGET_EXISTS) check_shuttle
	cp $(THIS_MAKEFILE_DIR)$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)/$(PART_OUTPUT_FILE) $(CONFIG_FILE_PATTERN).py

store_config_file: check_part check_voltage
		cp $(CONFIG_FILE_PATTERN).py $(THIS_MAKEFILE_DIR)$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)/$(PART_OUTPUT_FILE)

$(CONFIG_FILE_TARGET): | run get_config $(THIS_MAKEFILE_DIR)$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)

$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR):
	mkdir -p $@

gen_config_header: $(GPIO_CONFIG_DATA)

$(GPIO_CONFIG_DATA): check_part check_voltage check_shuttle gpio_config_io.py copy_config_file copy_gpio_config_io
	@echo
	@echo "Building configuration data."
	python3 ../gpio_config/gpio_config_builder.py
	mv gpio_config_data.h $(GPIO_CONFIG_DATA)
	@echo "$(GREEN)Done building configuration data.$(RESET_COLOR)"

.SUFFIXES:

hex: $(PATTERN:=.hex)

%.elf: %.c $(BITSTREAM_HEADER) $(THIS_MAKEFILE_DIR)../riscv_firmware_src/sections.lds $(THIS_MAKEFILE_DIR)../riscv_firmware_src/crt0_vex.S $(GEN_CONFIG_HEADER_PREREQUISITE)
	@echo
	@echo "Compiling firmware."
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-gcc $(INCLUDES) -O3 -g -mabi=ilp32 -march=rv32i_zicsr  -D__vexriscv__ -Wl,-Bstatic,-T,$(THIS_MAKEFILE_DIR)../riscv_firmware_src/sections.lds,--strip-debug -ffreestanding -nostdlib -o $@ $(SRC_FILES) $<
	@echo "$(GREEN)Done compiling firmware.$(RESET_COLOR)"

%.hex: %.elf
	@echo "Converting $< to $@"
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-objcopy -O verilog $< $@
	$(SED_CMD) 's/@1000/@0000/g' $@
	$(STRIP)
	@echo "$(GREEN)Done converting $< to $@.$(RESET_COLOR)"


run_and_store_config: |$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR) store_config_file
run_and_store_config: $(CONFIG_FILE_TARGET)
	@echo "$(GREEN)Executed GPIO test and stored config file to $(THIS_MAKEFILE_DIR)$(CONFIG_FILE_TARGET).$(RESET_COLOR)"
	@printf "\a"

clean::
	rm -f *.elf $(PYTHON_SRC)*.mpy *.orig config_io_o.hex

