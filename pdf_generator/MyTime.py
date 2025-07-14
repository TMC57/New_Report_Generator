import time

def date_milli(date_to_convert, format):
    newdate = date_to_convert = int(time.mktime(time.strptime(date_to_convert, format))) * 1000
    return(newdate)