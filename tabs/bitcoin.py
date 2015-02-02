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
        
        self.host = config["host"]
        
        self.addrlocal = "N/A"
        
        self.utx_count_on_block = -1
        self.utx_count = 0
        
        # The time since last block or when we started tracking new transactions
        # (eg. on first tab launch)
        self.utx_start_time = -1
        
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
            if self.block_count != blockcount:
                self.utx_count_on_block = len(utx)
                
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
            
            # Get the timestamp from the latest block if it's available            
            if 'time' in latest_block:
                self.last_block_time = latest_block['time']
            else:
                self.last_block_time = self.utx_start_time
                    
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
            tx_per_second = float(self.utx_count - self.utx_count_on_block) / float(time_since_start)
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
        
        self.price_data = {"source": "Couldn't update price",
                           "data": {}}
        
        # The price sources are checked starting from the first one
        # until a valid response is received
        self.price_sources = [{"api_url": "https://api.bitcoinaverage.com/ticker/global/USD/",
                               "name": "BitcoinAverage",
                               "data": { "Last": "last",
                                         "Ask": "ask",
                                         "Bid": "bid",
                                         "24h avg": "24h_avg"}},
                              
                              {"api_url": "https://www.bitstamp.net/api/ticker/",
                               "name": "Bitstamp",
                               "data": { "Last": "last",
                                         "High": "high",
                                         "Low": "low",
                                         "24h avg": "vwap"}},]
        
        self.UPDATE_INTERVAL = 120
        self.last_update = 0
        
    def update_price(self):
        current_time = time.time()
        
        if current_time >= self.last_update + 60:
            # Go through all of the available price sources until we have one that works
            for source in self.price_sources:
                try:
                    print "Updating %s" % source["name"]
                    response = urllib2.urlopen(source["api_url"]).read()
                    response = json.loads(response)
                except:
                    # Couldn't retrieve ticker data, proceed to next source in the list
                    print "Couldn't retrieve ticker data from %s, skipping..." % source["name"]
                    continue
                
                self.price_data["source"] = source["name"]
                self.price_data["data"] = {}
                
                for name, key in source["data"].iteritems():
                    self.price_data["data"][name] = float(response[key])
                    
                # Stop updating after the first working result
                break
                
            self.last_update = current_time
        
    def render_tab(self, ctx):
        # Update price if it hasn't been updated in the last 10 minutes
        self.update_price()
        
        # Write the source
        ctx.write_line(self.price_data["source"]).linebreak()
        
        ctx.set_text_size(3)
        
        # Write the data
        for entry, value in self.price_data["data"].iteritems():
            ctx.write_line(entry).fg_color(Screen.YELLOW).write_line("$%.2f" % value).fg_color(Screen.WHITE).linebreak()
        
        #ctx.set_text_size(3).bg_color(Screen.BLACK).write("Last ").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.last).linebreak()
        
        #ctx.fg_color(Screen.WHITE).write("24hr high").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.high)
        #ctx.fg_color(Screen.WHITE).write("24hr low").fg_color(Screen.YELLOW).linebreak().write_line("$%.2f" % self.low)
        
        ctx.set_text_size(2)