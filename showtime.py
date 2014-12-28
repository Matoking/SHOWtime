#!/usr/bin/env python

from context import Screen, ScreenContext
import config

# Import tabs here
from tabs.bitcoin import Bitcoind, BitcoinPrice
from tabs.sysinfo import SystemStats, DiskUsage

from header import Header

import atexit
import time
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--tab", "-t", help="start from which tab (default=1)",
                    type=int, default=1)
parser.add_argument("--time", "-T", 
                    help="for how many seconds should a tab be shown before changing it (default=15)",
                    type=int, default=15)
parser.add_argument("--port", "-p",
                    help="serial port to use as the output (default=/dev/ttyUSB0)",
                    type=str, default="/dev/ttyUSB0")
args = parser.parse_args()

# Apply the arguments
default_tab = args.tab - 1
tab_change_interval = args.time

tabs = config.tabs
current_tab = default_tab

ctx = ScreenContext(args.port)

atexit.register(ctx.cleanup)

# Wait 6 seconds for the screen to boot up before we start uploading anything
ctx.sleep(6).reset_lcd().set_rotation(0)

# Header
header = Header()

print "Started"

time_since_tab_change = 0
last_time = time.time()

while True:
    header.render_header(ctx, current_tab, tabs[current_tab].title, len(tabs))
    tabs[current_tab].render_tab(ctx)
    
    time_since_tab_change += time.time() - last_time
    last_time = time.time()
    
    if time_since_tab_change >= tab_change_interval and len(tabs) > 1:
        time_since_tab_change = 0
        current_tab += 1
        if current_tab > len(tabs)-1:
            current_tab = 0
            
        # Make the erasing maneuver a bit faster by temporarily changing
        # the font size to 4
        ctx.set_text_size(4)
        ctx.erase_rows(1, ctx.get_rows()-1)
        ctx.set_text_size(2)