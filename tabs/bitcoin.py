from context import Screen, ScreenContext
from tab import Tab

from utils import format_timespan

import sys
import time
import urllib2
import httplib
import json
import random
import pyjsonrpc
import socket

class Bitcoind(Tab):
    def __init__(self, config):
        self.title = "bitcoind stats"
        
        self.CONNECTION_YELLOW_THRESHOLD = 4
        self.CONNECTION_GREEN_THRESHOLD = 9
        
        self.TRANSACTION_PURGE_THRESHOLD = 20000
        
        self.host = config["host"]
        
        self.addrlocal = "N/A"
        
        self.utx_count = 0
        
        # The time since last block or when we started tracking new transactions
        # (eg. on first tab launch)
        self.utx_start_time = -1
        
        self.utx = []
        
        self.utx_since_last_block = 0
        
        self.connections = 0
        self.inbound = 0
        self.outbound = 0
        
        self.difficulty = 1.0
        self.block_count = 0
        
        self.last_block_time = int(time.time())
        
        # Create the JSON-RPC client
        self.client = pyjsonrpc.HttpClient(
            url = config["host"],
            username = config["username"],
            password = config["password"],
            
            timeout = 4
        )
        
        self.error = None
        
    def update_stats(self):
        self.error = None
        
        try:
            blockcount = self.client.getblockcount()
            peers = self.client.getpeerinfo()
            utx = self.client.getrawmempool()
            
            bestblockhash = self.client.getbestblockhash()
            
            latest_block = self.client.getblock(bestblockhash)
        except socket.timeout:
            print "Request timed out, bitcoind probably busy"
            self.error = "Request timed out, bitcoind probably busy"
            return
        except urllib2.URLError as e:
            print "Couldn't connect to bitcoind, error: %s" % e
            self.error = e
            return
        
        if 'error' in peers or \
           'error' in utx or \
           'error' in latest_block:
            print "Error in response, skipping"
        else:
            # If there are too many transactions in the memory,
            # clear the list entirely and start from scratch
            if len(self.utx) >= self.TRANSACTION_PURGE_THRESHOLD:
                self.utx = []
                self.utx_start_time = -1
                self.utx_since_last_block = 0
            
            if self.block_count != blockcount:
                self.utx_since_last_block = 0
                
                if self.utx_start_time != -1:
                    self.utx_start_time = int(time.time())
                
            self.block_count = blockcount
        
            self.connections = 0
            self.inbound = 0
            self.outbound = 0
            
            for peer in peers:
                if peer['inbound']:
                    self.inbound += 1
                else:
                    self.outbound += 1
                    
                self.connections += 1
                
                if 'addrlocal' in peer:
                    self.addrlocal = peer['addrlocal']
                
            self.utx_count = len(utx)
            
            # Add new transactions
            for tx in utx:
                if tx not in self.utx:
                    self.utx.append(tx)
                    
                    if self.utx_start_time != -1:
                        self.utx_since_last_block += 1
            
            self.last_block_time = latest_block['time']
            
            for tx in latest_block['tx']:
                if tx in self.utx:
                    self.utx.remove(tx)
                    
            # If this is the first time we ever fetched the transactions,
            # set the current time as the starting point for calculating tx/s
            if self.utx_start_time == -1:
                self.utx_start_time = int(time.time())
    
    def render_tab(self, ctx):
        self.update_stats()
        
        if self.error:
            ctx.fg_color(Screen.RED).write_line(str(self.error)).fg_color(Screen.WHITE)
            return
        
        ctx.bg_color(Screen.BLACK).fg_color(Screen.YELLOW).write_line(self.host.replace("http://", "")).linebreak()
        
        ctx.fg_color(Screen.WHITE).write("Connections: ")
        
        if self.connections < self.CONNECTION_YELLOW_THRESHOLD:
            ctx.fg_color(Screen.RED)
        elif self.connections >= self.CONNECTION_YELLOW_THRESHOLD and self.connections <= self.CONNECTION_GREEN_THRESHOLD:
            ctx.fg_color(Screen.YELLOW)
        else:
            ctx.fg_color(Screen.GREEN)
        
        ctx.write_line(str(self.connections))
        ctx.fg_color(Screen.WHITE).write("    inbound: ").fg_color(Screen.YELLOW).write_line(str(self.inbound))
        ctx.fg_color(Screen.WHITE).write("   outbound: ").fg_color(Screen.YELLOW).write_line(str(self.outbound)).linebreak()
        
        ctx.fg_color(Screen.WHITE).write("Blocks: ").fg_color(Screen.YELLOW).write_line(str(self.block_count))
        ctx.fg_color(Screen.WHITE).write("Unconf. tx: ").linebreak().fg_color(Screen.YELLOW).write(str(self.utx_count))
        
        current_time = int(time.time())
        time_since_start = current_time - self.utx_start_time
        
        if time_since_start != 0:
            tx_per_second = float(self.utx_since_last_block) / float(time_since_start)
        else:
            tx_per_second = 0.0
            
        time_since_block = current_time - self.last_block_time
        
        ctx.write_line(" (%.2f tx/s)" % tx_per_second).fg_color(Screen.WHITE)
        
        ctx.write_line("Time since block: ").fg_color(Screen.YELLOW).write_line(format_timespan(time_since_block))
        
class BitcoinPrice(Tab):
    def __init__(self):
        self.title = "Bitcoin price"
        
        self.last = 0.0
        
        self.high = 0.0
        self.low = 0.0
        
        self.UPDATE_INTERVAL = 120
        self.last_update = 0
        
    def update_price(self):
        current_time = time.time()
        
        if current_time >= self.last_update + 60:
            # Update value
            try:
                response = urllib2.urlopen("https://www.bitstamp.net/api/ticker/").read()
                response = json.loads(response)
            except urllib2.URLError, ValueError:
                # Either the ticker data couldn't be retrieved or JSON couldn't be parsed
                return
            
            self.last = float(response["last"])
            self.high = float(response["high"])
            self.low = float(response["low"])
            
            self.last_update = current_time
        
    def render_tab(self, ctx):
        # Update price if it hasn't been updated in the last 10 minutes
        self.update_price()
        
        ctx.set_text_size(3).bg_color(Screen.BLACK).write("Last ").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.last).linebreak()
        
        ctx.fg_color(Screen.WHITE).write("24hr high").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.high)
        ctx.fg_color(Screen.WHITE).write("24hr low").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.low)
        
        ctx.set_text_size(2)