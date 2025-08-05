import curses
import random

from math_utils import *
from entity import *

class Level:
    def __init__(self, size:tuple[int, int]=(300,200)) -> int:
        self.size: tuple[int, int] = size
        self.data: list[tuple[str, int]] = [('.', 0) for _ in range(self.size[0] * self.size[1])]
        self.seen: list[bool] = [False for _ in range(self.size[0] * self.size[1])]
        self.entities: list[Entity] = []

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                dist = distance(x / self.size[0], y / self.size[1], 0.5, 0.5)
                if dist > 0.45 and pow(random.random(), 2) < (dist - 0.45) * 20:
                    self.set_at(x, y, 'T', 2)

    def get_at(self, x, y) -> tuple[str, int]:
        return self.data[y * self.size[0] + x]

    def set_at(self, x, y, char, color) -> None:
        if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
            self.data[y * self.size[0] + x] = (char, color)

    def draw(self, vis, stdscr, ox, oy, cam_x, cam_y, gamesize=(78,22)):
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                if 0 <= y - cam_y < gamesize[1] and 0 <= x - cam_x < gamesize[0]:
                    if self.seen[y * self.size[0] + x]:
                        if vis[y * self.size[0] + x]:
                            char, color = self.get_at(x, y)
                        else:
                            char, color = self.get_at(x, y)[0], 3
                    else:
                        char, color = ' ', 0
                    stdscr.addch(oy + 1 + y - cam_y, ox + 1 + x - cam_x, char, curses.color_pair(color))