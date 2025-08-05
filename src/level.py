import curses
import random

from math_utils import *
from entity import *

class Level:
    def __init__(self, size:tuple[int, int]=(200,100)) -> int:
        self.size: tuple[int, int] = size
        self.data: list[tuple[str, int]] = [('.', 0) for _ in range(self.size[0] * self.size[1])]
        self.seen: list[bool] = [False for _ in range(self.size[0] * self.size[1])]
        self.entities: list[Entity] = []

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                dist = distance(x / self.size[0], y / self.size[1], 0.5, 0.5)
                if dist > 0.45 and pow(random.random(), 2) < (dist - 0.45) * 20:
                    self.set_at(x, y, 'T', 2)

        self.entities.append(Player(self.size[0] // 2, self.size[1] // 2))
        
        def add_building(center):
            rect = (
                random.randint(center[0] - 3, center[0] + 3),
                random.randint(center[1] - 3, center[1] + 3),
                random.randint(9, 15),
                random.randint(5, 8)
            )

            ext_positions: list[tuple[int, int]] = []

            for x in range(rect[0], rect[0] + rect[2] + 1):
                if x == rect[0] + rect[2] // 3 or x == rect[0] + int(rect[2] * (2 / 3)):
                    ext_positions.append((x, rect[1]))
                    ext_positions.append((x, rect[1] + rect[3]))
                else:
                    self.set_at(x, rect[1], '#', 0)
                    self.set_at(x, rect[1] + rect[3], '#', 0)
            for y in range(rect[1], rect[1] + rect[3] + 1):
                if y == rect[1] + rect[3] // 3 or y == rect[1] + int(rect[3] * (2 / 3)):
                    ext_positions.append((rect[0], y))
                    ext_positions.append((rect[0] + rect[2], y))
                else:
                    self.set_at(rect[0], y, '#', 0)
                    self.set_at(rect[0] + rect[2], y, '#', 0)
            
            random.shuffle(ext_positions)
            for i, pos in enumerate(ext_positions):
                if i <= 1:
                    # place 2 doors on the outside of each house
                    self.entities.append(Door(*pos))
                elif random.random() < 0.5:
                    # randomly place windows
                    self.entities.append(Window(*pos))

                    if random.random() < 0.1:
                        # 10% chance for the window to be broken
                        window = self.entities[-1]
                        window.broken = True
                        window.char = 'X'
                        window.solid = False
                else:
                    self.set_at(*pos, '#', 0)
        
            rx = random.randint(rect[0] + 1, rect[0] + rect[2] - 2)
            ry = random.randint(rect[1] + 1, rect[1] + rect[3] - 2)

            if self.get_at(rx, ry)[0] == '.':
                self.entities.append(Corpse(rx, ry))

        building_density = 4

        for i in range(building_density):
            for j in range(building_density):
                x = (i + 1) * (self.size[0] // (building_density + 1))
                y = (j + 1) * (self.size[1] // (building_density + 1))

                add_building((x, y))

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
                            # tiles that have been seen, but are not
                            # actively visible, are drawn in blue
                            char, color = self.get_at(x, y)[0], 3
                    else:
                        char, color = ' ', 0
                    stdscr.addch(oy + 1 + y - cam_y, ox + 1 + x - cam_x, char, curses.color_pair(color))