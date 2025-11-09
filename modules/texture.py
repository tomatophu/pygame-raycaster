from numbers import Real
from typing import Self

import pygame as pg


_FALLBACK_SURF = pg.Surface((2, 2))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(1, 0, 1, 1))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(0, 1, 1, 1))


class WallTexture(object):
    def __init__(self: Self, obj: pg.Surface | str) -> None:
        surf = obj
        if isinstance(obj, str):
            try:
                surf = pg.image.load(obj)
            except FileNotFoundError:
                surf = _FALLBACK_SURF
        self._surf = surf
        self._lines = []
        self._width = surf.width
        height = surf.height
        for i in range(self._width):
            line = pg.Surface((1, height))
            line.blit(surf, (0, 0), area=pg.Rect(i, 0, 1, height))
            self._lines.append(line.convert())

    def __getitem__(self: Self, dex: int) -> pg.Surface:
        return self._lines[dex]
    
    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def width(self: Self) -> Real:
        return self._width


# Level of abstraction for modding
class FloorTexture(object):
    def __init__(self: Self, obj: pg.Surface | str) -> None:
        surf = obj
        if isinstance(obj, str):
            try:
                surf = pg.image.load(obj)
            except FileNotFoundError:
                surf = _FALLBACK_SURF
        self._surf = surf
        self._size = surf.size
        self._array = pg.surfarray.array3d(surf)
    
    def __getitem__(self: Self, dex: object):
        return self._array[dex]

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def width(self: Self) -> Real:
        return self._size[0]

    @property
    def height(self: Self) -> Real:
        return self._size[1]
    

