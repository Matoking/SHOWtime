def format_timespan(seconds):
    seconds = int(seconds)
    
    if seconds == 0:
        return "0s"
    
    time_units = ({"divider": 1, "unit": 's'},
                  {"divider": 60, "unit": 'm'},
                  {"divider": 60*60, "unit": 'h'},
                  {"divider": 60*60*24, "unit": 'D'},
                  {"divider": 60*60*24*7, "unit": 'W'},
                  {"divider": 60*60*24*7*52, "unit": 'Y'})

    time_str = ""
    
    for unit in reversed(time_units):
        if seconds >= unit['divider']:
            count = int(seconds / unit['divider'])
            seconds %= unit['divider']
            time_str += "%d%s " % (count, unit['unit'])
            
    return time_str

def get_progress_bar(length, percent):
    bar = ""
    count = int(percent * (length))
    
    for i in range(0, length):
        if float(float(i) / float(length)) <= percent:
            bar += "|"
        else:
            bar += " "
            
    return bar

def split_string_into_chunks(string, length=25):
    """
    Split string into chunks of defined size
    """
    if len(string) <= length:
        return [ string ]
    else:
        return (string[0+i:length+i] for i in range(0, len(string), length))