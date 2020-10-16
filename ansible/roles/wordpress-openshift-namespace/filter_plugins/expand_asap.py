from datetime import datetime, timedelta

def expand_asap(date):
    """Add 2 minutes to crontab if date == asap"""
    if date == 'asap':
        return (datetime.now() + timedelta(minutes=1)).strftime("%M %H * * *")
    else:
        return date

class FilterModule(object):
    def filters(self):
        return {
            'expand_asap': expand_asap
        }
