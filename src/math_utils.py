import math

def distance(x1, y1, x2, y2):
    return math.sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2))

def clamp(a, minv, maxv):
    return min(max(minv, a), maxv)