from __future__ import division

import Numeric as num
from Scientific.Geometry.VectorModule import Vector

def overshootPath(pts):
    result = []
    for i in range(1, len(pts)-1):
        p2 = pts[i]
        back = 0
        i2 = i
        while back < 40 and i2 > 0:
            back += Vector(pts[i2 + 1] - pts[i2]).length()
            i2 -= 1
        p0 = pts[i2]

        back = 0
        i2 = i
        while back < 25 and i2 > 0:
            back += Vector(pts[i2 + 1] - pts[i2]).length()
            i2 -= 1
        p1 = pts[i2]

        f = 1
        d = 5
        p = -f/d * p0 + -(f*2)/d * p1 + (d + f * 3)/d * p2

        result.append(num.array([p[0], p[1]]))

    nearPts = num.concatenate((pts[:15], pts[-15:]))
    inner = sum(nearPts) / len(nearPts)

    result = [inner] + result[-2:] + result + result[:7]

        
    return result
