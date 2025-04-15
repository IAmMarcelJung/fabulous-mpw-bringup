include ../Makefile.common

# These need to be defined before including the Makefile
# to set the values defined here in the included Makefile
FILE_PATTERN := gpio_config_firmware_$(SHUTTLE)
FIRMWARE_FILE ?= $(FILE_PATTERN).hex
BITSTREAM_FILE := $(CWD)../../output_files/bitstream.bin
BITSTREAM_HEADER := $(CWD)../firmware_helpers/bitstream/bitstream.h
GPIO_CONFIG_DATA := $(CWD)../gpio_config/gpio_config_data.h
DONT_STRIP_HEX_FILE := true
BITSTREAM_CONVERSION_COMMAND := bin2header
CONFIG_FILES_DIR := ../nucleo_firmware/gpio_config_files

$(BITSTREAM_HEADER): $(BITSTREAM_FILE)
	@if ! command -v $(BITSTREAM_CONVERSION_COMMAND) > /dev/null; then \
			echo "$(RED)Error: $(BITSTREAM_CONVERSION_COMMAND) not installed.$(RESET_COLOR)"; \
			echo "Get it from: https://github.com/AntumDeluge/bin2header?tab=readme-ov-file"; \
			exit 1; \
	fi
	@if [ ! -f "$(BITSTREAM_FILE)" ]; then \
		echo "$(RED)Bitstream file $(BITSTREAM_FILE) does not exist. Please create it using FABulous.$(RESET_COLOR)"; \
		exit 1; \
	fi
	@echo "Converting bitstream..."
	$(BITSTREAM_CONVERSION_COMMAND) -o $@ -n bitstream $(BITSTREAM_FILE)
	@echo "$(GREEN)Done converting bitstream from binary to header file.$(RESET_COLOR)"

gen_config_header: $(GPIO_CONFIG_DATA)

$(GPIO_CONFIG_DATA): | check-params
	@echo "Building configuration data."
	# python3 ../gpio_config/gpio_config_builder.py
	VOLTAGE=$(VOLTAGE) PART=$(PART) python3 ../gpio_config/gpio_config_builder.py
	mv gpio_config_data.h $@
	@echo "$(GREEN)Done building configuration data.$(RESET_COLOR)"

# Target to build the Caravel firmware
hex: $(PATTERN:=.hex)

%.elf: %.c $(BITSTREAM_HEADER) $(LDSCRIPT) ../riscv_firmware_src/crt0_vex.S  $(GPIO_CONFIG_DATA)
	@echo
	@echo "Compiling firmware."
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-gcc $(INCLUDES) $(CFLAGS) $(LDFLAGS) -o $@ $(SRC_FILES) $<
	@echo "$(GREEN)Done compiling firmware.$(RESET_COLOR)"

%.hex: %.elf
	@echo
	@echo "Converting $< to $@"
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-objcopy -O verilog $< $@
	$(SED_CMD) 's/@1000/@0000/g' $@
	# $(STRIP)
	@echo "$(GREEN)Done converting $< to $@.$(RESET_COLOR)"

%.bin: %.elf
	$(TOOLCHAIN_PATH)$(TOOLCHAIN_PREFIX)-objcopy -O binary $< $@

flash_caravel: check-params $(FIRMWARE_FILE) $(BITSTREAM_FILE)
	@echo
	@echo "Start flashing Caravel."
	python3 ../util/caravel_hkflash.py  $(FIRMWARE_FILE)
	@echo "$(GREEN)Done flashing Caravel.$(RESET_COLOR)"

check: check-params gpio_config_def.py gpio_config_io.py gen_config_header
	@echo
	@echo "Checking GPIO configuration."
	python3 ../gpio_config/gpio_config_checker.py
	@echo "$(GREEN)Done checking GPIO configuration.$(RESET_COLOR)"

gpio_sim: check-params gen_config_header
	@echo
	@echo "Simulating GPIO configuration."
	VOLTAGE=$(VOLTAGE) PART=$(PART) python3 ../gpio_config/gpio_config_simulator.py

clean:
	rm -f *.hex *.bin *.vvp *.orig $(GPIO_CONFIG_DATA) $(CONFIG_FILE)

.PHONY: clean all gen_config_header $(GPIO_CONFIG_DATA)
