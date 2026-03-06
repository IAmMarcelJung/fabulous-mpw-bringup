# number of IO in the configuration stream for each chain
NUM_IO = 19

# defines these values for IO configurations
C_MGMT_OUT = 0
C_MGMT_IN = 1
C_USER_BIDIR = 2
C_DISABLE = 3
C_ALL_ONES = 4
C_USER_BIDIR_WPU = 5
C_USER_BIDIR_WPD = 6
C_USER_IN_NOPULL = 7
C_USER_OUT = 8
C_MGMT_HIGH_Z_STRONG_0_DISABLE_OUTPUT = 9
C_MGMT_HIGH_Z_STRONG_0 = 10

config_h = [
    C_DISABLE,  # 37
    C_DISABLE,  # 36
    C_DISABLE,  # 35
    C_DISABLE,  # 34
    C_DISABLE,  # 33
    C_DISABLE,  # 32
    C_DISABLE,  # 31
    C_DISABLE,  # 30
    C_DISABLE,  # 29
    C_DISABLE,  # 28
    C_DISABLE,  # 27
    C_USER_BIDIR_WPU,  # 26 - io 9
    C_USER_BIDIR_WPU,  # 25 - io 8
    C_USER_BIDIR_WPU,  # 24 - io 7
    C_USER_BIDIR_WPU,  # 23 - io 6
    C_USER_BIDIR_WPU,  # 22 - io 5
    C_USER_BIDIR_WPU,  # 21 - io 4
    C_USER_BIDIR_WPU,  # 20 - io 3
    C_USER_BIDIR_WPU,  # 19 - io 2
]

del config_h[NUM_IO:]

config_l = [
    C_ALL_ONES,  # 0
    C_MGMT_IN,  # 1 - CLK_SEL_0
    C_MGMT_IN,  # 2 - CLK_SEL_1
    C_MGMT_IN,  # 3 - s_clk
    C_MGMT_IN,  # 4 - s_data
    C_MGMT_IN,  # 5 - Rx
    C_MGMT_IN,  # 6 - Receive LED
    C_MGMT_IN,  # 7 - Fetch enable
    C_MGMT_IN,  # 8 - ICESOC UART Rx
    C_MGMT_IN,  # 9 - ICESOC UART to mem Rx
    C_MGMT_IN,  # 10 - ICESOC UART Tx
    C_MGMT_IN,  # 11 - ICESOC UART to mem Tx
    C_MGMT_IN,  # 12 - ICESOC Error UART to mem
    C_DISABLE,  # 13 - Unused
    C_DISABLE,  # 14 - Unused
    C_DISABLE,  # 15 - Unused
    C_MGMT_IN,  # 16 - ICESOC eFPGA Write Strobe 2
    C_USER_BIDIR_WPU,  # 17 - io 0
    C_USER_BIDIR_WPU,  # 18 - io 1
]

del config_l[NUM_IO:]
