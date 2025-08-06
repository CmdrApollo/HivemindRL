import curses
import random
import numpy as np
import time

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
    stdscr.nodelay(True)
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
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE)
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
    noise_map: list[int] = [0 for _ in range(level.size[0] * level.size[1])]

    def propogate_noise(x, y, radius, intensity=1):
        if radius == 0:
            return
        
        for cx in range(x - radius, x + radius + 1):
            for cy in range(y - radius, y + radius + 1):
                dist = distance(cx, cy, x, y)

                if dist <= radius:
                    noise_map[cy * level.size[0] + cx] += round((1 - dist / radius) * intensity)

    propogate_noise(player.x, player.y, player.noise + 2, player.noise + 2)

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

    def take_entity_turn(entity):
        nonlocal entities
        def corpse_zombie_conversion(entity):
            if isinstance(entity, Corpse):
                if entity.to_zombie:
                    entities.append(Zombie(entity.x, entity.y))
            elif isinstance(entity, Zombie):
                if entity.is_bloater:
                    pass
                else:
                    # TODO FIX
                    entities.append(Corpse(entity.x, entity.y))

        entity.on_my_turn(player)
        if entity.marked_for_death:
            corpse_zombie_conversion(entity)
            entities.remove(entity)
        elif StatusEffect.Exhausted in player.statuses:
            # entities get a second turn when the player is exhausted
            entity.on_my_turn(player)
            if entity.marked_for_death:
                corpse_zombie_conversion(entity)
                entities.remove(entity)

    update_visibility()
    update_entity_map()
    
    cam_x = clamp(player.x - game_size[0] // 2, 0, level.size[0] - game_size[0])
    cam_y = clamp(player.y - game_size[1] // 2, 0, level.size[1] - game_size[1])

    invert_timer = 0

    is_running: bool = True

    while is_running:
        invert_timer = max(0, invert_timer - 0.1)

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
        
        player.draw(level, active_visibility, stdscr, ox, oy, cam_x, cam_y, game_size, invert_timer > 0)

        # if int(time.time() * 2) & 1:
        #     for y in range(level.size[1]):
        #         for x in range(level.size[0]):
        #             if 0 <= y - cam_y < game_size[1] and 0 <= x - cam_x < game_size[0] and noise_map[y * level.size[0] + x]:
        #                 stdscr.addstr(oy + y + 1 - cam_y, ox + x + 1 - cam_x, hex(noise_map[y * level.size[0] + x]).removeprefix('0x'), curses.color_pair(noise_map[y * level.size[0] + x]))

        # draw UI
        health_color = percentage_to_color(player.health / player.max_health)
        food_color = percentage_to_color(player.food / player.max_food)
        water_color = percentage_to_color(player.water / player.max_water)
        set_text(ox + 1, oy + game_size[1] + 2, "\n".join([
            f"  `rHp`: `{health_color}{str(player.health).rjust(2, '0')}`/`g{player.max_health}` x `yFd`: `{food_color}{str(player.food).rjust(2, '0')}`/`g{player.max_food}` x `bWt`: `{water_color}{str(player.water).rjust(2, '0')}`/`g{player.max_water}`",
            f"  `cVsn`: `{percentage_to_color(player.sight_radius / 10)}{player.sight_radius}`    x `mNse`: `{percentage_to_color((10 - player.noise) / 10)}{player.noise}`"
        ]))

        t = ""
        for i, p_status in enumerate(player.statuses):
            t += {
                StatusEffect.Bleeding: "`rBleeding`",
                StatusEffect.Dehydrated: "`cDehydrated`",
                StatusEffect.Exhausted: "`mExhausted`",
                StatusEffect.Infected: "`gInfected`",
                StatusEffect.Starving: "`yStarving`",
            }[p_status] + "   "
            if i % 3 == 2:
                set_text(ox + 3, oy + game_size[1] + 5 + i // 3, t)
                t = ""
        if len(t):
            set_text(ox + 3, oy + game_size[1] + 5 + i // 3, t)

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

        old_health = player.health

        if dx or dy:
            old_x = player.x
            old_y = player.y

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
            
            if player.x != old_x or player.y != old_y:
                if level.get_at(player.x, player.y)[0] == '~':
                    # if the player passes over blood, have a chance of infection
                    if random.random() < 0.1 * (1 + (StatusEffect.Bleeding in player.statuses)):
                        if StatusEffect.Infected not in player.statuses:
                            player.add_status(StatusEffect.Infected)
                            add_message("You have become infected.")


                # we actually moved, so update status effects and allow
                # other entities to take their turns
                for status in list(player.statuses):
                    match status:
                        case StatusEffect.Bleeding:
                            player.health = max(0, player.health - 1)
                            add_message("You `rbleed out`, dealing `y1` damage.")
                            if random.random() < 0.05:
                                # 5% chance to stop bleeding
                                player.remove_status(StatusEffect.Bleeding)
                                add_message("You stop bleeding.")
                            # put blood on the floor
                            for i in range(-1, 2):
                                for j in range(-1, 2):
                                    if random.random() < 0.5:
                                        ch = level.get_at(player.x + i, player.y + j)[0]
                                        if ch == '.':
                                            level.set_at(player.x + i, player.y + j, '~', 1)
                        case StatusEffect.Dehydrated:
                            player.health = max(0, player.health - 1)
                            add_message("You are dehyrdated and take `y1` damage.")
                        case StatusEffect.Exhausted:
                            pass
                        case StatusEffect.Infected:
                            if random.random() < 0.1:
                                # 10% chance of taking damage when infected
                                add_message("You are infected, and take `y1` damage.")
                        case StatusEffect.Starving:
                            player.health = max(0, player.health - 1)
                            add_message("You are starving and take `y1` damage.")

                # every value in the noise map decreases by one
                for y in range(level.size[1]):
                    for x in range(level.size[0]):
                        value = noise_map[y * level.size[0] + x]
                        noise_map[y * level.size[0] + x] = max(0, value - 1)

                # we then propogate noise from the player's position again
                propogate_noise(player.x, player.y, player.noise)
                
                for entity in entities[::-1]:
                    if entity is not player:
                        take_entity_turn(entity)

            update_visibility()
            update_entity_map()

        # move the camera
        cam_x = clamp(player.x - game_size[0] // 2, 0, level.size[0] - game_size[0])
        cam_y = clamp(player.y - game_size[1] // 2, 0, level.size[1] - game_size[1])

        if player.health != old_health:
            invert_timer = 2
            
        # refresh and move on!
        stdscr.refresh()

if __name__ == "__main__":
    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        pass