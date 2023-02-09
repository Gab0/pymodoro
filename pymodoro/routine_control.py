import datetime

DPD = 4
DAY_START_HOUR = 8
BASE_HOUR = 6


def main(Verbose=True):
    h = datetime.datetime.now()
    hday = h - datetime.timedelta(hours=DAY_START_HOUR)
    h0 = hday.replace(hour=DAY_START_HOUR, minute=0, second=0)

    day = datetime.timedelta(days=1)

    delta = h - h0
    elapsed = max(0, delta.total_seconds() / 3600)

    elapsed_segments = elapsed / 16
    P = elapsed_segments * DPD * 2

    if h.weekday() > 4:
        P = 0
    if Verbose:
        print(f"Expected sessions by now: {P}")
    return P
