import curses
import random

class Entity:
    def __init__(self, x, y, health, name, description, char, color, solid=True, seethrough=False, detectable=True):
        self.x = x
        self.y = y
        self.health = self.max_health = health
        self.name = name
        self.description = description
        self.char = char
        self.color = color
        self.solid = solid
        self.seethrough = seethrough
        self.detectable = detectable

        self.marked_for_death = False
    
    def draw(self, level, current_vis, stdscr, ox, oy, cam_x, cam_y, gamesize=(78,22)):
        if 0 <= self.y - cam_y < gamesize[1] and 0 <= self.x - cam_x < gamesize[0]:
            if level.seen[self.y * level.size[0] + self.x]:
                if current_vis[self.y * level.size[0] + self.x]:
                    char, color = self.char, self.color
                else:
                    # entities that have been seen, but are not
                    # actively visible, are drawn in blue
                    if self.detectable:
                        char, color = self.char, 3
                    else:
                        char, color = level.get_at(self.x, self.y)[0], 3
            else:
                char, color = ' ', 0
            stdscr.addch(oy + 1 + self.y - cam_y, ox + 1 + self.x - cam_x, char, curses.color_pair(color))
    
    def on_bump_interact(self, player):
        pass

    def on_pass_over(self, player):
        pass

    def on_my_turn(self, player):
        pass

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 10, "You", "Yourself.", "@", random.randint(1, 6))

        self.food = self.max_food = 10
        self.water = self.max_water = 10

        self.sight_radius = 6
        self.noise = 5
    
        self.action = "move"

class Door(Entity):
    def __init__(self, x, y, locked=None):
        super().__init__(x, y, 5, "Wooden Door", "A simple wooden door.", "+", 1)
        self.open = False
        self.locked = random.random() < 0.8 if locked is None else locked

    def on_bump_interact(self, player):
        if player.action == "attack":
            dmg = random.randint(2, 3)
            old_health = self.health
            self.health = max(0, self.health - dmg)
            if self.health == 0:
                self.marked_for_death = True
                return f"You `rbreak down` the `g{self.name}`."
            return f"You deal `y{old_health - self.health}` damage to the `g{self.name}`."
        if self.locked:
            return "It's locked."
        self.open = True
        self.solid = False
        self.seethrough = True
        self.char = "/"
    
class Window(Entity):
    def __init__(self, x, y, locked=None):
        super().__init__(x, y, 5, "Window", "A window.", "=", 5, True, True)
        self.open = False
        self.broken = False
        self.locked = random.random() < 0.8 if locked is None else locked

    def on_bump_interact(self, player):
        if player.action == "attack":
            dmg = random.randint(2, 3)
            old_health = self.health
            self.health = max(0, self.health - dmg)
            if self.health == 0:
                self.broken = True
                self.char = 'X'
                self.solid = False
                return f"You `rbreak` the `g{self.name}`."
            return f"You deal `y{old_health - self.health}` damage to the `g{self.name}`."
        if self.locked:
            return "It's locked."
        if self.broken:
            return "This message shouldn't have shown up."
        self.open = True
        self.solid = False
        self.char = "'"
    
    def on_pass_over(self, player):
        if self.broken:
            if random.random() < 0.8:
                player.health = max(0, player.health - 2)
                return "You get cut by the broken glass."
            return "You pass through the window safely."

class Corpse(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 8, "Corpse", "A person's corpse.", "&", 0, True, True, False)