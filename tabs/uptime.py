from context import Screen, ScreenContext
from tab import Tab

import urllib2
import time

from utils import format_timespan

class WebsiteUptime(Tab):
    def __init__(self, config):
        self.title = "Website uptime"
        
        self.websites = config["websites"]
        
        # Websites' uptime status as a bool
        self.website_status = {}
        
        # Timestamps of when websites went down
        self.downtime = {}
            
        # Timestamp of the last update
        self.last_update = 0
        
        for website in self.websites:
            self.downtime[website["name"]] = -1
        
    def update_uptime(self):
        current_time = time.time()
        
        if current_time >= self.last_update + 60:
            for website in self.websites:
                # Is the website down?
                down = False
                
                # Try to get a response
                # If we get an exception assume the site is down
                try:
                    response = urllib2.urlopen(website["url"], timeout=5)
                except:
                    down = True
                    
                if not down:
                    self.website_status[website["name"]] = True
                    
                    self.downtime[website["name"]] = -1
                else:
                    self.website_status[website["name"]] = False
                    
                    if self.downtime[website["name"]] == -1:
                        self.downtime[website["name"]] = int(time.time())
                        
            self.last_update = current_time
                    
    def render_tab(self, ctx):
        self.update_uptime()
        
        for website, status in self.website_status.iteritems():
            ctx.fg_color(Screen.WHITE).write_line(website)
            
            if status:
                ctx.fg_color(Screen.GREEN).write_line("UP").linebreak()
            else:
                ctx.fg_color(Screen.RED).write_line("DOWN for %s" % format_timespan(int(time.time() - self.downtime[website]))).linebreak()