"""
Mona Jump: bounce ever higher from platform to platform, tilting to steer.

Green platforms are solid, blue ones slide, brown ones crumble after one
bounce, and springs launch Mona sky high. Fall off the bottom and the climb
is over; the badge keeps your best height.

Controls:
* Tilt or Left / Right = Steer
* Select = Start, or jump again
* Menu = Switch between tilt and button steering on the title screen
* Back = Back to the title
"""

import math
import os
import random
import sys

from badgeware import State

APP_DIR = "/system/apps/mona_jump"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

badge.mode(HIRES | VSYNC)
screen.antialias = image.OFF

WIDTH, HEIGHT = screen.width, screen.height

JUMPER = image.load("assets/jumper.png").spritesheet(2, 1)
PLATFORMS = image.load("assets/platforms.png").spritesheet(2, 1)
SPRING = image.load("assets/spring.png")

PLAYER_W, PLAYER_H = 32, 40
PLAT_W, PLAT_H = 48, 12
SPRING_W, SPRING_H = 20, 16
GRAVITY = 1000.0
JUMP_V = 440.0
SPRING_V = 780.0
MOVE_V = 240.0
SCROLL_LINE = 96            # keep Mona above this screen row by scrolling
TILT_GRAVITY = 16384.0
SOLID, MOVING, CRUMBLE = 0, 1, 2

SKY_TOP = color.rgb(96, 170, 240)
SKY_LOW = color.rgb(176, 220, 250)
CLOUD = color.rgb(255, 255, 255)
MOVING_TINT = color.rgb(80, 150, 240)
INK = color.rgb(20, 20, 32)
CREAM = color.rgb(240, 232, 208)
AMBER = color.rgb(255, 200, 48)
RED = color.rgb(230, 70, 70)
PANEL = color.rgb(20, 20, 32, 190)
SHADOW = color.rgb(0, 0, 0, 70)

TITLE = font.futile
BIG = font.ignore
BODY = font.nope
SMALL = font.sins

TITLE_SCREEN, PLAY, OVER = 0, 1, 2

state = {"best": 0, "games": 0, "tilt": True}
State.load("mona_jump", state)
for key in ("best", "games"):
    if not isinstance(state.get(key), int) or state[key] < 0:
        state[key] = 0
state["tilt"] = bool(state.get("tilt", True))


def save_state():
    try:
        State.save("mona_jump", state)
    except OSError as error:
        print("Mona Jump: could not save:", error)


# ----------------------------------------------------------------------------
# world: y grows downward, the camera is the world y of the screen top

mode = TITLE_SCREEN
player = None           # [x, y, vx, vy]
platforms = []          # [x, y, kind, dir, spring, broken_at]
clouds = []
camera_y = 0.0
start_y = 0.0
top_y = 0.0             # world y of the highest platform made so far
score = 0
dead_at = 0
facing = 1


def seed_clouds():
    del clouds[:]
    for n in range(6):
        clouds.append([random.randint(0, WIDTH), random.randint(-HEIGHT, HEIGHT), random.randint(24, 44)])


def height_score():
    return int((start_y - camera_y) / 10)


def make_platform(y):
    """A platform at world y, harder kinds and springs as the climb goes on."""
    climbed = max(0, height_score())
    roll = random.random()
    kind = SOLID
    if roll < min(0.35, 0.08 + climbed / 600):
        kind = MOVING
    elif roll < min(0.6, 0.12 + climbed / 400):
        kind = CRUMBLE
    spring = kind == SOLID and random.random() < 0.09
    direction = random.choice((-1, 1))
    platforms.append([float(random.randint(0, WIDTH - PLAT_W)), float(y), kind, direction, spring, None])


def extend_world():
    global top_y
    climbed = max(0, height_score())
    while top_y > camera_y - 80:
        gap = random.randint(42, 64 + min(34, climbed // 12))
        top_y -= gap
        make_platform(top_y)
    # anything well below the screen is gone for good
    limit = camera_y + HEIGHT + 60
    for index in range(len(platforms) - 1, -1, -1):
        if platforms[index][1] > limit:
            platforms.pop(index)


def start_game():
    global mode, player, camera_y, start_y, top_y, score, facing
    random.seed(badge.ticks)
    del platforms[:]
    camera_y = 0.0
    start_y = 0.0
    seed_clouds()
    platforms.append([float(WIDTH // 2 - PLAT_W // 2), float(HEIGHT - 30), SOLID, 1, False, None])
    top_y = HEIGHT - 30
    for n in range(6):
        top_y -= random.randint(44, 60)
        make_platform(top_y)
    player = [float(WIDTH // 2 - PLAYER_W // 2), float(HEIGHT - 30 - PLAYER_H), 0.0, -JUMP_V]
    score = 0
    facing = 1
    mode = PLAY


def read_steer():
    value = 0.0
    if badge.held(BUTTON_LEFT):
        value -= 1.0
    if badge.held(BUTTON_RIGHT):
        value += 1.0
    if value == 0.0 and state["tilt"]:
        try:
            ax = badge.imu()[0]
        except (OSError, TypeError, IndexError):
            ax = 0
        value = max(-1.0, min(1.0, -ax / TILT_GRAVITY * 2.5))
        if abs(value) < 0.08:
            value = 0.0
    return value


def update_play(dt):
    global camera_y, score, mode, dead_at, facing
    steer = read_steer()
    if steer:
        facing = 1 if steer > 0 else -1
    player[2] = steer * MOVE_V
    prev_feet = player[1] + PLAYER_H
    player[3] += GRAVITY * dt
    player[0] += player[2] * dt
    player[1] += player[3] * dt
    # wrap around the sides
    if player[0] < -PLAYER_W / 2:
        player[0] += WIDTH
    elif player[0] > WIDTH - PLAYER_W / 2:
        player[0] -= WIDTH
    feet = player[1] + PLAYER_H
    now = badge.ticks
    for plat in platforms:
        if plat[2] == MOVING:
            plat[0] += plat[3] * 60 * dt
            if plat[0] < 0 or plat[0] > WIDTH - PLAT_W:
                plat[3] = -plat[3]
                plat[0] = max(0, min(WIDTH - PLAT_W, plat[0]))
        if plat[5] is not None:
            continue
        if player[3] > 0 and prev_feet <= plat[1] + 4 and feet >= plat[1] and player[0] + 24 > plat[0] and player[0] + 8 < plat[0] + PLAT_W:
            on_spring = plat[4] and abs((player[0] + PLAYER_W / 2) - (plat[0] + PLAT_W / 2)) < 16
            player[3] = -(SPRING_V if on_spring else JUMP_V)
            player[1] = plat[1] - PLAYER_H
            if plat[2] == CRUMBLE:
                plat[5] = now
    for index in range(len(platforms) - 1, -1, -1):
        if platforms[index][5] is not None and now - platforms[index][5] > 250:
            platforms.pop(index)
    # scroll up when Mona climbs past the line
    screen_y = player[1] - camera_y
    if screen_y < SCROLL_LINE:
        camera_y = player[1] - SCROLL_LINE
    extend_world()
    score = height_score()
    if player[1] - camera_y > HEIGHT + 10:
        state["games"] += 1
        if score > state["best"]:
            state["best"] = score
        save_state()
        dead_at = now
        mode = OVER


# ----------------------------------------------------------------------------
# drawing

def fill(x, y, w, h, pen):
    screen.pen = pen
    screen.rectangle(x, y, w, h)


def write(text, x, y, pen, face=BODY):
    screen.font = face
    screen.pen = pen
    screen.text(text, x, y)


def text_width(text, face=BODY):
    screen.font = face
    return screen.measure_text(text)[0]


def write_centred(text, cx, y, pen, face=BODY):
    write(text, cx - text_width(text, face) // 2, y, pen, face)


def write_shadowed(text, cx, y, pen, face=BODY):
    write_centred(text, cx + 2, y + 2, INK, face)
    write_centred(text, cx, y, pen, face)


def draw_sky():
    fill(0, 0, WIDTH, HEIGHT // 2, SKY_TOP)
    fill(0, HEIGHT // 2, WIDTH, HEIGHT - HEIGHT // 2, SKY_LOW)
    for cloud in clouds:
        y = (cloud[1] - camera_y * 0.3) % (HEIGHT + 60) - 30
        fill(cloud[0], int(y), cloud[2], 8, CLOUD)
        fill(cloud[0] + 8, int(y) - 6, cloud[2] - 16, 7, CLOUD)


def draw_platforms():
    for x, y, kind, direction, spring, broken_at in platforms:
        sy = int(y - camera_y)
        if sy < -20 or sy > HEIGHT + 20:
            continue
        frame = 1 if kind == CRUMBLE else 0
        if broken_at is not None:
            # the two halves fall apart
            drop = (badge.ticks - broken_at) // 10
            screen.blit(PLATFORMS.sprite(frame, 0), rect(0, 0, 12, 6), rect(int(x) - drop, sy + drop, PLAT_W // 2, PLAT_H), image.NEAREST)
            screen.blit(PLATFORMS.sprite(frame, 0), rect(12, 0, 12, 6), rect(int(x) + PLAT_W // 2 + drop, sy + drop, PLAT_W // 2, PLAT_H), image.NEAREST)
            continue
        screen.blit(PLATFORMS.sprite(frame, 0), rect(0, 0, 24, 6), rect(int(x), sy, PLAT_W, PLAT_H), image.NEAREST)
        if kind == MOVING:
            fill(int(x) + 2, sy + 1, PLAT_W - 4, 3, MOVING_TINT)
        if spring:
            screen.blit(SPRING, rect(0, 0, 10, 8), rect(int(x) + PLAT_W // 2 - SPRING_W // 2, sy - SPRING_H + 2, SPRING_W, SPRING_H), image.NEAREST)


def draw_player():
    if player is None:
        return
    frame = 1 if player[3] < -120 else 0
    x, y = int(player[0]), int(player[1] - camera_y)
    width = PLAYER_W if facing > 0 else -PLAYER_W
    left = x if facing > 0 else x + PLAYER_W
    screen.blit(JUMPER.sprite(frame, 0), rect(0, 0, 16, 20), rect(left, y, width, PLAYER_H), image.NEAREST)
    # the wrapped copy when Mona straddles an edge
    if x < 0:
        screen.blit(JUMPER.sprite(frame, 0), rect(0, 0, 16, 20), rect(left + WIDTH, y, width, PLAYER_H), image.NEAREST)
    elif x > WIDTH - PLAYER_W:
        screen.blit(JUMPER.sprite(frame, 0), rect(0, 0, 16, 20), rect(left - WIDTH, y, width, PLAYER_H), image.NEAREST)


def draw_hud():
    fill(0, 0, WIDTH, 16, PANEL)
    write("%d M" % score, 6, 2, AMBER, BODY)
    write("BEST %d M" % state["best"], WIDTH - 6 - text_width("BEST %d M" % state["best"], BODY), 2, CREAM, BODY)


def draw_title():
    draw_sky()
    bounce = int(abs(math.sin(badge.ticks / 350)) * 22)
    screen.blit(PLATFORMS.sprite(0, 0), rect(0, 0, 24, 6), rect(WIDTH // 2 - PLAT_W // 2, 200, PLAT_W, PLAT_H), image.NEAREST)
    screen.blit(JUMPER.sprite(1 if bounce > 10 else 0, 0), rect(0, 0, 16, 20), rect(WIDTH // 2 - PLAYER_W // 2, 200 - PLAYER_H - bounce, PLAYER_W, PLAYER_H), image.NEAREST)
    fill(20, 26, WIDTH - 40, 104, PANEL)
    write_shadowed("MONA JUMP", WIDTH // 2, 34, AMBER, BIG)
    write_shadowed("HOW HIGH CAN AN OCTOCAT GO?", WIDTH // 2, 66, CREAM, SMALL)
    if (badge.ticks // 400) % 2:
        write_shadowed("SELECT TO JUMP", WIDTH // 2, 86, CREAM, BODY)
    write_shadowed("MENU: STEER BY %s" % ("TILT" if state["tilt"] else "BUTTONS"), WIDTH // 2, 106, CREAM, SMALL)
    if state["games"]:
        write_shadowed("BEST %d M IN %d CLIMBS" % (state["best"], state["games"]), WIDTH // 2, 222, AMBER, SMALL)


def draw_over():
    draw_sky()
    draw_platforms()
    fill(30, 50, WIDTH - 60, 120, PANEL)
    write_shadowed("%d M" % score, WIDTH // 2, 60, AMBER, BIG)
    write_centred("NEW BEST!" if score >= state["best"] and score > 0 else "BEST %d M" % state["best"], WIDTH // 2, 96, CREAM, BODY)
    if badge.ticks - dead_at > 600 and (badge.ticks // 400) % 2:
        write_centred("SELECT: AGAIN   BACK: TITLE", WIDTH // 2, 136, CREAM, SMALL)


def update():
    global mode
    dt = min(badge.ticks_delta, 50) / 1000
    if mode == TITLE_SCREEN:
        if badge.pressed(BUTTON_MENU):
            state["tilt"] = not state["tilt"]
            save_state()
        if badge.pressed(BUTTON_SELECT):
            start_game()
        draw_title()
    elif mode == PLAY:
        if badge.pressed(BUTTON_BACK):
            mode = TITLE_SCREEN
            return
        update_play(dt)
        draw_sky()
        draw_platforms()
        draw_player()
        draw_hud()
    else:
        if badge.ticks - dead_at > 600:
            if badge.pressed(BUTTON_SELECT):
                start_game()
            elif badge.pressed(BUTTON_BACK):
                mode = TITLE_SCREEN
        draw_over()


def on_exit():
    save_state()


seed_clouds()
run(update)
