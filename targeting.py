"""Convert a bounding box into aim coordinates."""


def bbox_center(bbox):
    """Return the (x, y) pixel center of an (x1, y1, x2, y2) box."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def pan_tilt_offset(target, frame_width, frame_height, invert_pan=False, invert_tilt=False):
    """Return a normalized (pan, tilt) offset from the frame center.

    Each value is in [-1.0, 1.0]:
      pan  -1.0 = left edge,   0.0 = center, +1.0 = right edge
      tilt -1.0 = bottom edge, 0.0 = center, +1.0 = top edge

    Tilt is flipped relative to image y (which grows downward) so that
    positive tilt means "aim up".
    """
    x, y = target
    half_w = frame_width / 2
    half_h = frame_height / 2

    pan = (x - half_w) / half_w
    tilt = (half_h - y) / half_h

    if invert_pan:
        pan = -pan
    if invert_tilt:
        tilt = -tilt

    return (_clamp(pan), _clamp(tilt))


def _clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))
