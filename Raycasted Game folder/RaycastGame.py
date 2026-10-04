import pygame, math, sys, os, random
try:
    import numpy as np          # used for the textured floor and roof (pip install numpy)
except ImportError:
    np = None

pygame.init()
W, H = 800, 600
win = pygame.display.set_mode((W, H), pygame.SCALED)   # SCALED lets F4 go fullscreen cleanly
clock = pygame.time.Clock()

# ---- Tweakable settings ----
MOUSE_SENS = 0.0012    # radians per pixel (lower = less sensitive)
MOUSE_SMOOTH = 18.0    # higher = snappier, lower = smoother/floatier
MOVE_SPEED = 2.5       # map units per second
MOVE_SMOOTH = 12.0     # how quickly movement speeds up / slows down
PLAYER_RADIUS = 0.2    # keeps you from clipping into walls
SWING_TIME = 0.4       # seconds for one sword swing
SHIELD_SPEED = 14.0    # how quickly the shield raises / lowers
FOV = math.pi / 3
GAME_TITLE = "Raycasted Dungeon Crawler"
pygame.display.set_caption(GAME_TITLE)
MENU_BG_TEXTURE_PATH = "backgroundtexture.png"  # any size, scaled to fill the window (extra is cropped) - or "" for the drawn background
MENU_BG_DIM = 0.6      # 1.0 = full brightness, lower = darker so the buttons stay readable

# ---- Procedural world (endless, built from 8x8-tile chunks) ----
WALL_DENSITY = 0.20        # chance each tile is a wall (0.1 = open, 0.3 = cramped)
LOAD_RADIUS = 2            # chunks generated around you (2 = a 5x5 chunk area)
KEEP_RADIUS = 3            # chunks further than this from you are deleted

# ---- Gold ----
GOLD_MIN, GOLD_MAX = 1, 5  # gold dropped per kill

# ---- Player / combat ----
PLAYER_MAX_HEALTH = 100
SWORD_DAMAGE = 1       # damage per hit
SWORD_RANGE = 1.4      # how far the sword reaches (map units)
SWORD_ARC_DEG = 40     # how far off-center an enemy can be and still get hit
SWING_HIT_AT = 0.45    # point in the swing (0-1) where the hit lands
BLOCK_ARC_DEG = 70     # shield only blocks enemies within this angle of where you look

# ---- Enemies ----
# Enemy image: upright, standing, feet at the bottom. Transparent PNG works best.
# Leave empty ("") to use a built-in green goblin.
ENEMY_TEXTURE_PATH = "knighttexture.png"  # or "" for built-in goblin
ENEMY_SCALE = 0.8      # enemy height relative to wall height
ENEMY_HEALTH = 3       # sword hits to kill
ENEMY_SPEED = 0.9      # map units per second
ENEMY_DAMAGE = 10
ENEMY_ATTACK_RANGE = 0.9
ENEMY_ATTACK_COOLDOWN = 1.2   # seconds between attacks
ENEMY_RADIUS = 0.2
ENEMY_COUNT = 3        # always exactly this many enemies, all in the chunk you are standing in
SPAWN_MIN_DIST = 3.0   # an enemy never spawns closer than this to you

# ---- Potions (press R to drink) ----
# Potion image: upright bottle, transparent PNG works best. Leave "" for a drawn red potion.
POTION_TEXTURE_PATH = "potiontexture.png"  # or "" for drawn version
POTION_ROTATE = 0      # degrees clockwise to turn your image so it stands upright
POTION_FLIP = False    # mirror the image left/right (applied after rotating)
POTION_HEIGHT = 160    # on-screen height in pixels (aspect ratio is kept)
START_POTIONS = 3
MAX_POTIONS = 9
POTION_HEAL = 25       # health restored per potion
POTION_TIME = 0.9      # seconds the drinking animation takes
POTION_DROP_CHANCE = 0.3   # chance an enemy drops a potion when killed
# Shop upgrades (Shop > Potions tab). Each step is (gold cost, amount added). Add or remove steps freely.
POTION_UPGRADES = {
    "heal": {"name": "Potion Potency", "steps": [(8, 5), (15, 5), (25, 15), (40, 5)]},    # + health per potion
    "drop": {"name": "Potion Luck",    "steps": [(10, 0.05), (20, 0.05), (32, 0.05), (48, 0.05)]},  # + drop chance
    "max": {"name": "Potion Capacity", "steps": [(12, 1), (24, 1), (36, 1), (48, 1)]}  # + max potions
}

# ---- Wall texture ----
# Put the path to your wall image here, e.g. "wall.png"
# Leave it empty ("") to use a plain placeholder pattern.
WALL_TEXTURE_PATH = "walltexture.png"  # or "" for placeholder

# ---- Floor & roof textures ----
# Put the image files next to this script. Seamless/tileable images look best (64x64 or 128x128 is plenty).
# Leave a path empty ("") - or if the file is missing - to get a flat color instead.
FLOOR_TEXTURE_PATH = "floortexture.png"   # or "" for a flat color
ROOF_TEXTURE_PATH = "rooftexture.png"     # or "" for a flat color
FLOOR_COLOR = (85, 75, 65)    # flat color used when there's no floor image
ROOF_COLOR = (50, 50, 65)     # flat color used when there's no roof image
FLOOR_TILE = 1.0     # how many map tiles one copy of the floor image covers (2.0 = twice as big, 0.5 = smaller)
ROOF_TILE = 1.0      # same, for the roof
FLOOR_DETAIL = 2     # 1 = sharpest but slowest, 2 = good balance, 3-4 = chunkier but fastest

# ---- Sword & shield textures ----
# Leave empty ("") to use the built-in drawn versions.
# Sword image: should point straight UP with the handle at the bottom.
# Shield image: drawn centered, upright. PNGs with transparency work best.
SWORD_TEXTURE_PATH = "swordtexture.png"  # or "" for drawn version
SHIELD_TEXTURE_PATH = "shieldtexture.png"  # or "" for drawn version
# The inventory and shop reuse the sword and shield images above (one image per item type;
# the Iron / Diamond / etc. colors are tinted over it, see TINTS). Two new image slots:
ARMOR_TEXTURE_PATH = "armortexture.png"    # chestplate, upright - or "" for drawn version
ARMOR_ROTATE = 0       # degrees clockwise to turn your armor image so it stands upright
ARMOR_FLIP = False     # mirror the armor image left/right (applied after rotating)
GOLD_TEXTURE_PATH = "goldtexture.png"      # coin image - or "" for drawn coin
MALE_TEXTURE_PATH = "maletexture.png"      # inventory person when you pick Male - or "" for the drawn figure
FEMALE_TEXTURE_PATH = "femaletexture.png"  # inventory person when you pick Female - or "" for the drawn figure
PLAYER_ROTATE = 0      # degrees clockwise to turn your person image so it stands upright
PLAYER_FLIP = False    # mirror the person image left/right (applied after rotating)
PLAYER_HEIGHT = 210    # on-screen height in the inventory (aspect ratio is kept)
ICON_SWORD_ANGLE = 45  # tilt of the sword in inventory/shop slots (0 = straight up, 45 = Minecraft-style)
# If your sword image doesn't point straight up, fix it here:
SWORD_ROTATE = 180       # degrees clockwise to turn the image (e.g. 45 if it points up-left,
                       # 90 if it points left, -45 if it points up-right, -90 if it points right)
SWORD_FLIP = False     # mirror the image left/right (applied after rotating)
SWORD_PIVOT = (0.5, 1.0)  # where the handle is in the final upright image (x, y from 0 to 1)
                          # (0.5, 1.0) = bottom center. This is the point the sword swings around.
SWORD_HEIGHT = 380     # on-screen height in pixels (aspect ratio is kept)
SHIELD_HEIGHT = 180    # on-screen height when lowered (grows when raised)

def make_placeholder_texture(size=64):
    """Simple brick-like pattern used when no image is provided."""
    surf = pygame.Surface((size, size))
    surf.fill((150, 150, 150))
    brick_h = size // 4
    for row in range(4):
        y = row * brick_h
        offset = (size // 4) if row % 2 else 0
        for bx in range(-1, 3):
            x = bx * (size // 2) + offset
            pygame.draw.rect(surf, (110, 110, 110),
                             (x, y, size // 2, brick_h), 1)
    return surf

def load_wall_texture(path):
    if not path:
        print("WALL_TEXTURE_PATH is empty - using placeholder texture.")
        return make_placeholder_texture()

    # Look for the image as given, then next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [path, os.path.join(script_dir, path)]
    for p in candidates:
        if os.path.isfile(p):
            try:
                tex = pygame.image.load(p).convert()
                print(f"Loaded wall texture: {p} ({tex.get_width()}x{tex.get_height()})")
                return tex
            except Exception as err:
                print(f"Found '{p}' but could not load it: {err}")
                return make_placeholder_texture()

    print("Texture file not found. Tried:")
    for p in candidates:
        print("  ", os.path.abspath(p))
    print("Using placeholder texture.")
    return make_placeholder_texture()

wall_tex = load_wall_texture(WALL_TEXTURE_PATH)
TEX_W, TEX_H = wall_tex.get_size()

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

def find_image(path):
    """Find the image: exact name first, then a forgiving search (any capitalization, any image
    extension, even a doubled one like 'floor.png.png') in this script's folder."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for p in (path, os.path.join(script_dir, path)):
        if os.path.isfile(p):
            return p
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    for folder in (script_dir, os.getcwd()):
        try:
            names = sorted(os.listdir(folder))
        except OSError:
            continue
        for name in names:
            if name.lower().startswith(stem) and name.lower().endswith(IMAGE_EXTS):
                return os.path.join(folder, name)
    return None

def load_flat_texture(path, color, label):
    """Pixel array (width, height, 3) for the floor/roof: your image, or a single solid color."""
    if path:
        p = find_image(path)
        if p:
            try:
                img = pygame.image.load(p).convert()
                print(f"Loaded {label} texture: {p} ({img.get_width()}x{img.get_height()})")
                return pygame.surfarray.array3d(img)
            except Exception as err:
                print(f"Found '{p}' but could not load the {label} texture: {err}")
        else:
            folder = os.path.dirname(os.path.abspath(__file__))
            print(f"{label} texture '{path}' not found - using a flat color.")
            print(f"  Looked in: {folder}")
            print("  Image files there:", [n for n in sorted(os.listdir(folder)) if n.lower().endswith(IMAGE_EXTS)])
    return np.array([[color]], dtype=np.uint8)

if np is None:
    print("numpy is not installed - floor and roof will be flat colors. Install it with: pip install numpy")
else:
    floor_tex = load_flat_texture(FLOOR_TEXTURE_PATH, FLOOR_COLOR, "floor")
    roof_tex = load_flat_texture(ROOF_TEXTURE_PATH, ROOF_COLOR, "roof")
    # Everything below depends only on the screen size, so it's worked out once here.
    _D = max(1, int(FLOOR_DETAIL))
    _fh = H - H // 2                                  # pixel rows below the horizon
    _nr, _nc = (_fh + _D - 1) // _D, (W + _D - 1) // _D
    _dy = (np.arange(_nr) + 0.5) * _D                 # screen rows below the horizon
    _perp = (H / 2) / _dy                             # distance of the floor seen on each row
    _off = -FOV / 2 + FOV * (np.arange(_nc) * _D + _D / 2) / W    # each column's angle from straight ahead
    _dist = _perp[:, None] / np.cos(_off)[None, :]    # distance along each ray (fixes fisheye)
    _shade = (1 / (1 + _perp ** 2 * 0.5))[:, None, None]          # same darkening as the walls

def draw_floor_roof(surface, px, py, pa):
    """Floor below the horizon, roof above it (the roof is the floor mirrored)."""
    if np is None:
        surface.fill(ROOF_COLOR, (0, 0, W, H // 2))
        surface.fill(FLOOR_COLOR, (0, H // 2, W, H - H // 2))
        return
    ang = pa + _off
    wx = px + np.cos(ang)[None, :] * _dist           # where each screen pixel lands in the world
    wy = py + np.sin(ang)[None, :] * _dist
    halves = []
    for tex, tile in ((floor_tex, FLOOR_TILE), (roof_tex, ROOF_TILE)):
        tw, th = tex.shape[0], tex.shape[1]
        tx = ((wx / tile) % 1.0 * tw).astype(np.int32) % tw
        ty = ((wy / tile) % 1.0 * th).astype(np.int32) % th
        pix = (tex[tx, ty] * _shade).astype(np.uint8)
        surf = pygame.surfarray.make_surface(np.ascontiguousarray(pix.swapaxes(0, 1)))
        halves.append(pygame.transform.scale(surf, (W, _fh)))
    surface.blit(halves[0], (0, H // 2))
    surface.blit(pygame.transform.flip(halves[1], False, True), (0, H // 2 - _fh))

def load_overlay_image(path, height, label, rotate=0, flip=False):
    """Load a transparent overlay image scaled to `height`, or None if unset."""
    if not path:
        return None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for p in (path, os.path.join(script_dir, path)):
        if os.path.isfile(p):
            try:
                img = pygame.image.load(p).convert_alpha()
                if rotate:
                    img = pygame.transform.rotate(img, -rotate)  # clockwise degrees
                if flip:
                    img = pygame.transform.flip(img, True, False)
                w = max(1, int(img.get_width() * height / img.get_height()))
                print(f"Loaded {label} texture: {p}")
                return pygame.transform.smoothscale(img, (w, height))
            except Exception as err:
                print(f"Found '{p}' but could not load {label} texture: {err}")
                return None
    print(f"{label} texture not found: {os.path.abspath(path)} - using drawn version.")
    return None

sword_img = load_overlay_image(SWORD_TEXTURE_PATH, SWORD_HEIGHT, "sword", SWORD_ROTATE, SWORD_FLIP)
shield_img = load_overlay_image(SHIELD_TEXTURE_PATH, SHIELD_HEIGHT, "shield")
armor_img = load_overlay_image(ARMOR_TEXTURE_PATH, 160, "armor", ARMOR_ROTATE, ARMOR_FLIP)
gold_img = load_overlay_image(GOLD_TEXTURE_PATH, 64, "gold")
def load_person(path, label):
    img = load_overlay_image(path, PLAYER_HEIGHT, label, PLAYER_ROTATE, PLAYER_FLIP)
    if img is not None and img.get_width() > 120:      # keep it clear of the slots and stats
        img = pygame.transform.smoothscale(
            img, (120, max(1, int(img.get_height() * 120 / img.get_width()))))
    return img

person_imgs = {"male": load_person(MALE_TEXTURE_PATH, "male person"),
               "female": load_person(FEMALE_TEXTURE_PATH, "female person")}
character = "male"        # picked on the main menu

def make_placeholder_menu_bg():
    """Dark purple gradient used when no menu background image is provided."""
    surf = pygame.Surface((W, H))
    for y in range(H):
        f = y / H
        pygame.draw.line(surf, (int(40 - 28 * f), int(22 - 14 * f), int(55 - 30 * f)), (0, y), (W, y))
    return surf

def load_menu_bg(path):
    """Load the main menu background, scaled to cover the window, or draw a gradient."""
    surf = None
    if path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for p in (path, os.path.join(script_dir, path)):
            if os.path.isfile(p):
                try:
                    img = pygame.image.load(p).convert()
                    f = max(W / img.get_width(), H / img.get_height())      # scale to cover, keep aspect
                    img = pygame.transform.smoothscale(
                        img, (max(W, int(img.get_width() * f + 0.5)), max(H, int(img.get_height() * f + 0.5))))
                    surf = pygame.Surface((W, H))
                    surf.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))   # centered crop
                    print(f"Loaded menu background: {p}")
                except Exception as err:
                    print(f"Found '{p}' but could not load the menu background: {err}")
                break
        else:
            print(f"menu background not found: {os.path.abspath(path)} - using drawn version.")
    if surf is None:
        surf = make_placeholder_menu_bg()
    v = max(0, min(255, int(255 * MENU_BG_DIM)))
    surf.fill((v, v, v), special_flags=pygame.BLEND_MULT)
    return surf

menu_bg = load_menu_bg(MENU_BG_TEXTURE_PATH)

def make_placeholder_enemy(h=256):
    """Simple green goblin used when no enemy image is provided."""
    w = int(h * 0.6)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    green, dark = (80, 130, 70), (50, 90, 45)
    pygame.draw.ellipse(surf, green, (w * 0.15, h * 0.35, w * 0.7, h * 0.6))
    pygame.draw.rect(surf, dark, (w * 0.2, h * 0.85, w * 0.2, h * 0.15))
    pygame.draw.rect(surf, dark, (w * 0.6, h * 0.85, w * 0.2, h * 0.15))
    pygame.draw.circle(surf, green, (w // 2, int(h * 0.25)), int(w * 0.27))
    for ex in (0.38, 0.62):
        pygame.draw.circle(surf, (230, 30, 30), (int(w * ex), int(h * 0.23)), int(w * 0.05))
    pygame.draw.line(surf, dark, (w * 0.15, h * 0.5), (w * 0.02, h * 0.75), 8)
    pygame.draw.line(surf, dark, (w * 0.85, h * 0.5), (w * 0.98, h * 0.75), 8)
    return surf

enemy_img = load_overlay_image(ENEMY_TEXTURE_PATH, 256, "enemy")
if enemy_img is None:
    enemy_img = make_placeholder_enemy()
def make_placeholder_potion(h):
    """Simple red potion used when no potion image is provided."""
    w = int(h * 0.6)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    glass = (190, 215, 225)
    pygame.draw.rect(surf, (120, 80, 40), (w * 0.38, 0, w * 0.24, h * 0.12))     # cork
    pygame.draw.rect(surf, glass, (w * 0.4, h * 0.1, w * 0.2, h * 0.25))          # neck
    pygame.draw.circle(surf, glass, (w // 2, int(h * 0.65)), int(w * 0.45))       # glass
    pygame.draw.circle(surf, (200, 30, 40), (w // 2, int(h * 0.67)), int(w * 0.38))  # liquid
    pygame.draw.circle(surf, (255, 150, 150), (int(w * 0.35), int(h * 0.6)), int(w * 0.07))
    return surf

potion_img = load_overlay_image(POTION_TEXTURE_PATH, POTION_HEIGHT, "potion", POTION_ROTATE, POTION_FLIP)
if potion_img is None:
    potion_img = make_placeholder_potion(POTION_HEIGHT)
_ph = 32
potion_icon = pygame.transform.smoothscale(
    potion_img, (max(1, int(potion_img.get_width() * _ph / potion_img.get_height())), _ph))
font = pygame.font.Font(None, 24)
big_font = pygame.font.Font(None, 90)
menu_font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 64)

# ---- Items: (name, cost, stat) - index 0 is what you start with ----
ITEMS = {
    "sword":  [("Rusty Sword", 0, 1), ("Iron Sword", 15, 2), ("Diamond Sword", 40, 3)],           # stat = damage
    "shield": [("Wooden Shield", 0, 70), ("Iron Shield", 12, 90), ("Diamond Shield", 35, 110)],   # stat = block arc (deg)
    "armor":  [("No Armor", 0, 0), ("Leather Armor", 10, 20), ("Iron Armor", 25, 40),
               ("Diamond Armor", 50, 60)],                                                         # stat = % less damage
}
ICON_COLORS = {
    "sword":  [(150, 150, 150), (205, 210, 220), (80, 225, 235)],
    "shield": [(120, 80, 45), (205, 210, 220), (80, 225, 235)],
    "armor":  [None, (150, 95, 55), (205, 210, 220), (80, 225, 235)],
}
# multiplied onto your sword / shield textures so upgrades are visible in your hands
TINTS = {
    "sword":  [(200, 170, 140), (255, 255, 255), (130, 240, 255)],
    "shield": [(210, 160, 110), (255, 255, 255), (130, 240, 255)],
    "armor":  [(255, 255, 255), (200, 150, 110), (255, 255, 255), (130, 240, 255)],   # index 0 = no armor (unused)
}
owned = {"sword": {0}, "shield": {0}, "armor": {0}}
equipped = {"sword": 0, "shield": 0, "armor": 0}
gold = 0
gold_pop = 0       # last gold drop, shown as "+N" next to the gold counter
gold_pop_t = 0.0
potion_level = {k: 0 for k in POTION_UPGRADES}      # how many upgrades of each kind you've bought

POTION_BASE = {"heal": POTION_HEAL, "drop": POTION_DROP_CHANCE, "max": MAX_POTIONS}   # value at level 0

def potion_value(key, lvl):
    steps = POTION_UPGRADES.get(key, {}).get("steps", [])[:lvl]
    total = POTION_BASE[key] + sum(a for _, a in steps)
    return min(1.0, total) if key == "drop" else total

def potion_heal():
    return potion_value("heal", potion_level.get("heal", 0))

def potion_drop_chance():
    return potion_value("drop", potion_level.get("drop", 0))

def potion_max():
    return potion_value("max", potion_level.get("max", 0))

def potion_stat_text(key, lvl):
    v = potion_value(key, lvl)
    if key == "heal":
        return f"Heals {v} HP"
    if key == "drop":
        return f"Drop chance {round(v * 100)}%"
    return f"Max {v} potions"

def stat_text(kind, v):
    return {"sword": f"Damage {v}", "shield": f"Block arc {v}", "armor": f"{v}% less damage"}[kind]

_tint_cache = {}
def tinted(kind, img, idx=None):
    """Your one image for this item type, with the tier color multiplied over it."""
    if img is None:
        return None
    if idx is None:
        idx = equipped[kind]
    key = (kind, idx)
    if key not in _tint_cache:
        t = img.copy()
        t.fill(TINTS[kind][idx], special_flags=pygame.BLEND_RGB_MULT)
        _tint_cache[key] = t
    return _tint_cache[key]

_icon_cache = {}
def item_icon(kind, idx, s):
    """Tinted slot icon built from the same image as the 3D item (None = use the drawn fallback)."""
    key = (kind, idx, s)
    if key not in _icon_cache:
        base = {"sword": sword_img, "shield": shield_img, "armor": armor_img}[kind]
        if base is None:
            _icon_cache[key] = None
        else:
            img = tinted(kind, base, idx)
            if kind == "sword" and ICON_SWORD_ANGLE:
                img = pygame.transform.rotate(img, -ICON_SWORD_ANGLE)
            w, h = img.get_size()
            f = 2 * s / max(w, h)
            _icon_cache[key] = pygame.transform.smoothscale(img, (max(1, int(w * f)), max(1, int(h * f))))
    return _icon_cache[key]

_coin_cache = {}
def draw_coin(surface, cx, cy, r=12):
    if gold_img is not None:
        if r not in _coin_cache:
            gw, gh = gold_img.get_size()
            _coin_cache[r] = pygame.transform.smoothscale(gold_img, (max(1, int(gw * 2 * r / gh)), 2 * r))
        c = _coin_cache[r]
        surface.blit(c, c.get_rect(center=(cx, cy)))
    else:
        pygame.draw.circle(surface, (230, 190, 40), (cx, cy), r)
        pygame.draw.circle(surface, (160, 120, 20), (cx, cy), r, 2)

# ---- Gold fly-to-counter animation ----
COUNTER_X, COUNTER_Y, COUNTER_R = 36, 96, 12   # where the HUD gold coin sits (coins shrink to this size)
fly_coins = []

def gold_shown():
    """Gold on the HUD counter: real gold minus the coins still in the air."""
    return max(0, gold - len(fly_coins))

def enemy_screen_pos(en):
    """Where a dead enemy was on screen (same projection as draw_enemies) + a starting coin radius."""
    dx, dy = en.x - player_x, en.y - player_y
    rel = angle_diff(math.atan2(dy, dx), player_angle)
    cd = math.hypot(dx, dy) * math.cos(rel)
    if cd < 0.25:                                   # behind you or right on top of you
        return W / 2, H * 0.6, 28
    wall_h = H / cd
    sh = wall_h * ENEMY_SCALE
    x = max(30, min(W - 30, W * (rel / FOV + 0.5)))
    y = max(60, min(H - 60, (H + wall_h) / 2 - sh * 0.6))      # about chest height
    return x, y, max(18, min(36, int(sh * 0.1)))

def spawn_gold_coins(en, n):
    """One coin per gold dropped; they pop up out of the enemy one after another."""
    x, y, r0 = enemy_screen_pos(en)
    for i in range(n):
        fly_coins.append({"x0": x + random.uniform(-18, 18), "y0": y + random.uniform(-10, 10),
                          "r0": r0, "t": -i * 0.1, "dur": random.uniform(0.7, 0.9),
                          "bend": random.uniform(-90, 90)})

def update_coins(dt):
    for c in fly_coins:
        c["t"] += dt / c["dur"]
    fly_coins[:] = [c for c in fly_coins if c["t"] < 1]       # landed: counter goes up

def draw_flying_coins(surface):
    for c in fly_coins:
        if c["t"] < 0:
            continue
        e = c["t"] ** 1.5                                      # speeds up as it nears the counter
        px, py = c["x0"], c["y0"]
        cx, cy = px + c["bend"], py - 140                      # curve: up first, then to the counter
        a, b, d = (1 - e) ** 2, 2 * (1 - e) * e, e * e
        x = a * px + b * cx + d * COUNTER_X
        y = a * py + b * cy + d * COUNTER_Y
        r = int(round(c["r0"] + (COUNTER_R - c["r0"]) * e))   # shrinks to the counter's coin size
        draw_coin(surface, int(x), int(y), max(4, r))

# ---- Procedural world: chunks are made on demand and deleted when you leave ----
# A chunk is 64 tiles (8x8) built from a seed + its coordinates, so a deleted chunk
# comes back identical if you walk back to it.
SEED = 0
chunks = {}
_last_chunk = None
START_X = START_Y = 0.5

def gen_chunk(cx, cy):
    rng = random.Random(hash((SEED, cx, cy)))
    c = [1 if rng.random() < WALL_DENSITY else 0 for _ in range(64)]
    if cx in (-1, 0) and cy in (-1, 0):          # keep a 5x5 clear area around the start
        for i in range(64):
            if abs(cx * 8 + (i & 7)) <= 2 and abs(cy * 8 + (i >> 3)) <= 2:
                c[i] = 0
    chunks[(cx, cy)] = c
    return c

def tile(x, y):
    c = chunks.get((x >> 3, y >> 3)) or gen_chunk(x >> 3, y >> 3)
    return c[((y & 7) << 3) | (x & 7)]

def update_chunks():
    """Generate chunks near the player and delete far ones (runs when you cross a chunk edge)."""
    global _last_chunk
    pc = (math.floor(player_x) >> 3, math.floor(player_y) >> 3)
    if pc == _last_chunk:
        return
    _last_chunk = pc
    for dy in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
        for dx in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
            k = (pc[0] + dx, pc[1] + dy)
            if k not in chunks:
                gen_chunk(*k)
    for k in [k for k in chunks if max(abs(k[0] - pc[0]), abs(k[1] - pc[1])) > KEEP_RADIUS]:
        del chunks[k]

def new_map():
    global SEED, _last_chunk
    SEED = random.getrandbits(32)
    chunks.clear()
    _last_chunk = None

new_map()

def is_wall(x, y):
    return tile(math.floor(x), math.floor(y)) == 1
def blocked(x, y, r=PLAYER_RADIUS):
    return (is_wall(x - r, y - r) or is_wall(x + r, y - r) or
            is_wall(x - r, y + r) or is_wall(x + r, y + r))

def cast_ray(px, py, angle, max_dist=10):
    """Fast grid-stepping ray cast (DDA). Returns (distance, u, side) where u is
    0..1 along the wall face and side is True if a vertical (east/west) face was hit."""
    dx, dy = math.cos(angle), math.sin(angle)
    cx, cy = math.floor(px), math.floor(py)
    ddx = abs(1 / dx) if dx else 1e30
    ddy = abs(1 / dy) if dy else 1e30
    if dx < 0:
        step_x, side_x = -1, (px - cx) * ddx
    else:
        step_x, side_x = 1, (cx + 1 - px) * ddx
    if dy < 0:
        step_y, side_y = -1, (py - cy) * ddy
    else:
        step_y, side_y = 1, (cy + 1 - py) * ddy
    while True:
        if side_x < side_y:
            dist = side_x
            side_x += ddx
            cx += step_x
            vertical = True
        else:
            dist = side_y
            side_y += ddy
            cy += step_y
            vertical = False
        if dist > max_dist:
            return max_dist, 0.0, False
        c = chunks.get((cx >> 3, cy >> 3)) or gen_chunk(cx >> 3, cy >> 3)
        if c[((cy & 7) << 3) | (cx & 7)] == 1:
            if vertical:
                u = py + dy * dist - cy
                if dx < 0: u = 1 - u
            else:
                u = px + dx * dist - cx
                if dy > 0: u = 1 - u
            return dist, u, vertical

# ---- Sword & shield overlay ----
def smooth(t):
    return t * t * (3 - 2 * t)

def keyframes(t, frames):
    """Smoothly interpolate through (time, value) keyframes."""
    for (t0, v0), (t1, v1) in zip(frames, frames[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
    return frames[-1][1]

SWING_ANGLE = [(0, 15), (0.25, 50), (0.6, -75), (1, 15)]   # degrees (0 = straight up)
SWING_SHIFT = [(0, 0), (0.25, 0.15), (0.6, 1), (1, 0)]     # how far the sword sweeps left

def place(points, angle_deg, ox, oy, scale=1.0):
    """Rotate local points around (0,0), then move them to (ox, oy)."""
    a = math.radians(angle_deg)
    c, s_ = math.cos(a), math.sin(a)
    return [(ox + (x * c - y * s_) * scale, oy + (x * s_ + y * c) * scale)
            for x, y in points]

def draw_sword(surface, swing_t, drop):
    if swing_t is None:
        angle, shift = 15, 0
    else:
        angle = keyframes(swing_t, SWING_ANGLE)
        shift = keyframes(swing_t, SWING_SHIFT)
    px = W - 170 - shift * 260
    py = H + 20 - shift * 40 + drop

    simg = tinted("sword", sword_img)
    if simg is not None:
        # Rotate around the handle point (SWORD_PIVOT) of the image
        rotated = pygame.transform.rotate(simg, -angle)
        w, h = simg.get_size()
        ox, oy = (SWORD_PIVOT[0] - 0.5) * w, (SWORD_PIVOT[1] - 0.5) * h
        a = math.radians(angle)
        vx = ox * math.cos(a) - oy * math.sin(a)
        vy = ox * math.sin(a) + oy * math.cos(a)
        surface.blit(rotated, rotated.get_rect(center=(px - vx, py - vy)))
        return

    handle = [(-8, 0), (8, 0), (8, -70), (-8, -70)]
    guard = [(-38, -70), (38, -70), (38, -84), (-38, -84)]
    blade = [(-14, -84), (14, -84), (10, -330), (0, -355), (-10, -330)]
    fuller = [(-2, -90), (2, -90), (2, -320), (-2, -320)]

    pygame.draw.polygon(surface, (90, 55, 30), place(handle, angle, px, py))
    pygame.draw.polygon(surface, (200, 170, 60), place(guard, angle, px, py))
    pygame.draw.polygon(surface, (200, 205, 215), place(blade, angle, px, py))
    pygame.draw.polygon(surface, (140, 145, 155), place(fuller, angle, px, py))

def draw_shield(surface, amt):
    e = smooth(amt)
    cx = 150 + (W // 2 - 60 - 150) * e
    cy = (H - 10) + ((H - 210) - (H - 10)) * e
    scale = 1.0 + 0.6 * e

    himg = tinted("shield", shield_img)
    if himg is not None:
        w, h = himg.get_size()
        scaled = pygame.transform.smoothscale(himg, (int(w * scale), int(h * scale)))
        surface.blit(scaled, scaled.get_rect(center=(cx, cy)))
        return

    kite = [(-60, -80), (60, -80), (60, 10), (0, 90), (-60, 10)]
    inner = [(x * 0.82, y * 0.82) for x, y in kite]
    pygame.draw.polygon(surface, (200, 170, 60), place(kite, 0, cx, cy, scale))
    pygame.draw.polygon(surface, (40, 70, 150), place(inner, 0, cx, cy, scale))
    # cross emblem
    pygame.draw.polygon(surface, (200, 170, 60),
                        place([(-6, -60), (6, -60), (6, 55), (-6, 55)], 0, cx, cy, scale))
    pygame.draw.polygon(surface, (200, 170, 60),
                        place([(-40, -20), (40, -20), (40, -8), (-40, -8)], 0, cx, cy, scale))

def draw_potion(surface, t):
    if t is None:
        return
    x = keyframes(t, [(0, W // 2 + 80), (0.2, W // 2 + 80), (0.5, W // 2 + 40), (0.8, W // 2 + 80), (1, W // 2 + 80)])
    y = keyframes(t, [(0, H + 150), (0.2, H - 170), (0.5, H - 290), (0.8, H - 170), (1, H + 150)])
    tilt = keyframes(t, [(0, 0), (0.2, 0), (0.5, -50), (0.8, 0), (1, 0)])
    rotated = pygame.transform.rotate(potion_img, -tilt)
    surface.blit(rotated, rotated.get_rect(center=(x, y)))

# ---- Enemies & HUD ----
class Enemy:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = ENEMY_HEALTH
        self.cooldown = random.uniform(0.6, 1.2)
        self.flash = 0.0

enemies = []
def angle_diff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi

def push(en, dx, dy):
    """Move an enemy by (dx, dy), sliding along walls."""
    if not blocked(en.x + dx, en.y, ENEMY_RADIUS):
        en.x += dx
    if not blocked(en.x, en.y + dy, ENEMY_RADIUS):
        en.y += dy

def spawn_enemy():
    """Spawn one enemy at a random open spot inside the chunk you are standing in.
    Returns False if no open spot was found."""
    ccx, ccy = math.floor(player_x) >> 3, math.floor(player_y) >> 3
    for _ in range(40):
        x, y = ccx * 8 + random.uniform(0.5, 7.5), ccy * 8 + random.uniform(0.5, 7.5)
        if (math.hypot(x - player_x, y - player_y) >= SPAWN_MIN_DIST
                and not blocked(x, y, ENEMY_RADIUS)
                and all(math.hypot(x - e.x, y - e.y) > 0.8 for e in enemies)):
            enemies.append(Enemy(x, y))
            return True
    return False

def sword_hit():
    for en in enemies:
        dx, dy = en.x - player_x, en.y - player_y
        dist = math.hypot(dx, dy)
        if dist < SWORD_RANGE and abs(angle_diff(math.atan2(dy, dx), player_angle)) < math.radians(SWORD_ARC_DEG):
            en.hp -= ITEMS["sword"][equipped["sword"]][2]
            en.flash = 0.15
            if dist > 0:
                push(en, dx / dist * 0.5, dy / dist * 0.5)  # knockback

def update_enemies(dt):
    global player_health, damage_flash, spawn_timer, kills, potions, gold, gold_pop, gold_pop_t
    # enemies only live in your chunk: leave it and the old ones are deleted (new ones spawn below)
    pk = (math.floor(player_x) >> 3, math.floor(player_y) >> 3)
    enemies[:] = [e for e in enemies if (math.floor(e.x) >> 3, math.floor(e.y) >> 3) == pk]
    for en in enemies:
        en.flash = max(0.0, en.flash - dt)
        en.cooldown -= dt
        dx, dy = player_x - en.x, player_y - en.y
        dist = math.hypot(dx, dy) or 0.001

        if dist > ENEMY_ATTACK_RANGE * 0.8:
            step = ENEMY_SPEED * dt
            push(en, dx / dist * step, dy / dist * step)

        # keep enemies from stacking on each other
        for other in enemies:
            if other is not en:
                ox, oy = en.x - other.x, en.y - other.y
                od = math.hypot(ox, oy)
                if 0 < od < 0.5:
                    strength = 3 * (0.5 - od) * dt
                    push(en, ox / od * strength, oy / od * strength)

        if dist <= ENEMY_ATTACK_RANGE and en.cooldown <= 0:
            en.cooldown = ENEMY_ATTACK_COOLDOWN
            in_front = abs(angle_diff(math.atan2(-dy, -dx), player_angle)) < math.radians(ITEMS["shield"][equipped["shield"]][2])
            if shield_amt > 0.6 and in_front:
                push(en, -dx / dist * 0.4, -dy / dist * 0.4)   # blocked: knocked back
            else:
                dmg = max(1, round(ENEMY_DAMAGE * (100 - ITEMS["armor"][equipped["armor"]][2]) / 100))
                player_health = max(0, player_health - dmg)
                damage_flash = 0.3

    alive_list = [e for e in enemies if e.hp > 0]
    for dead in [e for e in enemies if e.hp <= 0]:
        if random.random() < potion_drop_chance():
            potions = min(potion_max(), potions + 1)
        drop = random.randint(GOLD_MIN, GOLD_MAX)
        gold += drop
        gold_pop, gold_pop_t = drop, 1.2
        spawn_gold_coins(dead, drop)
    kills += len(enemies) - len(alive_list)
    enemies[:] = alive_list
    # always keep exactly ENEMY_COUNT enemies in your chunk
    while len(enemies) < ENEMY_COUNT and spawn_enemy():
        pass

def draw_enemies(surface, px, py, pang, zbuf):
    order = sorted(enemies, key=lambda e: -math.hypot(e.x - px, e.y - py))
    img_aspect = enemy_img.get_width() / enemy_img.get_height()
    for en in order:
        dx, dy = en.x - px, en.y - py
        dist = math.hypot(dx, dy)
        rel = angle_diff(math.atan2(dy, dx), pang)
        if abs(rel) > FOV / 2 + 0.5:
            continue
        cd = dist * math.cos(rel)          # fisheye-corrected distance
        if cd < 0.25:
            continue
        wall_h = H / cd
        sh = int(wall_h * ENEMY_SCALE)
        sw = int(sh * img_aspect)
        if sh < 2 or sw < 1:
            continue
        sprite = pygame.transform.scale(enemy_img, (sw, sh))
        if en.flash > 0:
            sprite.fill((140, 40, 40), special_flags=pygame.BLEND_RGB_ADD)
        shade = max(35, int(255 / (1 + cd * cd * 0.5)))
        sprite.fill((shade, shade, shade), special_flags=pygame.BLEND_MULT)

        screen_x = W * (rel / FOV + 0.5)
        left = int(screen_x - sw / 2)
        top = int((H + wall_h) / 2 - sh)    # feet on the floor
        for x in range(max(0, left), min(W, left + sw)):
            if cd < zbuf[x]:                # only draw where no wall is in front
                surface.blit(sprite, (x, top), area=(x - left, 0, 1, sh))

def draw_hud(surface):
    bx, by, bw, bh = 20, 16, 300, 22
    pygame.draw.rect(surface, (40, 0, 0), (bx, by, bw, bh))
    fill = int(bw * player_health / PLAYER_MAX_HEALTH)
    if fill > 0:
        pygame.draw.rect(surface, (210, 20, 20), (bx, by, fill, bh))
    pygame.draw.rect(surface, (230, 230, 230), (bx, by, bw, bh), 2)
    label = font.render(f"{player_health} / {PLAYER_MAX_HEALTH}", True, (255, 255, 255))
    surface.blit(label, label.get_rect(center=(bx + bw // 2, by + bh // 2)))
    kt = font.render(f"Kills: {kills}", True, (255, 255, 255))
    surface.blit(kt, (W - kt.get_width() - 20, by + 2))
    surface.blit(potion_icon, (20, 46))
    pt = font.render(f"x {potions}   [R] drink", True, (255, 255, 255))
    surface.blit(pt, (20 + potion_icon.get_width() + 8, 54))
    draw_coin(surface, COUNTER_X, COUNTER_Y, COUNTER_R)
    gt = font.render(f"x {gold_shown()}", True, (255, 230, 120))
    surface.blit(gt, (54, 88))
    if gold_pop_t > 0:
        pt2 = font.render(f"+{gold_pop}", True, (255, 230, 120))
        pt2.set_alpha(int(255 * min(1.0, gold_pop_t / 0.5)))
        surface.blit(pt2, (54 + gt.get_width() + 10, 88))

player_x, player_y = START_X, START_Y
player_angle = random.uniform(0, 2 * math.pi)

vel_x, vel_y = 0.0, 0.0   # smoothed velocity
mouse_dx_smooth = 0.0     # smoothed mouse movement

swing_t = None            # None = not swinging, else 0..1 progress
shield_amt = 0.0          # 0 = lowered, 1 = fully raised
blocking = False
swing_hit = False         # has this swing already landed?
player_health = PLAYER_MAX_HEALTH
kills = 0
spawn_timer = 1.5
damage_flash = 0.0
potions = START_POTIONS
drinking_t = None         # None = not drinking, else 0..1 progress
drink_healed = False

flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
death_surf = pygame.Surface((W, H), pygame.SRCALPHA)
death_surf.fill((80, 0, 0, 150))

def reset_game():
    global player_x, player_y, player_angle, vel_x, vel_y, swing_t, swing_hit
    global shield_amt, blocking, player_health, kills, spawn_timer, damage_flash
    global potions, drinking_t, drink_healed, gold, gold_pop_t
    new_map()                                  # fresh random map every restart
    player_x, player_y, player_angle = START_X, START_Y, random.uniform(0, 2 * math.pi)
    gold, gold_pop_t = 0, 0.0
    owned.update({"sword": {0}, "shield": {0}, "armor": {0}})
    equipped.update({"sword": 0, "shield": 0, "armor": 0})
    potion_level.update({k: 0 for k in POTION_UPGRADES})
    vel_x = vel_y = 0.0
    swing_t, swing_hit, blocking, shield_amt = None, False, False, 0.0
    player_health, kills, spawn_timer, damage_flash = PLAYER_MAX_HEALTH, 0, 1.5, 0.0
    potions, drinking_t, drink_healed = START_POTIONS, None, False
    enemies.clear()
    fly_coins.clear()

# ---- Fullscreen & pause menu ----
fullscreen = False

def toggle_fullscreen():
    global win, fullscreen
    fullscreen = not fullscreen
    try:
        pygame.display.toggle_fullscreen()
    except pygame.error:
        pygame.display.set_mode((W, H), pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0))
    win = pygame.display.get_surface()
    pygame.event.set_grab(not paused)

# Add new menu buttons here: (label, page name). Quit/Resume are special.
MENU_BUTTONS = [("Resume", "resume"), ("Controls", "controls"), ("Inventory", "inventory"),
                ("Shop", "shop"), ("Quit To Main Menu", "quit")]

# Add text for new pages here (one string per line).
MENU_PAGES = {
    "controls": [
        "W / A / S / D   -   Move and strafe",
        "Mouse   -   Look left / right",
        "Left Click   -   Swing sword",
        "Right Click (hold)   -   Block with shield",
        "R   -   Drink potion  (restart when dead)",
        "Esc   -   Pause menu  (also goes back)",
        "F4   -   Toggle fullscreen",
        "Quit   -   Use the menu buttons",
    ],
    "settings": ["Coming soon..."],
}

BTN_W, BTN_H, BTN_GAP = 300, 50, 14
paused = False
menu_page = "main"
pause_bg = None
pause_dim = pygame.Surface((W, H), pygame.SRCALPHA)
pause_dim.fill((0, 0, 0, 170))

def set_paused(value):
    global paused, menu_page, pause_bg, mouse_dx_smooth
    paused = value
    menu_page = "main"
    if value:
        pause_bg = win.copy()               # freeze the last frame as the backdrop
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    else:
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.get_rel()              # avoid a camera jump on resume
        mouse_dx_smooth = 0.0

def menu_rects():
    if menu_page == "main":
        total = len(MENU_BUTTONS) * BTN_H + (len(MENU_BUTTONS) - 1) * BTN_GAP
        top = (H - total) // 2 + 30
        return [(label, action,
                 pygame.Rect((W - BTN_W) // 2, top + i * (BTN_H + BTN_GAP), BTN_W, BTN_H))
                for i, (label, action) in enumerate(MENU_BUTTONS)]
    return [("Back", "back", pygame.Rect((W - BTN_W) // 2, H - 110, BTN_W, BTN_H))]

# ---- Item icons, inventory and shop pages ----
def draw_icon(surface, kind, idx, cx, cy, s=26):
    if kind == "armor" and idx == 0:
        return
    icon = item_icon(kind, idx, s)
    if icon is not None:
        surface.blit(icon, icon.get_rect(center=(cx, cy)))
        return
    col = ICON_COLORS[kind][idx]      # no image set: use the drawn fallback below
    dark = (35, 35, 40)
    if kind == "sword":
        pygame.draw.line(surface, (90, 55, 30), (cx - s * 0.3, cy + s * 0.3), (cx - s * 0.65, cy + s * 0.65), 5)
        pygame.draw.line(surface, col, (cx - s * 0.3, cy + s * 0.3), (cx + s * 0.6, cy - s * 0.6), max(4, int(s * 0.28)))
        pygame.draw.line(surface, (200, 170, 60), (cx - s * 0.55, cy + s * 0.05), (cx - s * 0.05, cy + s * 0.55), 5)
    elif kind == "shield":
        pts = [(-.6, -.7), (.6, -.7), (.6, .1), (0, .8), (-.6, .1)]
        pygame.draw.polygon(surface, col, [(cx + x * s, cy + y * s) for x, y in pts])
        pygame.draw.polygon(surface, dark, [(cx + x * s, cy + y * s) for x, y in pts], 2)
        pygame.draw.line(surface, dark, (cx, cy - s * 0.6), (cx, cy + s * 0.6), 2)
        pygame.draw.line(surface, dark, (cx - s * 0.45, cy - s * 0.2), (cx + s * 0.45, cy - s * 0.2), 2)
    else:
        pts = [(-.8, -.5), (-.4, -.75), (-.15, -.55), (.15, -.55), (.4, -.75), (.8, -.5),
               (.6, -.1), (.55, .7), (-.55, .7), (-.6, -.1)]
        pygame.draw.polygon(surface, col, [(cx + x * s, cy + y * s) for x, y in pts])
        pygame.draw.polygon(surface, dark, [(cx + x * s, cy + y * s) for x, y in pts], 2)

def draw_slot(surface, rect, hover=False):
    pygame.draw.rect(surface, (139, 139, 139), rect)
    pygame.draw.rect(surface, (55, 55, 55), rect, 3)
    if hover:
        hl = pygame.Surface(rect.size, pygame.SRCALPHA)
        hl.fill((255, 255, 255, 70))
        surface.blit(hl, rect)

def equip_slot_rects():
    return {"armor": pygame.Rect(120, 150, 64, 64), "sword": pygame.Rect(120, 226, 64, 64),
            "shield": pygame.Rect(120, 302, 64, 64)}

def bag_items():
    """Owned items that aren't equipped (armor 0 = 'no armor' isn't an item)."""
    out = []
    for kind in ("sword", "shield", "armor"):
        for idx in sorted(owned[kind]):
            if idx != equipped[kind] and not (kind == "armor" and idx == 0):
                out.append((kind, idx))
    return out

def bag_rects():
    return [pygame.Rect(124 + i * 62, 400, 56, 56) for i in range(9)]

def draw_gold_label(surface):
    gt = menu_font.render(str(gold), True, (255, 230, 120))
    x = W // 2 - (36 + gt.get_width()) // 2
    draw_coin(surface, x + 13, 128, 13)
    surface.blit(gt, (x + 36, 128 - gt.get_height() // 2))

def draw_person(surface, px, py, bottom, armor_idx=None):
    """The person for the picked character: your image, or a drawn figure (head at py)."""
    pimg = person_imgs[character]
    if pimg is not None:
        surface.blit(pimg, pimg.get_rect(midbottom=(px, bottom)))
        return
    if armor_idx is None:
        armor_idx = equipped["armor"]
    armor_col = ICON_COLORS["armor"][armor_idx] or (90, 120, 170)
    if character == "female":
        pygame.draw.rect(surface, (110, 70, 40), (px - 20, py + 4, 40, 60), border_radius=14)   # long hair
    pygame.draw.circle(surface, (225, 190, 150), (px, py + 18), 18)
    if character == "male":
        pygame.draw.rect(surface, (80, 55, 35), (px - 16, py + 1, 32, 9))                        # short hair
    pygame.draw.rect(surface, armor_col, (px - 24, py + 38, 48, 70))
    pygame.draw.rect(surface, armor_col, (px - 40, py + 40, 14, 60))
    pygame.draw.rect(surface, armor_col, (px + 26, py + 40, 14, 60))
    pygame.draw.rect(surface, (60, 60, 90), (px - 22, py + 108, 20, 60))
    pygame.draw.rect(surface, (60, 60, 90), (px + 2, py + 108, 20, 60))

def draw_inventory(surface):
    mouse = pygame.mouse.get_pos()
    draw_gold_label(surface)

    for kind, rect in equip_slot_rects().items():
        draw_slot(surface, rect, rect.collidepoint(mouse))
        draw_icon(surface, kind, equipped[kind], rect.centerx, rect.centery)
    px, py = 255, 160
    draw_person(surface, px, py, 366)

    lines = [
        f"Sword:  {ITEMS['sword'][equipped['sword']][0]}  ({stat_text('sword', ITEMS['sword'][equipped['sword']][2])})",
        f"Shield:  {ITEMS['shield'][equipped['shield']][0]}  ({stat_text('shield', ITEMS['shield'][equipped['shield']][2])})",
        f"Armor:  {ITEMS['armor'][equipped['armor']][0]}  ({stat_text('armor', ITEMS['armor'][equipped['armor']][2])})",
        f"Potions:  {potions}/{potion_max()}  (heals {potion_heal()})",
    ]
    y = 175
    for line in lines:
        surface.blit(font.render(line, True, (230, 230, 230)), (330, y))
        y += 34
    surface.blit(font.render("Click an item in the bag to equip it.", True, (170, 170, 170)), (330, y + 10))
    surface.blit(font.render("Click your armor to take it off.", True, (170, 170, 170)), (330, y + 34))

    surface.blit(font.render("Bag", True, (230, 230, 230)), (124, 378))
    items = bag_items()
    for i, rect in enumerate(bag_rects()):
        draw_slot(surface, rect, rect.collidepoint(mouse) and i < len(items))
        if i < len(items):
            draw_icon(surface, items[i][0], items[i][1], rect.centerx, rect.centery, 22)
    for i, rect in enumerate(bag_rects()):
        if i < len(items) and rect.collidepoint(mouse):
            kind, idx = items[i]
            name = ITEMS[kind][idx][0]
            tip = font.render(f"{name} - {stat_text(kind, ITEMS[kind][idx][2])}", True, (255, 255, 255))
            surface.blit(tip, tip.get_rect(center=(W // 2, 470)))

def shop_cards():
    out = []
    for ci, kind in enumerate(("sword", "shield", "armor")):
        for j in range(1, len(ITEMS[kind])):
            out.append((kind, j, pygame.Rect(50 + ci * 240, 180 + (j - 1) * 80, 220, 70)))
    return out

shop_tab = "gear"      # "gear" or "potions"

def tier_unlocked(kind, j):
    """Gear has to be bought in order: you need the previous tier before you can buy this one."""
    return (j - 1) in owned[kind]

def shop_tab_rects():
    return {"gear": pygame.Rect(50, 112, 110, 32), "potions": pygame.Rect(170, 112, 110, 32)}

def potion_cards():
    return [(key, pygame.Rect(50 + (i % 2) * 360, 190 + (i // 2) * 125, 340, 110))
            for i, key in enumerate(POTION_UPGRADES)]

def draw_shop(surface):
    mouse = pygame.mouse.get_pos()
    draw_gold_label(surface)
    for tab, rect in shop_tab_rects().items():
        active = tab == shop_tab
        pygame.draw.rect(surface, (120, 30, 30) if active or rect.collidepoint(mouse) else (50, 50, 60),
                         rect, border_radius=6)
        pygame.draw.rect(surface, (230, 230, 230), rect, 2, border_radius=6)
        lt = font.render(tab.capitalize(), True, (255, 255, 255))
        surface.blit(lt, lt.get_rect(center=rect.center))
    if shop_tab == "potions":
        draw_potion_shop(surface, mouse)
        return
    for ci, name in enumerate(("Swords", "Shields", "Armor")):
        h = font.render(name, True, (230, 230, 230))
        surface.blit(h, h.get_rect(center=(160 + ci * 240, 160)))
    for kind, j, rect in shop_cards():
        name, cost, stat = ITEMS[kind][j]
        if equipped[kind] == j:
            status, scol = "EQUIPPED", (120, 220, 120)
        elif j in owned[kind]:
            status, scol = "OWNED", (170, 170, 170)
        elif not tier_unlocked(kind, j):
            status, scol = "Locked", (110, 110, 110)
        elif gold >= cost:
            status, scol = f"Buy - {cost} gold", (255, 230, 120)
        else:
            status, scol = f"{cost} gold", (220, 90, 90)
        locked = j not in owned[kind] and not tier_unlocked(kind, j)
        hover = rect.collidepoint(mouse) and j not in owned[kind] and not locked
        bg = (38, 38, 44) if locked else ((120, 30, 30) if hover else (50, 50, 60))
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, (120, 120, 120) if locked else (230, 230, 230), rect, 2, border_radius=8)
        draw_icon(surface, kind, j, rect.x + 32, rect.centery, 22)
        surface.blit(font.render(name, True, (130, 130, 130) if locked else (255, 255, 255)), (rect.x + 66, rect.y + 8))
        surface.blit(font.render(stat_text(kind, stat), True, (110, 110, 110) if locked else (190, 190, 190)), (rect.x + 66, rect.y + 28))
        surface.blit(font.render(status, True, scol), (rect.x + 66, rect.y + 48))
        if locked and rect.collidepoint(mouse):
            tip = font.render(f"Buy the {ITEMS[kind][j - 1][0]} first", True, (255, 220, 120))
            surface.blit(tip, tip.get_rect(center=(W // 2, 440)))

def draw_potion_shop(surface, mouse):
    for key, rect in potion_cards():
        steps = POTION_UPGRADES[key]["steps"]
        lvl = potion_level[key]
        maxed = lvl >= len(steps)
        pygame.draw.rect(surface, (120, 30, 30) if rect.collidepoint(mouse) and not maxed else (50, 50, 60),
                         rect, border_radius=8)
        pygame.draw.rect(surface, (230, 230, 230), rect, 2, border_radius=8)
        surface.blit(potion_icon, potion_icon.get_rect(center=(rect.x + 30, rect.y + 36)))
        surface.blit(font.render(POTION_UPGRADES[key]["name"], True, (255, 255, 255)), (rect.x + 62, rect.y + 10))
        surface.blit(font.render(potion_stat_text(key, lvl), True, (190, 190, 190)), (rect.x + 62, rect.y + 32))
        for i in range(len(steps)):                       # level pips
            col = (120, 220, 120) if i < lvl else (30, 30, 36)
            pygame.draw.circle(surface, col, (rect.x + 70 + i * 24, rect.y + 62), 8)
            pygame.draw.circle(surface, (230, 230, 230), (rect.x + 70 + i * 24, rect.y + 62), 8, 2)
        if maxed:
            status, scol = "MAX LEVEL", (120, 220, 120)
        else:
            cost = steps[lvl][0]
            nxt = potion_stat_text(key, lvl + 1)
            if gold >= cost:
                status, scol = f"Upgrade: {nxt} - {cost} gold", (255, 230, 120)
            else:
                status, scol = f"Upgrade: {nxt} - {cost} gold", (220, 90, 90)
        surface.blit(font.render(status, True, scol), (rect.x + 14, rect.y + 84))

def buy_potion_upgrade(key):
    steps = POTION_UPGRADES[key]["steps"]
    lvl = potion_level[key]
    global gold
    if lvl < len(steps) and gold >= steps[lvl][0]:
        gold -= steps[lvl][0]
        potion_level[key] += 1

def page_click(pos):
    """Clicks inside the inventory / shop pages."""
    global shop_tab
    if menu_page == "shop":
        for tab, rect in shop_tab_rects().items():
            if rect.collidepoint(pos):
                shop_tab = tab
                return
        if shop_tab == "potions":
            for key, rect in potion_cards():
                if rect.collidepoint(pos):
                    buy_potion_upgrade(key)
            return
        for kind, j, rect in shop_cards():
            if (rect.collidepoint(pos) and j not in owned[kind] and tier_unlocked(kind, j)
                    and gold >= ITEMS[kind][j][1]):
                buy(kind, j)
    elif menu_page == "inventory":
        items = bag_items()
        for i, rect in enumerate(bag_rects()):
            if i < len(items) and rect.collidepoint(pos):
                kind, idx = items[i]
                equipped[kind] = idx
                return
        if equip_slot_rects()["armor"].collidepoint(pos):
            equipped["armor"] = 0

def buy(kind, j):
    global gold
    gold -= ITEMS[kind][j][1]
    owned[kind].add(j)
    if j > equipped[kind]:          # auto-equip upgrades
        equipped[kind] = j

def menu_click(pos):
    global menu_page
    if menu_page in ("shop", "inventory"):
        page_click(pos)
    for label, action, rect in menu_rects():
        if rect.collidepoint(pos):
            if action == "resume":
                set_paused(False)
            elif action == "quit":
                go_to_main_menu()
            elif action == "back":
                menu_page = "main"
            else:
                menu_page = action
            return

def draw_pause_menu(surface):
    title = "PAUSED" if menu_page == "main" else menu_page.upper()
    t = title_font.render(title, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=(W // 2, 90)))

    if menu_page == "inventory":
        draw_inventory(surface)
    elif menu_page == "shop":
        draw_shop(surface)
    elif menu_page != "main":
        lines = MENU_PAGES.get(menu_page, ["Coming soon..."])
        y = 170
        for line in lines:
            txt = menu_font.render(line, True, (230, 230, 230))
            surface.blit(txt, txt.get_rect(center=(W // 2, y)))
            y += 42

    mouse = pygame.mouse.get_pos()
    for label, action, rect in menu_rects():
        hover = rect.collidepoint(mouse)
        pygame.draw.rect(surface, (120, 30, 30) if hover else (50, 50, 60), rect, border_radius=8)
        pygame.draw.rect(surface, (230, 230, 230), rect, 2, border_radius=8)
        txt = menu_font.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))

# ---- Main menu ----
state = "menu"            # "menu" = main menu, "playing" = in the game
MM_X = 150                # left edge of the main menu buttons

def main_menu_buttons():
    items = [("Play", "play"), (f"Character: {character.title()}", "character"),
             ("Quit to Desktop", "quit")]
    return [(label, action, pygame.Rect(MM_X, 250 + i * (BTN_H + BTN_GAP), BTN_W, BTN_H))
            for i, (label, action) in enumerate(items)]

def draw_main_menu(surface):
    surface.blit(menu_bg, (0, 0))
    t = big_font.render(GAME_TITLE, True, (255, 255, 255))
    if t.get_width() > 440:                                # long title: shrink to fit
        t = pygame.transform.smoothscale(t, (440, max(1, int(t.get_height() * 440 / t.get_width()))))
    surface.blit(t, t.get_rect(center=(MM_X + BTN_W // 2, 160)))
    draw_person(surface, 600, 230, 398, armor_idx=0)      # preview of the picked character
    mouse = pygame.mouse.get_pos()
    for label, action, rect in main_menu_buttons():
        hover = rect.collidepoint(mouse)
        pygame.draw.rect(surface, (120, 30, 30) if hover else (50, 50, 60), rect, border_radius=8)
        pygame.draw.rect(surface, (230, 230, 230), rect, 2, border_radius=8)
        txt = menu_font.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))

def start_game():
    global state, mouse_dx_smooth
    reset_game()                                # fresh world, gear, gold and enemies every run
    state = "playing"
    mouse_dx_smooth = 0.0
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.mouse.get_rel()                      # avoid a camera jump

def go_to_main_menu():
    global state, paused, menu_page
    state, paused, menu_page = "menu", False, "main"
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

def main_menu_click(pos):
    global character
    for label, action, rect in main_menu_buttons():
        if rect.collidepoint(pos):
            if action == "play":
                start_game()
            elif action == "character":
                character = "female" if character == "male" else "male"
            elif action == "quit":
                pygame.quit(); sys.exit()
            return

# Start on the main menu (the mouse is only captured once you press Play)
pygame.mouse.set_visible(True)
pygame.event.set_grab(False)

while True:
    dt = min(clock.tick(60) / 1000.0, 0.05)
    alive = player_health > 0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        # Left click = swing sword (only if not blocking or already swinging)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F4:
            toggle_fullscreen()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and state == "playing":
            if paused and menu_page != "main":
                menu_page = "main"                  # Esc inside Controls / Inventory / Shop goes back
            else:
                set_paused(not paused)              # Esc opens / closes the pause menu
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if state == "menu":
                main_menu_click(e.pos)
            elif paused:
                menu_click(e.pos)
            elif swing_t is None and not blocking and alive and drinking_t is None:
                swing_t = 0.0
                swing_hit = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_r and not paused and state == "playing":
            if not alive:
                reset_game()
            elif (drinking_t is None and swing_t is None and not blocking
                  and potions > 0 and player_health < PLAYER_MAX_HEALTH):
                drinking_t = 0.0
                drink_healed = False

    # ---- Main menu: nothing else runs until you press Play ----
    if state == "menu":
        draw_main_menu(win)
        pygame.display.flip()
        continue

    # ---- Paused: draw the menu over the frozen frame and skip the game ----
    if paused:
        win.blit(pause_bg, (0, 0))
        win.blit(pause_dim, (0, 0))
        draw_pause_menu(win)
        pygame.display.flip()
        continue

    # ---- Mouse look (smoothed) ----
    raw_dx, _ = pygame.mouse.get_rel()
    if not alive:
        raw_dx = 0
    mouse_dx_smooth += (raw_dx - mouse_dx_smooth) * (1 - math.exp(-MOUSE_SMOOTH * dt))
    player_angle += mouse_dx_smooth * MOUSE_SENS

    # ---- WASD movement (smoothed) ----
    keys = pygame.key.get_pressed()
    forward = (keys[pygame.K_w] - keys[pygame.K_s]) if alive else 0
    strafe = (keys[pygame.K_d] - keys[pygame.K_a]) if alive else 0

    # Normalize so diagonals aren't faster
    length = math.hypot(forward, strafe)
    if length:
        forward /= length
        strafe /= length

    cos_a, sin_a = math.cos(player_angle), math.sin(player_angle)
    target_vx = (cos_a * forward - sin_a * strafe) * MOVE_SPEED
    target_vy = (sin_a * forward + cos_a * strafe) * MOVE_SPEED

    k = 1 - math.exp(-MOVE_SMOOTH * dt)
    vel_x += (target_vx - vel_x) * k
    vel_y += (target_vy - vel_y) * k

    # Move each axis separately so you slide along walls
    new_x = player_x + vel_x * dt
    if not blocked(new_x, player_y):
        player_x = new_x
    new_y = player_y + vel_y * dt
    if not blocked(player_x, new_y):
        player_y = new_y

    # ---- Sword / shield state ----
    if swing_t is not None:
        swing_t += dt / SWING_TIME
        if swing_t >= 1:
            swing_t = None
    # Right mouse button held = block (not while swinging)
    blocking = pygame.mouse.get_pressed()[2] and swing_t is None and drinking_t is None and alive
    target = 1.0 if blocking else 0.0
    shield_amt += (target - shield_amt) * (1 - math.exp(-SHIELD_SPEED * dt))

    # Sword lands partway through the swing
    if swing_t is not None and not swing_hit and swing_t >= SWING_HIT_AT:
        swing_hit = True
        sword_hit()

    # ---- Potion ----
    if not alive:
        drinking_t = None
    if drinking_t is not None:
        drinking_t += dt / POTION_TIME
        if not drink_healed and drinking_t >= 0.5:      # heal at the moment of drinking
            drink_healed = True
            potions -= 1
            player_health = min(PLAYER_MAX_HEALTH, player_health + potion_heal())
        if drinking_t >= 1:
            drinking_t = None
    drink_pose = (keyframes(drinking_t, [(0, 0), (0.2, 1), (0.8, 1), (1, 0)])
                  if drinking_t is not None else 0.0)

    # ---- World chunks (generate nearby, delete far away) ----
    update_chunks()
    gold_pop_t = max(0.0, gold_pop_t - dt)
    update_coins(dt)

    # ---- Enemies ----
    damage_flash = max(0.0, damage_flash - dt)
    if alive:
        update_enemies(dt)

    # ---- Render ----
    draw_floor_roof(win, player_x, player_y, player_angle)
    fov = FOV
    zbuf = [0.0] * W
    for i in range(W):
        ray_angle = player_angle - fov/2 + fov * i / W
        d, u, side = cast_ray(player_x, player_y, ray_angle)
        # Correct fisheye distortion
        d *= math.cos(ray_angle - player_angle)
        zbuf[i] = d

        full_h = max(1, int(H / (d + 0.001)))
        tx = min(TEX_W - 1, int(u * TEX_W))

        # If the wall is taller than the screen, only sample the visible slice
        if full_h > H:
            src_h = max(1, int(TEX_H * H / full_h))
            src_y = (TEX_H - src_h) // 2
            draw_h = H
        else:
            src_h, src_y, draw_h = TEX_H, 0, full_h

        col = pygame.transform.scale(
            wall_tex.subsurface((tx, src_y, 1, src_h)), (1, draw_h))

        # Distance shading (east/west faces a bit darker for depth)
        shade = max(0, int(255 / (1 + d * d * 0.5)))
        if side:
            shade = int(shade * 0.75)
        col.fill((shade, shade, shade), special_flags=pygame.BLEND_MULT)

        win.blit(col, (i, (H - draw_h) // 2))

    draw_enemies(win, player_x, player_y, player_angle, zbuf)

    # ---- Overlay ----
    draw_sword(win, swing_t, drop=max(shield_amt, drink_pose) * 220)
    draw_shield(win, shield_amt)
    draw_potion(win, drinking_t)
    draw_hud(win)
    draw_flying_coins(win)

    if damage_flash > 0:
        flash_surf.fill((200, 0, 0, int(140 * damage_flash / 0.3)))
        win.blit(flash_surf, (0, 0))

    if not alive:
        win.blit(death_surf, (0, 0))
        t1 = big_font.render("YOU DIED", True, (255, 255, 255))
        t2 = font.render(f"Kills: {kills}   -   Press R to restart", True, (230, 230, 230))
        win.blit(t1, t1.get_rect(center=(W // 2, H // 2 - 20)))
        win.blit(t2, t2.get_rect(center=(W // 2, H // 2 + 40)))
    pygame.display.flip()