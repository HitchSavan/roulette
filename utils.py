"""Utility module"""


def interpolate(x, in_min, in_max, out_min, out_max) -> float:
    """Analog of the `numpy.interp`"""

    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)


def angle_to_sector(angle: float, sectors_amount: int) -> int:
    """Converts angle in degrees to sector number"""

    return int((360 - angle) / (360 / sectors_amount)) % sectors_amount
