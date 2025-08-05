import curses
import random

class Entity:
    def __init__(self, x, y, health, name, description, char, color, solid=True):
        self.x = x
        self.y = y
        self.health = self.max_health = health
        self.name = name
        self.description = description
        self.char = char
        self.color = color
        self.solid = solid
    
    def draw(self, stdscr, ox, oy, cam_x, cam_y, gamesize=(78,22)):
        if 0 <= self.y - cam_y < gamesize[1] and 0 <= self.x - cam_x < gamesize[0]:
            stdscr.addch(oy + 1 + self.y - cam_y, ox + 1 + self.x - cam_x, self.char, curses.color_pair(self.color))
    
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 10, "You", "Yourself.", "@", random.randint(1, 6))

        self.food = self.max_food = 10
        self.water = self.max_water = 10

        self.sight_radius = 6