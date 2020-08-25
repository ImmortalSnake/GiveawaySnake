from datetime import timedelta
import re

from discord.ext import commands


def friendly_duration(td: timedelta, long=False) -> str:
    """
    Returns a friendly readable duration string from a timedelta object
    Format: %dd %hh %mm %ss
            %d days %h hours %m minutes %s seconds (long)
    """
    seconds = td.seconds

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if long == True:
        return f"{days} days {hours} hours {minutes} minutes {seconds} seconds"

    return f"{days}d {hours}h {minutes}m {seconds}s"



regex = re.compile(r'(?:(\d+)(s|m|h|d))+?')
formats = { 's': 1, 'm': 60, 'h': 3600, 'd': 86400 }

def human_duration(string: str) -> int:
    """
    Parses a duration string into seconds

    - '10s' --> 10
    - '10m10s' --> 610
    """
    matched = regex.findall(string.lower())
    if not matched:
        raise commands.BadArgument("Invalid duration string provided")

    seconds = 0
    for key, value in matched:
        try:
            print(key, value)
            if value in ['days', 'day', 'd']:
                seconds += int(key) * 86400
            elif value in ['hours', 'hour', 'h']:
                seconds += int(key) * 3600
            elif value in ['minutes', 'minute', 'm']:
                seconds += int(key) * 60
            else:
                seconds += int(key)
        except ValueError:
            raise commands.BadArgument("Invalid duration string provided (number)")
        
    return seconds


print(human_duration('10s'))
print(human_duration('10m10s'))
print(human_duration('2d12h'))
print(human_duration('2days'))
print(human_duration('2da'))