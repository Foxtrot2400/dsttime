# dsttime
Time manager that also accounts for daylight savings for MicroPython.
Utilizes NTP to account for time zone and daylight savings on-the-fly.
Allows synchronizing the internal RTC to this clock as well.
    

Functions included:
is_dst(time_tuple) - Determines if provided time is in US daylight savings
get_ntp_time() - Retrieves current time from the NTP pool server.
utc_to_local() - Converts UTC time to local time, and adds DST offset.
set_local_time() - Syncs RTC to a local time given the time zone.
    
Utilizing this library fully requires a network connection be established before set_local_time or get_ntp_time is called.
This library only is designed for use in US-based timezones.
