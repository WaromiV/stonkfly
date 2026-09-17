"""Render observations into an RGB chart; never reads future prices or P&L."""

import numpy as np
from PIL import Image, ImageDraw


def market_frame(product, history, bid, ask, account=None, candles=None):
    im = Image.new("RGB", (320, 180), (235, 240, 249))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 319, 27), fill=(19, 36, 71))
    d.text((9, 8), product, fill=(219, 229, 249))
    if candles:
        d.text((264, 8), "1 MIN", fill=(219, 229, 249))
    top, bottom = (94 if account else 34), 160
    for x in range(12, 310, 30):
        d.line((x, top, x, bottom), fill=(200, 212, 233))
    for y in range(top + 4, bottom + 2, 24):
        d.line((10, y, 308, y), fill=(200, 212, 233))
    values = np.asarray(history[-100:], dtype=float)
    if candles:
        bars = candles[-100:]
        low, high = min(float(c["low"]) for c in bars), max(float(c["high"]) for c in bars)
        span = max(high - low, float(bid) * .002)
        lo, span = low - span * .12, span * 1.24
        y = lambda v: bottom - 7 - (float(v) - lo) / span * (bottom - top - 17)
        for i, candle in enumerate(bars):
            x = 12 + i * 294 / max(1, len(bars) - 1)
            color = (0, 101, 183) if float(candle["close"]) >= float(candle["open"]) else (197, 37, 78)
            d.line((x, y(candle["low"]), x, y(candle["high"])), fill=color)
            a, b = sorted((y(candle["open"]), y(candle["close"])))
            d.rectangle((x - 1, a, x + 1, max(a + 1, b)), fill=color)
    elif len(values):
        span = max(float(np.ptp(values)), float(np.mean(values)) * 0.002)
        lo = float(values.min()) - span * 0.12
        span *= 1.24
        points = [
            (12 + i * 294 / max(1, len(values) - 1), bottom - 7 - (v - lo) / span * (bottom - top - 17))
            for i, v in enumerate(values)
        ]
        if len(points) > 1:
            for a, b in zip(points, points[1:]):
                d.line(
                    (*a, *b),
                    fill=(0, 101, 183) if b[1] <= a[1] else (197, 37, 78),
                    width=3,
                )
        for x, y in points:
            d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(27, 39, 81))
    d.text((9, bottom + 5), f"BID {bid}  ASK {ask}"[:50], fill=(28, 46, 82))
    if account:
        # Broad bars/blocks are sampled by the existing eyes; text is for humans.
        # No claim that the fly reads labels or understands currencies.
        # The upper band intersects both eyes' actual retained projection.
        # Lower-left screen regions have almost no retained R1-R6 samples.
        d.rectangle((0, 28, 319, 88), fill=(18, 24, 34))
        for x, key, label in [(8, "cash_fraction", "CASH"), (164, "inventory_fraction", "HELD")]:
            fraction = min(1.0, max(0.0, float(account[key])))
            d.text((x, 29), label, fill=(230, 230, 230))
            d.rectangle((x, 42, x + 146, 57), fill=(40, 46, 54))
            if fraction > 0:
                d.rectangle((x, 42, x + max(0, round(146 * fraction) - 1), 57), fill=(240, 240, 240))
        previous = account["previous_execution"]
        for x, side in [(8, "BUY"), (164, "SELL")]:
            affordable = account[side.lower() + "_affordable"]
            d.rectangle((x, 63, x + 64, 83), fill=(225, 225, 225) if affordable else (45, 45, 45))
            d.text((x + 4, 68), side, fill=(10, 10, 10) if affordable else (150, 150, 150))
            # A separate outcome block for each side: gray unknown/other, cyan
            # filled, red rejected. Position/brightness also carry the cue.
            color = (45, 45, 45)
            if previous and previous["side"] == side:
                if previous["status"] == "FILLED":
                    color = (80, 210, 230)
                elif previous["status"] == "VETO":
                    color = (240, 90, 80)
            d.rectangle((x + 72, 63, x + 146, 83), fill=color)
    return np.asarray(im, dtype=np.uint8)
