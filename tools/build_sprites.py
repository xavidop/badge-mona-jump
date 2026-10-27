"""Draw the sprite sheets for Mona Slugger and Mona Hoops from pixel maps.

    python3 tools/build_sprites.py slugger <assets dir>
    python3 tools/build_sprites.py hoops <assets dir>

Each sheet is a paletted PNG with transparency. Letters pick colours; '.' is
clear. Frames sit side by side in one row.
"""
import struct
import sys
import zlib
from pathlib import Path

MONA = {"M": (124, 58, 237), "m": (88, 28, 180), "F": (255, 200, 210), "W": (255, 255, 255), "E": (30, 30, 40)}

# a right-handed batter in profile: ready with the bat up, the swing across
# the plate, and the follow-through. 24x24 each.
BATTER = (
    (
        "........................",
        "....M......M........HH..",
        "....MM....MM.......HH...",
        "....MMMMMMMM......HH....",
        "...MMMMMMMMMM....BB.....",
        "...MMEMMMMEMM...BB......",
        "...MMMMMMMMMM..BB.......",
        "...MMMMFFFMMM.BB........",
        "....MMMMMMMM.BB.........",
        ".....MMMMMM.BB..........",
        "......KKKKKKK...........",
        ".....KKKKKKKKK..........",
        ".....KKKKKKKKK..........",
        ".....KKKKKKKKK..........",
        "....MMKKKKKKKMM.........",
        "....MM.KKKKK.MM.........",
        "......KKKKKKK...........",
        "......KKK.KKK...........",
        "......KKK.KKK...........",
        "......MMM.MMM...........",
        "......MMM.MMM...........",
        ".....SSS...SSS..........",
        "........................",
        "........................",
    ),
    (
        "........................",
        "......M......M..........",
        "......MM....MM..........",
        "......MMMMMMMM..........",
        ".....MMMMMMMMMM.........",
        ".....MMEMMMMEMM.........",
        ".....MMMMMMMMMM.........",
        ".....MMMMFFFMMM.........",
        "......MMMMMMMM..........",
        ".......MMMMMM...........",
        "........KKKKKKK.........",
        ".......KKKKKKKKKMMBBBBBB",
        ".......KKKKKKKKKMMHHHHHH",
        ".......KKKKKKKKK........",
        "......KKKKKKKKKK........",
        ".....MMKKKKKKKK.........",
        ".....MM.KKKKKK..........",
        "........KKK.KKK.........",
        "........KKK.KKK.........",
        "........MMM.MMM.........",
        "........MMM.MMM.........",
        ".......SSS...SSS........",
        "........................",
        "........................",
    ),
    (
        "........................",
        "......M......M..........",
        "......MM....MM..........",
        "......MMMMMMMM..........",
        ".....MMMMMMMMMM.........",
        ".....MMEMMMMEMM.........",
        ".....MMMMMMMMMM.........",
        ".....MMMMFFFMMM.........",
        "......MMMMMMMM..........",
        ".......MMMMMM...........",
        "........KKKKKKK.........",
        ".....MMKKKKKKKKK........",
        "...BBMMKKKKKKKKK........",
        ".HHBB..KKKKKKKKK........",
        "HH.....KKKKKKKKK........",
        ".......KKKKKKKK.........",
        "........KKKKKK..........",
        "........KKK.KKK.........",
        "........KKK.KKK.........",
        "........MMM.MMM.........",
        "........MMM.MMM.........",
        ".......SSS...SSS........",
        "........................",
        "........................",
    ),
)
BATTER_PENS = dict(MONA, K=(220, 60, 60), B=(140, 90, 40), H=(220, 180, 120), S=(240, 240, 240))

# the pitcher far away: set, and the arm up in the windup. 12x16 each.
PITCHER = (
    (
        "...P....P...",
        "...PPPPPP...",
        "..PPEPPEPP..",
        "..PPPPPPPP..",
        "...PPPPPP...",
        "....UUUU....",
        "...UUUUUU...",
        "..PUUUUUUP..",
        "..P.UUUU.P..",
        "....UUUU....",
        "....UU.UU...",
        "....UU.UU...",
        "....PP.PP...",
        "...SS..SS...",
        "............",
        "............",
    ),
    (
        "...P....P.PP",
        "...PPPPPP.P.",
        "..PPEPPEPPP.",
        "..PPPPPPPP..",
        "...PPPPPP...",
        "....UUUU....",
        "...UUUUUUP..",
        "..PUUUUUU...",
        "..P.UUUU....",
        "....UUUU....",
        "....UU.UU...",
        "....UU.UU...",
        "....PP.PP...",
        "...SS..SS...",
        "............",
        "............",
    ),
)
PITCHER_PENS = {"P": (48, 96, 200), "E": (30, 30, 40), "U": (240, 240, 240), "S": (40, 40, 40)}

BASEBALL = (
    ".WWWW.",
    "WRWWRW",
    "WWRRWW",
    "WWRRWW",
    "WRWWRW",
    ".WWWW.",
)
BASEBALL_PENS = {"W": (250, 250, 250), "R": (220, 60, 60)}

# Mona holding the ball at her chest, and reaching up on the release. 16x24.
SHOOTER = (
    (
        "....M......M....",
        "....MM....MM....",
        "....MMMMMMMM....",
        "...MMMMMMMMMM...",
        "...MMEMMMMEMM...",
        "...MMMMMMMMMM...",
        "...MMMMFFFMMM...",
        "....MMMMMMMM....",
        ".....MMMMMM.....",
        "......JJJJ......",
        ".....JJJJJJ.....",
        "....MJJJJJJM....",
        "....MJJJJJJM....",
        "....MJJJJJJM....",
        ".....JJJJJJ.....",
        ".....JJJJJJ.....",
        ".....JJ..JJ.....",
        ".....JJ..JJ.....",
        ".....MM..MM.....",
        ".....MM..MM.....",
        "....SSS..SSS....",
        "................",
        "................",
        "................",
    ),
    (
        "....M......M.MM.",
        "....MM....MM.MM.",
        "....MMMMMMMM.MM.",
        "...MMMMMMMMMMMM.",
        "...MMEMMMMEMMM..",
        "...MMMMMMMMMM...",
        "...MMMMFFFMMM...",
        "....MMMMMMMM....",
        ".....MMMMMM.....",
        "......JJJJ......",
        ".....JJJJJJ.....",
        "....MJJJJJJ.....",
        "....MJJJJJJ.....",
        "....MJJJJJJ.....",
        ".....JJJJJJ.....",
        ".....JJJJJJ.....",
        ".....JJ..JJ.....",
        ".....JJ..JJ.....",
        ".....MM..MM.....",
        ".....MM..MM.....",
        "....SSS..SSS....",
        "................",
        "................",
        "................",
    ),
)
SHOOTER_PENS = dict(MONA, J=(255, 200, 48), S=(240, 240, 240))

BASKETBALL = (
    "..OOOO..",
    ".OOKOOO.",
    "OOOKOOOO",
    "KKKKKKKK",
    "OOOKOOOO",
    "OOOKOOOO",
    ".OOKOOO.",
    "..OOOO..",
)
BASKETBALL_PENS = {"O": (240, 130, 40), "K": (60, 30, 20)}

# Mona facing the camera for the jumper: standing, legs tucked mid-jump, and
# a spring-loaded squash. 16x20 each.
JUMPER = (
    (
        "...M........M...",
        "...MM......MM...",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMEMMMMMMEMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMFFMMMMM..",
        "...MMMMMMMMMM...",
        "....MMMMMMMM....",
        "....GGGGGGGG....",
        "...MGGGGGGGGM...",
        "...MGGGGGGGGM...",
        "....GGGGGGGG....",
        "....GGGGGGGG....",
        "....GG....GG....",
        "....GG....GG....",
        "....MM....MM....",
        "...SSS....SSS...",
        "................",
        "................",
    ),
    (
        "...M........M...",
        "...MM......MM...",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMEMMMMMMEMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMFFMMMMM..",
        "...MMMMMMMMMM...",
        "..M.MMMMMMMM.M..",
        "..M.GGGGGGGG.M..",
        "..MMGGGGGGGGMM..",
        "....GGGGGGGG....",
        "....GGGGGGGG....",
        "...GGG....GGG...",
        "..MM........MM..",
        ".SSS........SSS.",
        "................",
        "................",
        "................",
        "................",
    ),
)
JUMPER_PENS = dict(MONA, G=(80, 200, 120), S=(240, 240, 240))

# platforms for the jumper: solid, crumbling, and a spring. 24x6 / 10x8.
PLATFORM = (
    "GGGGGGGGGGGGGGGGGGGGGGGG",
    "GgggggggggggggggggggggggG",
    "DDDDDDDDDDDDDDDDDDDDDDDD",
    "DDDDDDDDDDDDDDDDDDDDDDDD",
    ".DDDDDDDDDDDDDDDDDDDDDD.",
    "..DDDDDDDDDDDDDDDDDDDD..",
)
CRUMBLE = (
    "RRRRRR.RRRRRRRRR.RRRRRRR",
    "rrrrrr.rrrrrrrrr.rrrrrrr",
    "BBBBB...BBBBBBB...BBBBBB",
    "BBBB.....BBBBB.....BBBBB",
    ".BBB.....BBBB.......BBB.",
    "..BB......BBB........BB.",
)
SPRING = (
    "..KKKKKK..",
    ".KKKKKKKK.",
    "..S....S..",
    "...S..S...",
    "..S....S..",
    "...S..S...",
    ".KKKKKKKK.",
    "KKKKKKKKKK",
)
PLATFORM_PENS = {"G": (90, 200, 90), "g": (140, 230, 120), "D": (120, 80, 40),
                 "R": (200, 100, 80), "r": (230, 150, 120), "B": (110, 70, 50),
                 "K": (220, 80, 60), "S": (240, 240, 240)}

# Mona from above for the road crosser, facing up, with a hop frame. 16x16.
CROSSER = (
    (
        "....M......M....",
        "....MM....MM....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "...MMMMMMMMMM...",
        "....MMMMMMMM....",
        "...JJJJJJJJJJ...",
        "..JJJJJJJJJJJJ..",
        "..JJJJJJJJJJJJ..",
        "...JJJJJJJJJJ...",
        "....JJ....JJ....",
        "....SS....SS....",
        "................",
    ),
    (
        "....M......M....",
        "....MM....MM....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "...MMMMMMMMMM...",
        "....MMMMMMMM....",
        "...JJJJJJJJJJ...",
        "..JJJJJJJJJJJJ..",
        "..JJJJJJJJJJJJ..",
        "...JJJJJJJJJJ...",
        "...JJ......JJ...",
        "...SS......SS...",
        "................",
    ),
)
CROSSER_PENS = dict(MONA, J=(255, 200, 48), S=(240, 240, 240))

# traffic seen from above, heading right (flipped at draw time for the other
# lane): a car, a truck, and a log for the river. 24x12 / 36x12.
CAR = (
    "....CCCCCCCCCCCCCCC.....",
    "..CCCCCCCWWWCCCCCCCCC...",
    ".CCCCCCCWWWWWCCCCCCCCCC.",
    "CCCCCCCCWWWWWCCCCCCCCCCY",
    "CCCCCCCCWWWWWCCCCCCCCCCY",
    ".CCCCCCCWWWWWCCCCCCCCCC.",
    "..CCCCCCCWWWCCCCCCCCC...",
    "....CCCCCCCCCCCCCCC.....",
    "...KK............KK.....",
    "...KK............KK.....",
    "........................",
    "........................",
)
TRUCK = (
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCCCCCCCC.",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCC",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCY",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCY",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCY",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCY",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCWWCCCCCC",
    "TTTTTTTTTTTTTTTTTTTTTTTT.CCCCCCCCCC.",
    "..KK............KK.....KK........KK.",
    "..KK............KK.....KK........KK.",
    "....................................",
    "....................................",
)
LOG = (
    ".LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL.",
    "LLLLLLLlLLLLLLLLLLLlLLLLLLLLLLLLLLLL",
    "LLLllLLLLLLLLllLLLLLLLLLllLLLLLLLLLL",
    "LLLLLLLLLLlLLLLLLLLLLLLLLLLLllLLLLLL",
    "LLLLlLLLLLLLLLLLLLllLLLLLLLLLLLLLlLL",
    "LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL",
    ".LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL.",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
    "....................................",
)
TRAFFIC_PENS = {"C": (230, 70, 70), "W": (170, 220, 250), "Y": (255, 230, 120), "K": (30, 30, 40),
                "T": (80, 140, 220), "L": (130, 90, 50), "l": (170, 120, 70)}


def png(path, width, height, palette, pixels):
    rows = b"".join(b"\x00" + bytes(pixels[y * width:(y + 1) * width]) for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0))
            + chunk(b"PLTE", b"".join(bytes(entry[:3]) for entry in palette))
            + chunk(b"tRNS", bytes(entry[3] for entry in palette))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
    Path(path).write_bytes(data)
    print(path, width, "x", height, len(data), "bytes")


class Sheet:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.palette = [(0, 0, 0, 0)]
        self.pixels = [0] * (width * height)

    def put(self, x, y, rgb):
        entry = (rgb[0], rgb[1], rgb[2], 255)
        if entry not in self.palette:
            self.palette.append(entry)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = self.palette.index(entry)

    def stamp(self, rows, pens, left, top):
        for y, line in enumerate(rows):
            for x, key in enumerate(line):
                if key in pens:
                    self.put(left + x, top + y, pens[key])


def strip(path, frames, pens):
    width, height = len(frames[0][0]), len(frames[0])
    sheet = Sheet(width * len(frames), height)
    for index, rows in enumerate(frames):
        sheet.stamp(rows, pens, index * width, 0)
    png(path, sheet.width, sheet.height, sheet.palette, sheet.pixels)


def main():
    game = sys.argv[1]
    assets = Path(sys.argv[2])
    assets.mkdir(exist_ok=True)
    if game == "slugger":
        strip(assets / "batter.png", BATTER, BATTER_PENS)
        strip(assets / "pitcher.png", PITCHER, PITCHER_PENS)
        strip(assets / "ball.png", (BASEBALL,), BASEBALL_PENS)
    elif game == "hoops":
        strip(assets / "shooter.png", SHOOTER, SHOOTER_PENS)
        strip(assets / "ball.png", (BASKETBALL,), BASKETBALL_PENS)
    elif game == "jump":
        strip(assets / "jumper.png", JUMPER, JUMPER_PENS)
        strip(assets / "platforms.png", (PLATFORM, CRUMBLE), PLATFORM_PENS)
        strip(assets / "spring.png", (SPRING,), PLATFORM_PENS)
    elif game == "crossing":
        strip(assets / "crosser.png", CROSSER, CROSSER_PENS)
        strip(assets / "car.png", (CAR,), TRAFFIC_PENS)
        strip(assets / "truck.png", (TRUCK,), TRAFFIC_PENS)
        strip(assets / "log.png", (LOG,), TRAFFIC_PENS)
    else:
        raise SystemExit("game must be slugger, hoops, jump or crossing")


if __name__ == "__main__":
    main()
