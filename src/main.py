import curses
import random
import numpy as np

from entity import *
from level import *
from utils import *
from math_utils import *

import tcod.path
import tcod.map

game_name: str = "Hivemind"

def curses_main(stdscr: curses.window) -> None:
    curses.noecho()
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    def set_text(x, y, text, color=0):
        # ignore this garbage ass code
        i = j = 0
        c = color
        cont = True
        for char in text:
            if char == '`':
                if c == color:
                    cont = False
                c = color
                continue
            if cont:
                if char == '\n':
                    j += 1
                    i = 0
                    continue
                stdscr.addch(y + j, x + i, char, curses.color_pair(c))
                i += 1
            else:
                if char in {
                    'w': 0,
                    'r': 1,
                    'g': 2,
                    'b': 3,
                    'y': 4,
                    'c': 5,
                    'm': 6,
                }:
                    c = {
                        'w': 0,
                        'r': 1,
                        'g': 2,
                        'b': 3,
                        'y': 4,
                        'c': 5,
                        'm': 6,
                    }[char]
                else:
                    c = 0
                cont = True

    def percentage_to_color(v: float) -> str:
        if v < 0.4:
            return 'r'
        elif v < 0.7:
            return 'y'
        return 'g'

    has_color: bool = curses.has_colors()

    if has_color:
        curses.start_color()

        # initialize color pairs
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    else:
        print(f"{game_name} requires an 8-color terminal.")
        return

    # game size
    screen_size: tuple[int, int] = (80, 30)

    game_size: tuple[int, int] = (58, 22)

    # get terminal bounds
    h, w = stdscr.getmaxyx()
    if w < screen_size[0] or h < screen_size[1]:
        # assure that bounds are of sufficient size
        print(f"{game_name} requires at least {screen_size[1]} rows and {screen_size[0]} columns.")
        return

    # half of the terminal width/height
    cx: int = w // 2
    cy: int = h // 2

    level: Level = Level()

    entities: list[Entity] = level.entities
    player: Player = None

    for entity in entities:
        if isinstance(entity, Player):
            player = entity
            break
    
    if player is None:
        print("Player not found within level. Yell at the dev for this. It is her fault.")
        return

    messages: list[str] = []
    max_messages: int = screen_size[1] - game_size[1] - 3

    cam_x: int = 0
    cam_y: int = 0

    entity_map = {}

    active_visibility: list[bool] = level.seen.copy()

    def update_visibility():
        nonlocal active_visibility

        # used for pathfinding and fov
        solid_tiles = np.array([[ True for _ in range(level.size[0]) ] for _ in range(level.size[1])])

        for x in range(level.size[0]):
            for y in range(level.size[1]):
                if level.get_at(x, y)[0] in solids or ((x, y) in entity_map and entity_map[(x, y)].seethrough == False):
                    solid_tiles[y, x] = False
        
        fov = tcod.map.compute_fov(solid_tiles, (player.y, player.x), player.sight_radius, algorithm=tcod.constants.FOV_DIAMOND)
        for j in range(level.size[1]):
            for i in range(level.size[0]):
                if fov[j, i] or (i - player.x, j - player.y) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    active_visibility[j * level.size[0] + i] = True
                    level.seen[j * level.size[0] + i] = True
                else:
                    active_visibility[j * level.size[0] + i] = False

    def update_entity_map():
        nonlocal entity_map
        entity_map = {(e.x, e.y): e for e in entities if e is not player}

    def add_message(msg: str) -> None:
        nonlocal messages
        messages.append(": " + msg)
        while len(messages) > max_messages:
            messages.pop(0)

    update_visibility()
    update_entity_map()
    
    cam_x = clamp(player.x - game_size[0] // 2, 0, level.size[0] - game_size[0])
    cam_y = clamp(player.y - game_size[1] // 2, 0, level.size[1] - game_size[1])

    is_running: bool = True

    while is_running:
        # clear the screen before anything else
        stdscr.clear()

        # drawing code

        oy, ox = cy - screen_size[1] // 2, cx - screen_size[0] // 2

        # box around the game
        for y in range(screen_size[1]):
            if y in [0, screen_size[1] - 1]: ch = '+'
            else: ch = '|'
            stdscr.addch(oy + y, ox, ch)
            stdscr.addch(oy + y, ox + screen_size[0] - 1, ch)
        # box around the game
        for x in range(screen_size[0]):
            if x in [0, screen_size[0] - 1]: ch = '+'
            else: ch = '-'
            stdscr.addch(oy, ox + x, ch)
            stdscr.addch(oy + screen_size[1] - 1, ox + x, ch)
        # game title
        stdscr.addstr(oy, ox + 2, game_name)
        
        # draw the in-game info
        for y in range(game_size[1] + 1):
            for x in range(screen_size[0] - 2):
                # line splitting the UI from the game
                if y == game_size[1]:
                    stdscr.addch(oy + y + 1, ox + x + 1, '-', curses.color_pair(0))
                elif x < game_size[0]:
                    stdscr.addch(oy + y + 1, ox + x + 1, '.', curses.color_pair(0))
        
        # UI mid-way line
        for y in range(screen_size[1] - game_size[1] - 1):
            stdscr.addch(oy + game_size[1] + 1 + y, ox + screen_size[0] // 2 - 1, '+' if y in [0, screen_size[1] - game_size[1] - 2] else '|')
        # backpack seperator line
        for y in range(game_size[1] + 2):
            stdscr.addch(oy + y, ox + game_size[0] + 1, '+' if y in [0, game_size[1] + 1] else '|')

        # draw level
        level.draw(active_visibility, stdscr, ox, oy, cam_x, cam_y, game_size)

        # draw entities
        for entity in entities:
            if entity is player:
                continue
            entity.draw(level, active_visibility, stdscr, ox, oy, cam_x, cam_y, game_size)
        
        player.draw(level, active_visibility, stdscr, ox, oy, cam_x, cam_y, game_size)

        # draw UI
        health_color = percentage_to_color(player.health / player.max_health)
        food_color = percentage_to_color(player.food / player.max_food)
        water_color = percentage_to_color(player.water / player.max_water)
        set_text(ox + 1, oy + game_size[1] + 2, "\n".join([
            f"  `rHp`: `{health_color}{str(player.health).rjust(2, '0')}`/`g{player.max_health}` x `yFd`: `{food_color}{str(player.food).rjust(2, '0')}`/`g{player.max_food}` x `bWt`: `{water_color}{str(player.water).rjust(2, '0')}`/`g{player.max_water}`",
            f"  `cVsn`: `{percentage_to_color(player.sight_radius / 10)}{player.sight_radius}`    x `mNse`: `{percentage_to_color((10 - player.noise) / 10)}{player.noise}`"
        ]))
        # draw messages
        for y, message in enumerate(messages):
            set_text(ox + screen_size[0] // 2, oy + game_size[1] + 2 + y, message)

        # stats text
        stdscr.addstr(oy + game_size[1] + 1, ox + 2, "Stats")
        # messages text
        stdscr.addstr(oy + game_size[1] + 1, ox + screen_size[0] // 2 + 1, "Messages")
        # backpack text
        stdscr.addstr(oy, ox + game_size[0] + 3, "Backpack")

        # user input
        try:
            key: int = stdscr.get_wch()
        except:
            # no key pressed
            key: int = -1

        key_up: int = curses.KEY_UP
        key_down: int = curses.KEY_DOWN
        key_left: int = curses.KEY_LEFT
        key_right: int = curses.KEY_RIGHT

        key_shift_up: int = 0x223
        key_shift_down: int = 0x224
        key_shift_left: int = 0x187
        key_shift_right: int = 0x190

        dx, dy = 0, 0
        if key != -1:
            player.action = "move"
            if key == key_up:
                dx, dy = 0, -1
            elif key == key_down:
                dx, dy = 0, 1
            elif key == key_left:
                dx, dy = -1, 0
            elif key == key_right:
                dx, dy = 1, 0
            elif key == key_shift_up:
                dx, dy = 0, -1
                player.action = "attack"
            elif key == key_shift_down:
                dx, dy = 0, 1
                player.action = "attack"
            elif key == key_shift_left:
                dx, dy = -1, 0
                player.action = "attack"
            elif key == key_shift_right:
                dx, dy = 1, 0
                player.action = "attack"
            elif key == 97:
                player.health = max(0, player.health - random.randint(1, 2))
                player.food = max(0, player.food - random.randint(1, 2))
                player.water = max(0, player.water - random.randint(1, 2))

        if dx or dy:
            player.x += dx
            player.y += dy
            if level.get_at(player.x, player.y)[0] in solids:
                player.x -= dx
                player.y -= dy
            else:
                if (player.x, player.y) in entity_map:
                    entity = entity_map[(player.x, player.y)]

                    if entity.solid:
                        player.x -= dx
                        player.y -= dy
                        # if the player collides with an entity, bump interact with it
                        message = entity.on_bump_interact(player)
                    else:
                        message = entity.on_pass_over(player)

                    if message is not None:
                        add_message(message)
                    if entity.marked_for_death:
                        entities.remove(entity)

            update_visibility()
            update_entity_map()

        # move the camera
        cam_x = clamp(player.x - game_size[0] // 2, 0, level.size[0] - game_size[0])
        cam_y = clamp(player.y - game_size[1] // 2, 0, level.size[1] - game_size[1])

        # refresh and move on!
        stdscr.refresh()

if __name__ == "__main__":
    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        pass