"""
    Time manager that also accounts for daylight savings for MicroPython.
    Utilizes NTP to account for time zone and daylight savings on-the-fly.
    Allows synchronizing the internal RTC to this clock as well.
    
    Functions included:
    is_dst(time_tuple) - Determines if provided time is in US daylight savings
    get_ntp_time() - Retrieves current time from the NTP pool server.
    utc_to_local() - Converts UTC time to local time, and adds DST offset.
    set_local_time() - Syncs RTC to a local time given the time zone.
    
    Utilizing this library fully requires a network connection be established before set_local_time or get_ntp_time is called.
"""

import socket
import struct
import time
import machine

# NTP settings
NTP_DELTA = 2208988800
NTP_HOST = "pool.ntp.org"

# Timezone definitions (Standard UTC offset only)
TIMEZONES = {
    "US/Eastern": -5,
    "US/Central": -6,
    "US/Mountain": -7,
    "US/Pacific": -8,
}

def is_dst(time_tuple):
    """
    Determine if the given localtime tuple is in US daylight saving time.
    
    :param time_tuple: tuple from time.localtime()
    :return: True if DST is active, False otherwise
    """
    year, month, day, hour, *_ = time_tuple

    # Find second Sunday in March
    # March 1st weekday
    import time  # allowed since MicroPython supports it
    march1 = time.mktime((year, 3, 1, 0, 0, 0, 0, 0))
    march1_wday = time.localtime(march1)[6]  # 0=Mon, ..., 6=Sun
    dst_start_day = 14 - march1_wday if march1_wday <= 6 else 7 - (march1_wday - 7)

    # Find first Sunday in November
    nov1 = time.mktime((year, 11, 1, 0, 0, 0, 0, 0))
    nov1_wday = time.localtime(nov1)[6]
    dst_end_day = 1 + (7 - nov1_wday) % 7

    if month < 3 or month > 11:
        return False
    elif 3 < month < 11:
        return True
    elif month == 3:
        if day > dst_start_day:
            return True
        elif day == dst_start_day:
            return hour >= 2
    elif month == 11:
        if day < dst_end_day:
            return True
        elif day == dst_end_day:
            return hour < 2
    return False

def get_ntp_time(host=NTP_HOST):
    """Get UTC time from NTP server."""
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
    except OSError:
        raise RuntimeError("You must be connected to a network to use this function.")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    msg = b'\x1b' + 47 * b'\0'
    try:
        s.sendto(msg, addr)
        msg = s.recv(48)
    except Exception:
        return None
    finally:
        s.close()

    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    return time.gmtime(t)

def utc_to_local(utc_time, tz_offset):
    """Convert UTC to local time with DST adjustment."""
    epoch = time.mktime(utc_time)
    local_epoch = epoch + tz_offset * 3600
    local_time = time.localtime(local_epoch)

    if is_dst(local_time):
        local_time = time.localtime(local_epoch + 3600)

    return local_time

def set_local_time(tz_name):
    """
    Sync internal RTC to local time for the given US timezone name.
    Handles DST automatically.
    """
    if tz_name not in TIMEZONES:
        raise ValueError("Unsupported timezone name (Supported are: US/Eastern, US/Central, US/Mountain, US/Pacific")

    tz_offset = TIMEZONES[tz_name]
    retries = 0
    while retries < 10:
        utc_time = get_ntp_time()
        if utc_time is None:
            print("Failed to get NTP time. Retrying...")
            retries += 1
        else:
            if retries > 0:
                print("Successfully retrieved NTP time on retry.")
            break
           
    if utc_time is None:
        raise RuntimeError("Failed to get NTP time")

    local_time = utc_to_local(utc_time, tz_offset)

    # Set internal RTC to local time
    tm = local_time[:3] + (0,) + local_time[3:6] + (0,)
    machine.RTC().datetime(tm)
    return local_time  # return for confirmation if desired
