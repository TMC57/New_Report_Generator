import time

def date_tsd(date_to_convert, format):
    newdate = date_to_convert = int(time.mktime(time.strptime(date_to_convert, format))) * 1000
    return(newdate)