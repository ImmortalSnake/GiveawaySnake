from datetime import timedelta
import re

from discord.ext import commands


def friendly_duration(td: timedelta, long=False) -> str:
    """
    Returns a friendly readable duration string from a timedelta object
    Example:
    - friendly_duration(timedelta(days=2, hours=4)) -> 2d 4h
    - friendly_duration(timedelta(seconds=3600)) -> 1h
    - friendly_duration(timedelta(seconds=864000), long=True) -> 10 days
    """
    seconds, days = td.seconds, td.days

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    words = [' days', ' hours', ' minutes', ' seconds'] if long else ['d', 'h', 'm', 's']
    return ' '.join(f'{num}{word}' for (num, word) in zip([days, hours, minutes, seconds], words) if num > 0)


regex = re.compile(r'(?:(\d+) *(s|m|h|d))+?')
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
