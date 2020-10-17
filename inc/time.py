from time import gmtime, strftime
from datetime import datetime, timedelta, timezone

readable_time_format = "%Y-%m-%d %H:%M:%S"

def relative_time(date, lang = 'en'):
    """Take a datetime and return its "age" as a string.
    https://jonlabelle.com/snippets/view/python/relative-time-in-python
 
    The age can be in second, minute, hour, day, month or year. Only the
    biggest unit is considered, e.g. if it's 2 days and 3 hours, "2 days" will
    be returned.
 
    Make sure date is not in the future, or else it won't work.
    """

    def formatn(n, s):
        """Add "s" if it's plural"""
        if n < 2:
            return "1 %s" % s
        elif n >= 2:
            if lang == 'es' and s == 'mes':
                return "%d %ses" % (n, s)
            else:
                return "%d %ss" % (n, s)

    def qnr(a, b):
        """Return quotient and remaining"""

        return a / b, a % b

    class FormatDelta:

        def __init__(self, dt):
            now = datetime.now(timezone.utc)
            delta = now - dt
            self.day = delta.days
            self.second = delta.seconds
            self.year, self.day = qnr(self.day, 365)
            self.month, self.day = qnr(self.day, 30)
            self.hour, self.second = qnr(self.second, 3600)
            self.minute, self.second = qnr(self.second, 60)

        def format(self):
            if lang == 'es':
                for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
                    n = getattr(self, period)
                    
                    if period == 'year':
                        period_trad = 'año'
                    if period == 'month':
                        period_trad = 'mes'
                    if period == 'day':
                        period_trad = 'día'
                    if period == 'hour':
                        period_trad = 'hora'
                    if period == 'minute':
                        period_trad = 'minuto'
                    elif period == 'second':
                        period_trad = 'segundo'

                    if n > 0:
                        return 'hace {0}'.format(formatn(n, period_trad))
                return "justo ahora"
            else:
                for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
                    n = getattr(self, period)
                    if n > 0:
                        return '{0} ago'.format(formatn(n, period))
                return "just now"

    return FormatDelta(date).format()


def readable_log_time(dt, lang='en'):
    return "{}, {}".format(
        dt.astimezone().strftime(readable_time_format),
        relative_time(dt, lang))
