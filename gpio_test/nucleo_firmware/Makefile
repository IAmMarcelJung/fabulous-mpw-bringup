include ../Makefile.common
# Definition for the directory of this Makefile
#

# Definitions used for device interaction
FLASH := /pyboard/flash/
DEV := $(shell mpremote connect list | grep STLink | cut -f 1 -d ' ')
COPY_CMD := rshell --port $(DEV) cp
LS_CMD := rshell --port $(DEV) ls


PATTERN ?= config_io_o


.PHONY: clean hex copy repl run 


GPIO_CONFIG_DATA := ../gpio_config/gpio_config_data.h


ifeq ($(wildcard ../nucleo_firmware/$(CONFIG_FILE_TARGET)), )
	PREREQUISITES_IF_CONFIG_FILE_TARGET_EXISTS := $(CONFIG_FILE_TARGET)
endif

# Definitions related to python
PYTHON_SRC := src/

PYTHON_FILES := $(wildcard $(PYTHON_SRC)*.py)
MPY_FILES := $(patsubst $(PYTHON_SRC)%.py,$(PYTHON_SRC)%.mpy,$(PYTHON_FILES))



USERNAME := $(shell whoami)
USERNAME_FILE = src/user.py
USERNAME_MPY = src/user.mpy



compile: $(MPY_FILES) $(USERNAME_MPY)

$(USERNAME_FILE):
	echo "USER = '$(USER)'" > $@

$(USERNAME_MPY): $(USERNAME_FILE)
	mpy-cross $<
	$(COPY_CMD) $@ $(FLASH)

$(PYTHON_SRC)%.mpy: $(PYTHON_SRC)%.py
	mpy-cross $<
	$(COPY_CMD) $@ $(FLASH)

# runs script from the local filesystem
reset: check-device
	mpremote connect $(DEV) exec "import machine; machine.reset()"

# runs script from the local filesystem
version: check-device
	mpremote connect $(DEV) exec "import io_config; io_config.version()"

# run io_config test to characterize a new part
run: check-device check-part hex F746ZG-copy
	mpremote connect $(DEV) exec "import io_config; io_config.run('$(PART)', $(VOLTAGE))"

# copy the definition file for a part after running io_config
get_config: check-device
	mpremote cp :$(CONFIG_FILE_PATTERN).py .

# run a sanity check using the gpio_config_def.py file on the nucleo
sanity_check: check-device hex
ifndef CONFIG_FILE
	$(error CONFIG_FILE is undefined, please export it before running make flash)
else
	$(COPY_CMD) $(CONFIG_FILE) $(FLASH)$(CONFIG_FILE_PATTERN).py
	$(COPY_CMD) config_io_o.hex $(FLASH)
	sync
	sleep 2
	mpremote connect $(DEV) exec "import io_config; io_config.run_sanity_check()"
	mpremote rm :config_io_o.hex
endif

# power up the caravel hat while mounted to Nucleo
poweron: check-device
	mpremote connect $(DEV) exec "import io_config; io_config.run_poweron($(VOLTAGE))"

change_power: check-device
	mpremote connect $(DEV) exec "import io_config; io_config.run_change_power($(VOLTAGE))"

# flash firmware on caravel hat while mounted to Nucleo
flash: check-device
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
F746ZG:
	st-flash --connect-under-reset --format ihex write F746ZG_firmware.hex
	make F746ZG-copy

F413ZH:
	st-flash --connect-under-reset --format ihex write F413ZH_firmware.hex
	sleep 7
	make F413ZH-copy

# copies scripts to nucleo
copy2 F746ZG-copy: compile check-device hex
	$(COPY_CMD) config_io_o.hex $(FLASH)
	sync
	$(LS_CMD) $(FLASH)
	echo "File sytem usage"
	mpremote df

copy3 F413ZH-copy: compile check-device hex
	$(COPY_CMD) config_io_o.hex $(FLASH)
	sync
	$(LS_CMD)
	echo "File sytem usage"
	mpremote df

check-python:
ifeq ($(shell which python3),)
$(error Please install python 3.6+)
endif



store_config_file: check-part
		cp $(CONFIG_FILE_PATTERN).py $(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)/$(PART_OUTPUT_FILE)

$(CONFIG_FILE_TARGET): | run get_config $(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR)

$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR):
	mkdir -p $@


.SUFFIXES:

hex: $(PATTERN:=.hex)

%.elf: %.c $(BITSTREAM_HEADER) $(LDSCRIPT) ../riscv_firmware_src/crt0_vex.S $(GEN_CONFIG_HEADER_PREREQUISITE)
	@echo
	@echo "Compiling firmware."
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-gcc $(INCLUDES) $(CFLAGS) $(LDFLAGS) -o $@ $(SRC_FILES) $<
	@echo "$(GREEN)Done compiling firmware.$(RESET_COLOR)"

%.hex: %.elf
	@echo "Converting $< to $@"
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-objcopy -O verilog $< $@
	$(SED_CMD) 's/@1000/@0000/g' $@
	$(STRIP)
	@echo "$(GREEN)Done converting $< to $@.$(RESET_COLOR)"


run_and_store_config: |$(CONFIG_FILES_DIR)/$(PART_OUTPUT_DIR) store_config_file
run_and_store_config: $(CONFIG_FILE_TARGET)
	@echo "$(GREEN)Executed GPIO test and stored config file to $(CONFIG_FILE_TARGET).$(RESET_COLOR)"
	@printf "\a"

clean::
	rm -f *.elf $(PYTHON_SRC)*.mpy *.orig config_io_o.hex

