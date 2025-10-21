#Mikael Oganesyan --- main!=poss
import pygame, sys, math
pygame.init()
import traceback

# Global exception hook to show uncaught exceptions in the terminal
def _excepthook(type, value, tb):
    traceback.print_exception(type, value, tb)
    try:
        input("Program crashed. Press Enter to exit.")
    except Exception:
        pass

sys.excepthook = _excepthook

# Screen Setup
TILE_SIZE = 32
# window size now matches camera viewport (20 tiles)
WIDTH, HEIGHT = 640, 542
screen = pygame.display.set_mode((WIDTH, HEIGHT))
is_fullscreen = False
clock = pygame.time.Clock()
SPEED = 2
ATTACK_SPEED = 2.5
ROLL_COOLDOWN = 1000
ROLL_TIME = 450
ROLL_SPEED = 5
# Player circular hitbox radius (pixels)
PLAYER_HIT_RADIUS = 16
# How far the sword hitbox is offset away from the player (pixels)
SWORD_HIT_OFFSET = 4
SWORD_DIAG_OFFSET = SWORD_HIT_OFFSET + 16
# Loading Tile Images
grass = pygame.image.load("assets/tiles/misc/grass.png").convert_alpha()
rock = pygame.image.load("assets/tiles/misc/rock.png").convert_alpha()
water = pygame.image.load("assets/tiles/misc/water.png").convert_alpha()
lava = pygame.image.load("assets/tiles/misc/lava.png").convert_alpha()
chest = pygame.image.load("assets/tiles/misc/chest.png").convert_alpha()
pathway = pygame.image.load("assets/tiles/misc/pathway.png").convert_alpha()
cobblestone = pygame.image.load("assets/tiles/misc/cobblestone.png").convert_alpha()

tiles = {0: grass, 1: rock, 2: water, 3: lava, 4: chest, 5: pathway, 6: cobblestone}

# Load building tiles (tavern) for area1 if available
try:
    tavern_img = pygame.image.load("assets/tiles/buildings/tavern.png").convert_alpha()
    # compute tavern tile dimensions (assume tavern image is multiple of TILE_SIZE)
    tavern_tiles_w = max(1, tavern_img.get_width() // TILE_SIZE)
    tavern_tiles_h = max(1, tavern_img.get_height() // TILE_SIZE)
    tavern_subs = {}
    for by in range(tavern_tiles_h):
        for bx in range(tavern_tiles_w):
            rect = pygame.Rect(bx * TILE_SIZE, by * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            # get tavern tile (may contain transparency)
            try:
                tile_part = tavern_img.subsurface(rect).copy()
            except Exception:
                tile_part = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            # composite onto cobblestone so transparent areas show cobblestone
            comp = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            try:
                comp.blit(cobblestone, (0, 0))
            except Exception:
                comp.fill((0,0,0,0))
            comp.blit(tile_part, (0, 0))
            tavern_subs[(bx, by)] = comp
    # default tavern placement in area1 (tile coords)
    tavern_origin = (14, 4)  # top-left tile where tavern will be placed in area1
except Exception:
    tavern_img = None
    tavern_subs = {}
    tavern_origin = None

# --- Map ---
tilemap = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,5,5,5,0,0,0,0,0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,5,5,5,5,5,0,0,0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,2,2,5,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,2,2,2,0,0,5,5,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,5,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,5,5,5,5,5,5,5,5,5,0,0,0,0],
    [0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,5,5,5,5,5,5,5,5,5,5],
    [2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,5,5,5],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ]

#Load walking frames (3 frames)
walk_right = [pygame.image.load(f"assets/animations/kirby_right{i}.png").convert_alpha() for i in range(1,4)] 
walk_left = [pygame.transform.rotate(img, 180) for img in walk_right]
walk_up = [pygame.transform.rotate(img, 90) for img in walk_right]
walk_down = [pygame.transform.rotate(img, -90) for img in walk_right]
walk_up_left = [pygame.transform.rotate(img, 135) for img in walk_right]
walk_up_right = [pygame.transform.rotate(img, 45) for img in walk_right]
walk_down_left = [pygame.transform.rotate(img, 225) for img in walk_right]
walk_down_right = [pygame.transform.rotate(img, -45) for img in walk_right]

#Attack animation (3 frames) 
swing_right = [pygame.image.load(f"assets/animations/kirby_sword_right{i}.png").convert_alpha() for i in range(1,4)] 
swing_left = [pygame.transform.rotate(img, 180) for img in swing_right] 
swing_up = [pygame.transform.rotate(img, 90) for img in swing_right] 
swing_down = [pygame.transform.rotate(img, -90) for img in swing_right]
swing_up_left = [pygame.transform.rotate(img, 135) for img in swing_right] 
swing_up_right = [pygame.transform.rotate(img, 45) for img in swing_right] 
swing_down_left = [pygame.transform.rotate(img, 225) for img in swing_right] 
swing_down_right = [pygame.transform.rotate(img, -45) for img in swing_right] 

#Roll animation (4 frames)
roll_right = [pygame.image.load(f"assets/animations/kirby_roll_right{i}.png").convert_alpha() for i in range(1,5)]
roll_left = [pygame.transform.rotate(img, 180) for img in roll_right]
roll_up = [pygame.transform.rotate(img, 90) for img in roll_right]
roll_down = [pygame.transform.rotate(img, -90) for img in roll_right]
roll_up_left = [pygame.transform.rotate(img, 135) for img in roll_right] 
roll_up_right = [pygame.transform.rotate(img, 45) for img in roll_right] 
roll_down_left = [pygame.transform.rotate(img, 225) for img in roll_right] 
roll_down_right = [pygame.transform.rotate(img, -45) for img in roll_right] 

#Player setup
player_rect = walk_down[0].get_rect(topleft=(64,64))
player_speed = SPEED

# Player state variables
enemies = []
import random
import copy
 
# Inventory setup
inventory = []
MAX_STACK = 99
INVENTORY_COLS = 6
SLOT_SIZE = 48
SLOT_PADDING = 6
MAX_SLOTS = INVENTORY_COLS * 3

def get_inventory_layout():
    """Return a dict with scaled slot size and panel coordinates that fit in `WIDTH`/`HEIGHT`.
    Keys: slot, padding, cols, rows, panel_w, panel_h, left_x, left_y, right_x, right_y
    """
    cols = INVENTORY_COLS
    rows = 3
    padding = SLOT_PADDING
    # Make slots smaller
    base_slot = 32  # was SLOT_SIZE (48)
    # Move inventory panel more to the right
    max_slot_w = max((WIDTH - 220 - cols * padding) // cols, 16)
    max_slot_h = max((HEIGHT - 120 - rows * padding) // rows, 16)
    slot = min(base_slot, max_slot_w, max_slot_h)
    panel_w = cols * (slot + padding) + padding
    panel_h = rows * (slot + padding) + padding
    left_x = 30  # left margin, keeps panel on screen
    left_y = (HEIGHT - panel_h) // 2
    right_x = left_x + panel_w + 40
    right_y = left_y
    return {
        'slot': slot,
        'padding': padding,
        'cols': cols,
        'rows': rows,
        'panel_w': panel_w,
        'panel_h': panel_h,
        'left_x': left_x,
        'left_y': left_y,
        'right_x': right_x,
        'right_y': right_y,
    }

# Inventory/UI state
quest_journal_open = False
selected_quest_idx = None
quest_showing = False
inv_selected_idx = None
# Inventory action menu state
INVENTORY_MOUSE_ENABLED = False
inv_action_menu_open = False
inv_action_options = ['Discard', 'Cancel']
inv_action_selected_idx = 0
inv_pending_slot = None
inv_confirm_open = False
inv_confirm_selected_idx = 0

# Quest data structure
quests = [
    {
        'title': 'Explore',
        'summary': 'Travel to new areas, inspect interesting locations, and overcome small challenges to learn more about the world.',
        'objectives': [
            'Walk to a new area',
            'Find a chest',
            'Defeat an enemy'
        ]
    },
    {
        'title': 'test quest',
        'summary': 'This is a test quest used to verify the quest journal functionality.',
        'objectives': [
            'Open the quest journal',
            'Select this test quest',
            'Verify the summary appears'
        ]
    },
    # Add more quests here
]
inventory_open = False
dragging = None
drag_source = None

# load item images
item_images = {}
try:
    item_images['apple'] = pygame.image.load('assets/items/apple.png').convert_alpha()
except Exception:
    # fallback placeholder
    surf = pygame.Surface((32,32), pygame.SRCALPHA)
    surf.fill((255, 215, 0, 255))
    item_images['apple'] = surf

# --- NPCs ---
npc_images = {}
try:
    npc_base = pygame.image.load('assets/animations/npc1_right.png').convert_alpha()
except Exception:
    # fallback simple square
    npc_base = pygame.Surface((32,32), pygame.SRCALPHA)
    npc_base.fill((200,100,100,255))
npc_images['npc1'] = npc_base

# Build NPC animation frames (3-frame walk) by reusing npc_base variations
npc_dir_frames = []
npc_walk_frames = []
try:
    # load 3-frame npc walk animation facing right
    for i in range(1,4):
        img = pygame.image.load(f"assets/animations/npc1_right{i}.png").convert_alpha()
        npc_walk_frames.append(img)
except Exception:
    # fallback: repeat base
    npc_walk_frames = [npc_base, npc_base, npc_base]

# build 8-direction rotated frames (for each angle, store list of 3 frames)
angles = [0, -45, -90, -135, -180, -225, -270, -315]
for a in angles:
    frames = [pygame.transform.rotate(img, a) for img in npc_walk_frames]
    npc_dir_frames.append(frames)

# Add simple per-NPC state defaults when building

# NPCs per-area (list of dicts with rect, id, facing_index, dialog)
npcs_by_area = {}
def build_npcs_for_area(area_id):
    """Populate `npcs_by_area[area_id]` with NPCs for the given area."""
    npcs = []
    if area_id == 1:
        # two NPCs at the provided coordinates (world pixels); facing=2 -> down
        # spaced further apart so they don't overlap and are easier to interact with
        npcs.append({
            'id': 'npc1',
            'rect': pygame.Rect(300, 320, npc_base.get_width(), npc_base.get_height()),
            'facing': 2,
            'dialog': [
                "Are you an adventurer?",
                "If you are, you should head to the adventurer's guild.",
            ],
        })
        npcs.append({
            'id': 'npc1',
            'rect': pygame.Rect(364, 320, npc_base.get_width(), npc_base.get_height()),
            'facing': 2,
            'dialog': [
                "I'm gonna touch you.",
            ],
        })
    npcs_by_area[area_id] = npcs


# NPC behavior: walk a small rectangular loop (right->down->left->up) half-way then pause
def npc_update(npc, dt):
    # ensure state fields
    npc.setdefault('frame_idx', 0)
    npc.setdefault('anim_timer', 0)
    npc.setdefault('walk_timer', 0)
    npc.setdefault('pause_timer', 0)
    npc.setdefault('walk_step', 0)  # which leg of the loop
    npc.setdefault('walk_progress', 0.0)  # pixels moved along current leg
    # movement parameters
    WALK_DIST = TILE_SIZE * 2  # walk two tiles per leg
    WALK_SPEED = 24.0  # pixels per second
    PAUSE_MS = 10000

    # if paused
    if npc.get('pause_timer', 0) > 0:
        npc['pause_timer'] = max(0, npc['pause_timer'] - dt)
        npc['anim_timer'] = 0
        return

    # move along current leg
    dx = dy = 0
    step = npc['walk_step'] % 4
    remaining = WALK_DIST - npc['walk_progress']
    move_amt = WALK_SPEED * (dt / 1000.0)
    move_amt = min(move_amt, remaining)
    if step == 0:
        dx = move_amt
    elif step == 1:
        dy = move_amt
    elif step == 2:
        dx = -move_amt
    elif step == 3:
        dy = -move_amt

    # apply movement with simple collision against solid tiles
    rect = npc['rect']
    rect.x += int(round(dx))
    # check tile collision and revert if blocked
    # reuse solid tile detection from player code
    solid_tiles = []
    for r in range(len(tilemap)):
        for c in range(len(tilemap[r])):
            t = tilemap[r][c]
            if t in (1,2,4):
                solid_tiles.append(pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE))
    blocked = False
    for tile in solid_tiles:
        if rect.colliderect(tile):
            blocked = True
            break
    if blocked:
        rect.x -= int(round(dx))
        # treat as finishing leg
        npc['walk_progress'] = WALK_DIST
    else:
        npc['walk_progress'] += abs(dx)

    rect.y += int(round(dy))
    blocked = False
    for tile in solid_tiles:
        if rect.colliderect(tile):
            blocked = True
            break
    if blocked:
        rect.y -= int(round(dy))
        npc['walk_progress'] = WALK_DIST
    else:
        npc['walk_progress'] += abs(dy)

    # advance leg if completed half of loop (halfway = two legs)
    if npc['walk_progress'] >= WALK_DIST:
        npc['walk_progress'] = 0.0
        npc['walk_step'] = (npc['walk_step'] + 1) % 4
        # if we've completed two legs (halfway), pause
        if npc['walk_step'] % 4 == 2:
            npc['pause_timer'] = PAUSE_MS

    # animate frames
    npc['anim_timer'] += dt
    if npc['anim_timer'] >= 160:
        npc['anim_timer'] = 0
        npc['frame_idx'] = (npc.get('frame_idx', 0) + 1) % len(npc_walk_frames)

    # set facing based on last movement direction
    try:
        if dx != 0 or dy != 0:
            angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
            dir_idx = int((angle + 22.5) // 45) % 8
            npc['dir_idx'] = dir_idx
    except Exception:
        pass

# build for area 1 initially so list exists
build_npcs_for_area(1)

def add_item(item_id, count):
    global inventory
    remaining = count
    # try to add into existing stacks first
    for it in inventory:
        if it['id'] == item_id and it.get('count', 0) < MAX_STACK:
            space = MAX_STACK - it['count']
            to_add = min(space, remaining)
            it['count'] += to_add
            remaining -= to_add
            if remaining <= 0:
                return
    # if there's still remaining, add new stacks if there's room
    while remaining > 0 and len(inventory) < MAX_SLOTS:
        to_put = min(MAX_STACK, remaining)
        inventory.append({'id': item_id, 'count': to_put})
        remaining -= to_put

# load base enemy frames
try:
    base_enemy_frames = [pygame.image.load(f"assets/animations/enemy1_right{i}.png").convert_alpha() for i in range(1,4)]
except Exception:
    base_enemy_frames = [pygame.Surface((32,32)) for _ in range(3)]

# Animation / timing constants
animation_speed = 0.15
frame_time_ms = 90
roll_time_ms = 400
roll_cooldown_ms = 1000
roll_speed = ROLL_SPEED

# Player animation state
direction = "down"
current_frame = 0.0
player_img = walk_down[0]
attacking = False
rolling = False
roll_cooldown = 0
roll_timer = 0
attack_timer = 0
sword_hitbox = None
current_frame = 0.0
player_img = walk_down[0]
attacking = False
rolling = False
roll_cooldown = 0
roll_timer = 0
attack_timer = 0

# Build enemy directional frames (8 directions) and masks
enemy_dir_frames = []
enemy_dir_masks = []
angles = [0, -45, -90, -135, -180, -225, -270, -315]
for a in angles:
    frames = [pygame.transform.rotate(img, a) for img in base_enemy_frames]
    enemy_dir_frames.append(frames)
    enemy_dir_masks.append([pygame.mask.from_surface(f) for f in frames])

# --- Area / Chests ---
# keep original map as area 0 and build a simple area 1
tilemap_area0 = copy.deepcopy(tilemap)
rows = len(tilemap_area0)
cols = max(len(r) for r in tilemap_area0)
# manually define tilemap_area1 for more interesting layout
manual_tilemap_area1 = [
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
    ]

# Build tilemap_area1 from manual input if provided, otherwise use a simple builder
if manual_tilemap_area1 is not None:
    tilemap_area1 = manual_tilemap_area1
else:
    # default builder: mostly grass with a left-side pathway to return
    tilemap_area1 = [[0 for _ in range(cols)] for _ in range(rows)]
    for rr in range(6, min(16, rows)):
        for cc in range(0, min(3, cols)):
            tilemap_area1[rr][cc] = 5
    if rows > 10 and cols > 6:
        tilemap_area1[10][4] = 4

# If tavern image was loaded, stamp its tiles into the area1 tilemap as solid tiles
# so the tavern behaves like part of the map (for collision). Visuals are still
# drawn from `tavern_subs` during rendering.
try:
    if tavern_origin and tavern_subs:
        ox, oy = tavern_origin
        # ensure tilemap_area1 is large enough
        for (bx, by), sub in list(tavern_subs.items()):
            tx = ox + bx
            ty = oy + by
            if 0 <= ty < len(tilemap_area1) and 0 <= tx < len(tilemap_area1[ty]):
                # Inspect the original tavern image tile to see if it contains any opaque pixels
                try:
                    rect = pygame.Rect(bx * TILE_SIZE, by * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    orig_tile = tavern_img.subsurface(rect).copy()
                    mask = pygame.mask.from_surface(orig_tile)
                    if mask.count() > 0:
                        # tile has opaque pixels -> treat as solid (rock)
                        tilemap_area1[ty][tx] = 1
                    else:
                        # tile is fully transparent -> leave underlying tile as-is (walkable)
                        pass
                except Exception:
                    # fallback: keep existing behavior and mark solid
                    tilemap_area1[ty][tx] = 1
except Exception:
    pass

# current active area and tilemap reference
current_area = 0
tilemap = tilemap_area0

# chests list will be rebuilt per-area
chests = []
active_chest = None

# store enemies per-area so they respawn when revisiting
area_enemies = {}
# track whether we've spawned initial enemies for an area (so they don't respawn while still in it)
area_spawned = set()

def build_chests():
    global chests
    chests = []
    for r in range(len(tilemap)):
        for c in range(len(tilemap[r])):
            if tilemap[r][c] == 4:
                chests.append({
                    'rect': pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                    'items': [{'id': 'apple', 'count': 1}],
                    'opened': False,
                })

# initial build for area 0
build_chests()
# Drag/drop state for inventory
dragging = None  # {'id':..., 'count':int}
drag_source = None  # ('inventory', idx) or ('chest', idx)

# --- Health ---
max_health = 100
health = max_health

# --- Enemies and damage ---
enemies = []
# Spawner configuration
ENEMY_SPAWN_INTERVAL_MS = 5000
enemy_spawn_timer = ENEMY_SPAWN_INTERVAL_MS
ENEMY_MAX = 10

import random

def find_spawn_position(avoid_rect=None, min_distance=200):
    # Enemy spawn is now static only; no random spawn positions.
    return None

# (spawn zones removed — enemies are now placed statically on pathway tiles)

# --- Pathfinding helpers (A* on tile grid, 4-way) ---
def tile_is_solid(r, c):
    # ensure row index valid
    if r < 0 or r >= len(tilemap):
        return True
    # ensure column index valid for this specific row
    if c < 0 or c >= len(tilemap[r]):
        return True
    return tilemap[r][c] in (1,2,4)

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def compute_path(start_px, goal_px):
    # convert to tile coords
    sx = start_px[0] // TILE_SIZE
    sy = start_px[1] // TILE_SIZE
    gx = goal_px[0] // TILE_SIZE
    gy = goal_px[1] // TILE_SIZE
    start = (sy, sx)
    goal = (gy, gx)
    open_set = {start}
    came_from = {}
    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    import heapq
    heap = [(fscore[start], start)]
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    while heap:
        _, current = heapq.heappop(heap)
        if current == goal:
            # reconstruct path
            path = []
            cur = current
            while cur in came_from:
                path.append((cur[1]*TILE_SIZE + TILE_SIZE//2, cur[0]*TILE_SIZE + TILE_SIZE//2))
                cur = came_from[cur]
            path.reverse()
            return path
        for d in dirs:
            nr = current[0] + d[0]
            nc = current[1] + d[1]
            neighbor = (nr, nc)
            if tile_is_solid(nr, nc):
                continue
            tentative_g = gscore.get(current, 999999) + 1
            if tentative_g < gscore.get(neighbor, 999999):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g
                fscore[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(heap, (fscore[neighbor], neighbor))
    return None

def rect_overlaps_lava(r):
    left = r.left // TILE_SIZE
    right = (r.right - 1) // TILE_SIZE
    top = r.top // TILE_SIZE
    bottom = (r.bottom - 1) // TILE_SIZE
    for rr in range(top, bottom+1):
        if rr < 0 or rr >= len(tilemap):
            continue
        for cc in range(left, right+1):
            if cc < 0 or cc >= len(tilemap[rr]):
                continue
            if tilemap[rr][cc] == 3:
                return True
    return False


# Unified enemy AI: all enemies call this each frame to update position, timers, and animation
def enemy_ai_update(e, dt):
    # ensure required fields exist with sensible defaults
    er = e.get('rect')
    if er is None:
        return
    e.setdefault('fx', float(er.x))
    e.setdefault('fy', float(er.y))
    e.setdefault('speed', 48.0)
    e.setdefault('frame_idx', 0)
    e.setdefault('anim_timer', 0)
    e.setdefault('hurt_timer', 0)
    e.setdefault('lava_timer', 0)
    e.setdefault('health', 100)

    # vector from enemy to player
    dx_e = player_rect.centerx - er.centerx
    dy_e = player_rect.centery - er.centery
    dist = math.hypot(dx_e, dy_e)

    # choose facing/frame based on angle to player
    angle = (math.degrees(math.atan2(dy_e, dx_e)) + 360) % 360
    dir_idx = int((angle + 22.5) // 45) % 8
    # set frame for rendering (render code expects dir_idx and frame_idx)
    e['dir_idx'] = dir_idx

    # only move when player is within chase range
    if dist <= ENEMY_CHASE_RANGE and dist > 0:
        nx = dx_e / dist
        ny = dy_e / dist
        spd = e.get('speed', 48.0)
        move_x = nx * spd * (dt / 1000.0)
        move_y = ny * spd * (dt / 1000.0)
        try:
            if rect_overlaps_lava(er):
                move_x *= 0.5
                move_y *= 0.5
        except Exception:
            pass

        # collision tests per-axis against solid tiles
        fx = e['fx']
        fy = e['fy']
        new_fx = fx + move_x
        new_fy = fy + move_y

        test_x_rect = er.copy()
        test_x_rect.x = int(new_fx)
        test_y_rect = er.copy()
        test_y_rect.y = int(new_fy)

        def rect_on_solid(r):
            left = r.left // TILE_SIZE
            right = (r.right - 1) // TILE_SIZE
            top = r.top // TILE_SIZE
            bottom = (r.bottom - 1) // TILE_SIZE
            for rr in range(top, bottom+1):
                if rr < 0 or rr >= len(tilemap):
                    return True
                for cc in range(left, right+1):
                    if cc < 0 or cc >= len(tilemap[rr]):
                        return True
                    if tilemap[rr][cc] in (1,2,4):
                        return True
            return False

        if not rect_on_solid(test_x_rect):
            fx = new_fx
        if not rect_on_solid(test_y_rect):
            fy = new_fy

        e['fx'] = fx
        e['fy'] = fy
        er.x = int(round(fx))
        er.y = int(round(fy))

        # avoid overlapping player by nudging away
        try:
            if player_hitbox.colliderect(er):
                dx_push = er.centerx - player_rect.centerx
                dy_push = er.centery - player_rect.centery
                d = math.hypot(dx_push, dy_push) or 1
                nxp = dx_push / d
                nyp = dy_push / d
                er.x += int(nxp * 2)
                er.y += int(nyp * 2)
                e['fx'] = float(er.x)
                e['fy'] = float(er.y)
        except Exception:
            pass

        # simple separation from other enemies
        for other in enemies:
            if other is e:
                continue
            orect = other.get('rect')
            if orect is None:
                continue
            if er.colliderect(orect):
                dx_push = er.centerx - orect.centerx
                dy_push = er.centery - orect.centery
                d = math.hypot(dx_push, dy_push) or 1
                nxp = dx_push / d
                nyp = dy_push / d
                er.x += int(nxp * 2)
                er.y += int(nyp * 2)
                other['rect'].x -= int(nxp * 1)
                other['rect'].y -= int(nyp * 1)
                e['fx'] = float(er.x)
                e['fy'] = float(er.y)

    # update timers and animation
    e['anim_timer'] = e.get('anim_timer', 0) + dt
    if e.get('hurt_timer', 0) > 0:
        e['hurt_timer'] = max(0, e['hurt_timer'] - dt)
    if e['anim_timer'] >= ENEMY_FRAME_MS:
        e['anim_timer'] = 0
        e['frame_idx'] = (e.get('frame_idx', 0) + 1) % len(base_enemy_frames)

# Player currency
gold = 100

import json, os

SAVE_FILE = os.path.join(os.path.dirname(__file__), 'save.sav')

def save_game():
    try:
        data = {
            'gold': gold,
            'inventory': inventory,
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass

def load_game():
    global gold, inventory
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                gold = data.get('gold', gold)
                inventory = data.get('inventory', inventory)
    except Exception:
        pass

# attempt to load saved data at startup
load_game()
# chase range: 10 tiles
ENEMY_CHASE_RANGE = 10 * TILE_SIZE
ENEMY_FRAME_MS = 160
ENEMY_KNOCKBACK = 18
INVULN_MS = 1000
invuln_timer = 0
HEAL_MS = 1000
heal_timer = HEAL_MS
# user message display (ms)
MSG_MS = 2000
msg_text = ""
msg_timer = 0
# floating messages (list of dict {text, timer, x, y}) to avoid global overwrite/flicker
floating_messages = []
# dialog box state (for NPC conversations)
dialog_open = False
dialog_lines = []
dialog_index = 0
# Dialog helpers
def dialog_len():
    try:
        return len(dialog_lines) if isinstance(dialog_lines, (list, tuple)) else 0
    except Exception:
        return 0

def dialog_current_line():
    try:
        if dialog_index < dialog_len():
            return dialog_lines[dialog_index]
    except Exception:
        pass
    return ''
# Game over state
game_over = False

# --- Camera / viewport ---
# show this many tiles across and down
CAM_TILES = 20
CAM_W = CAM_TILES * TILE_SIZE
CAM_H = CAM_TILES * TILE_SIZE
# camera center in world coordinates (pixels)
cam_x = player_rect.centerx
cam_y = player_rect.centery
camera_follow = True
CAM_PAN_SPEED = 300  # pixels per second when using arrow keys to pan
camera_surf = pygame.Surface((CAM_W, CAM_H))
# clamp initial camera within world
max_w = len(tilemap[0]) * TILE_SIZE
max_h = len(tilemap) * TILE_SIZE
half_w = CAM_W // 2
half_h = CAM_H // 2
cam_x = max(half_w, min(max_w - half_w, cam_x))
cam_y = max(half_h, min(max_h - half_h, cam_y))

def reset_game():
    global health, invuln_timer, player_rect, game_over
    health = max_health
    invuln_timer = 0
    player_rect.topleft = (64, 64)
    game_over = False

def switch_area(area_id, spawn_pos=None):
    """Switch current map area to `area_id` and reposition player.
    `spawn_pos` if provided should be (x,y) world pixel coords for the player to appear at.
    This clears enemies and rebuilds chests for the new tilemap."""
    global tilemap, current_area, enemies, cam_x, cam_y, chests
    if area_id == current_area:
        return
    if area_id == 0:
        tilemap = tilemap_area0
    elif area_id == 1:
        tilemap = tilemap_area1
    else:
        return
    # ensure NPC list exists for this area (populate if not present)
    try:
        if area_id not in npcs_by_area:
            build_npcs_for_area(area_id)
    except Exception:
        pass
    current_area = area_id
    # Clear area_spawned so enemies respawn when re-entering any area
    area_spawned.clear()
    # save current area's enemies and clear (only if there are enemies)
    try:
        if enemies:
            area_enemies[current_area] = [
                {k: (v.copy() if isinstance(v, dict) else v) for k, v in en.items()} if isinstance(en, dict) else en
                for en in enemies
            ]
        else:
            # remove any saved key so re-entry will spawn fresh enemies
            if current_area in area_enemies:
                del area_enemies[current_area]
    except Exception:
        if enemies:
            area_enemies[current_area] = list(enemies)
        else:
            if current_area in area_enemies:
                del area_enemies[current_area]
    enemies.clear()
    # rebuild chests for the new map
    build_chests()
    # reposition player
    if spawn_pos:
        player_rect.topleft = spawn_pos
    else:
        # sensible defaults: area0 left-top, area1 near left pathway
        if current_area == 0:
            player_rect.topleft = (64, 64)
        else:
            player_rect.topleft = (TILE_SIZE * 2, TILE_SIZE * 8)
    # resync camera to player and clamp
    cam_x = player_rect.centerx
    cam_y = player_rect.centery
    max_w = len(tilemap[0]) * TILE_SIZE
    max_h = len(tilemap) * TILE_SIZE
    half_w = CAM_W // 2
    half_h = CAM_H // 2
    cam_x = max(half_w, min(max_w - half_w, cam_x))
    cam_y = max(half_h, min(max_h - half_h, cam_y))
    # restore saved enemies for the new area if present, but skip for area 1
    if current_area == 1:
        enemies.clear()
        area_enemies[current_area] = []
    else:
        saved = area_enemies.get(current_area)
        if saved:
            enemies.clear()
            for s in saved:
                er = s.get('rect') if isinstance(s, dict) else None
                if isinstance(er, pygame.Rect):
                    rect = er.copy()
                elif isinstance(er, (list, tuple)) and len(er) >= 4:
                    rect = pygame.Rect(er[0], er[1], er[2], er[3])
                else:
                    rect = base_enemy_frames[0].get_rect(topleft=(player_rect.x + TILE_SIZE*2, player_rect.y))
                new_e = {
                    'rect': rect,
                    'fx': float(rect.x),
                    'fy': float(rect.y),
                    'frame_idx': s.get('frame_idx', 0),
                    'anim_timer': s.get('anim_timer', 0),
                    'speed': s.get('speed', 48.0),
                    'health': s.get('health', 100),
                    'hurt_timer': s.get('hurt_timer', 0),
                    'lava_timer': s.get('lava_timer', 0),
                }
                enemies.append(new_e)
            area_spawned.add(current_area)

#Main game loop
print("DEBUG: about to enter main loop")
sys.stdout.flush()
while True:
    dt = clock.tick(60)
    # debug: indicate main loop tick
    print("DEBUG: loop tick", dt)
    sys.stdout.flush()
    print("DEBUG: before spawn check")
    sys.stdout.flush()

    # --- Static enemy placement: only run for area 0 and only once per visit ---
    # Do not spawn or update enemies while dialog with an NPC is open
    if dialog_open:
        print("DEBUG: dialog open — skipping spawn/update")
    else:
        if current_area == 0 and (current_area not in area_spawned) and not enemies and not area_enemies.get(current_area):
            # Place 2 enemies at the middle of the pathway in area 0
            mid_row = len(tilemap) // 2
            mid_col = len(tilemap[0]) // 2
            # Find two pathway tiles near the center
            positions = []
            for offset in [-1, 1]:
                for r in range(mid_row-2, mid_row+3):
                    for c in range(mid_col-2, mid_col+3):
                        if tilemap[r][c] == 5:
                            positions.append((c * TILE_SIZE, r * TILE_SIZE))
                            if len(positions) >= 2:
                                break
                    if len(positions) >= 2:
                        break
                if len(positions) >= 2:
                    break
            # If not enough found, fallback to exact center
            while len(positions) < 2:
                positions.append((mid_col * TILE_SIZE, mid_row * TILE_SIZE))
            for sx, sy in positions[:2]:
                rect = base_enemy_frames[0].get_rect(topleft=(sx, sy))
                enemies.append({
                    'rect': rect,
                    'fx': float(rect.x),
                    'fy': float(rect.y),
                    'frame_idx': 0,
                    'anim_timer': 0,
                    'speed': 48.0,
                    'health': 100,
                    'hurt_timer': 0,
                    'lava_timer': 0,
                })
            area_spawned.add(current_area)

    print("DEBUG: after spawn, before events")
    sys.stdout.flush()
    #Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Mouse interactions (disabled for inventory when INVENTORY_MOUSE_ENABLED=False)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if inventory_open and not INVENTORY_MOUSE_ENABLED and dragging is None:
                # ignore mouse clicks for inventory
                pass
            elif inventory_open and INVENTORY_MOUSE_ENABLED and dragging is None:
                mx, my = event.pos
                # compute left panel area using layout helper
                layout = get_inventory_layout()
                left_x = layout['left_x']
                left_y = layout['left_y']
                slot = layout['slot']
                padding = layout['padding']
                cols = layout['cols']
                rows = layout['rows']
                # check which slot clicked
                for idx in range(min(len(inventory), cols * rows)):
                    col = idx % cols
                    row = idx // cols
                    slot_x = left_x + padding + col * (slot + padding)
                    slot_y = left_y + padding + row * (slot + padding)
                    slot_rect = pygame.Rect(slot_x, slot_y, slot, slot)
                    if slot_rect.collidepoint(mx, my):
                        # right-click (button 3) => split stack into two if possible
                        if event.button == 3:
                            # only split if this slot has more than 1 item and there's room for a new stack
                            if inventory[idx]['count'] > 1 and len(inventory) < MAX_SLOTS:
                                half = inventory[idx]['count'] // 2
                                if half > 0:
                                    inventory[idx]['count'] -= half
                                    # insert new stack immediately after this slot
                                    inventory.insert(idx+1, {'id': inventory[idx]['id'], 'count': half})
                            break
                        # left-click (button 1) => start dragging one item from this slot
                        else:
                            dragging = {'id': inventory[idx]['id'], 'count': 1}
                            drag_source = ('inventory', idx)
                            inventory[idx]['count'] -= 1
                            if inventory[idx]['count'] <= 0:
                                del inventory[idx]
                            break
        if event.type == pygame.MOUSEBUTTONUP:
            if inventory_open and INVENTORY_MOUSE_ENABLED and dragging is not None:
                mx, my = event.pos
                # compute left panel area to detect if dropping back into inventory
                layout = get_inventory_layout()
                left_x = layout['left_x']
                left_y = layout['left_y']
                left_w = layout['panel_w']
                left_h = layout['panel_h']
                inv_area = pygame.Rect(left_x, left_y, left_w, left_h)
                if inv_area.collidepoint(mx, my):
                    # dropped back into inventory => add item back
                    add_item(dragging['id'], dragging['count'])
                else:
                    # dropped outside => discard (do nothing)
                    pass
                dragging = None
                drag_source = None
        if event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_r:
                    reset_game()
                continue

            # If a dialog box is open, let space advance/close it and ignore other keys
            if dialog_open:
                if event.key == pygame.K_SPACE:
                    # advance safely
                    if dialog_index + 1 >= dialog_len():
                        dialog_open = False
                        dialog_lines = []
                        dialog_index = 0
                    else:
                        dialog_index += 1
                # swallow other keys while dialog open
                continue

            if event.key == pygame.K_q:
                quest_journal_open = not quest_journal_open
                if quest_journal_open:
                    selected_quest_idx = 0
                    quest_showing = False
                else:
                    selected_quest_idx = None
                    quest_showing = False

            if event.key == pygame.K_h and not attacking and not rolling:
                attacking = True
                attack_timer = 0
            # Inventory / Quest navigation with WASD and Enter
            # If action menu is open, handle menu input first
            if inv_action_menu_open:
                if event.key == pygame.K_w or event.key == pygame.K_a:
                    inv_action_selected_idx = max(0, inv_action_selected_idx - 1)
                if event.key == pygame.K_s or event.key == pygame.K_d:
                    inv_action_selected_idx = min(len(inv_action_options)-1, inv_action_selected_idx + 1)
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    choice = inv_action_options[inv_action_selected_idx]
                    inv_action_menu_open = False
                    if choice == 'Discard':
                        inv_confirm_open = True
                        inv_confirm_selected_idx = 1  # default to 'No'
                    elif choice == 'Eat':
                        # Eat one item from the pending slot (applies to apples)
                        if inv_pending_slot is not None and inv_pending_slot < len(inventory):
                            item = inventory[inv_pending_slot]
                            # heal player by 20, clamp to max_health
                            health = min(max_health, health + 20)
                            # consume one item
                            item['count'] -= 1
                            if item['count'] <= 0:
                                del inventory[inv_pending_slot]
                                inv_selected_idx = min(inv_pending_slot, len(inventory)-1) if inventory else None
                        inv_pending_slot = None
                    else:
                        inv_pending_slot = None
                if event.key == pygame.K_ESCAPE:
                    inv_action_menu_open = False
                    inv_pending_slot = None
            elif inv_confirm_open:
                if event.key == pygame.K_a or event.key == pygame.K_w:
                    inv_confirm_selected_idx = max(0, inv_confirm_selected_idx - 1)
                if event.key == pygame.K_d or event.key == pygame.K_s:
                    inv_confirm_selected_idx = min(1, inv_confirm_selected_idx + 1)
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # 0 = Yes, 1 = No
                    if inv_confirm_selected_idx == 0 and inv_pending_slot is not None and inv_pending_slot < len(inventory):
                        # discard one item from the pending slot
                        inventory[inv_pending_slot]['count'] -= 1
                        if inventory[inv_pending_slot]['count'] <= 0:
                            del inventory[inv_pending_slot]
                            inv_selected_idx = min(inv_pending_slot, len(inventory)-1) if inventory else None
                    inv_confirm_open = False
                    inv_pending_slot = None
                if event.key == pygame.K_ESCAPE:
                    inv_confirm_open = False
                    inv_pending_slot = None
            elif inventory_open:
                # compute layout
                layout = get_inventory_layout()
                cols = layout['cols']
                rows = layout['rows']
                max_idx = cols * rows - 1
                if event.key == pygame.K_w:
                    if inv_selected_idx is None:
                        inv_selected_idx = 0
                    else:
                        inv_selected_idx = max(0, inv_selected_idx - cols)
                if event.key == pygame.K_s:
                    if inv_selected_idx is None:
                        inv_selected_idx = 0
                    else:
                        inv_selected_idx = min(max_idx, inv_selected_idx + cols)
                if event.key == pygame.K_a:
                    if inv_selected_idx is None:
                        inv_selected_idx = 0
                    else:
                        inv_selected_idx = max(0, inv_selected_idx - 1)
                if event.key == pygame.K_d:
                    if inv_selected_idx is None:
                        inv_selected_idx = 0
                    else:
                        inv_selected_idx = min(max_idx, inv_selected_idx + 1)
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # open action menu for the selected inventory slot
                    if inv_selected_idx is not None and inv_selected_idx < len(inventory):
                        inv_pending_slot = inv_selected_idx
                        item = inventory[inv_pending_slot]
                        if item.get('id') == 'apple':
                            inv_action_options = ['Eat', 'Discard', 'Cancel']
                        else:
                            inv_action_options = ['Discard', 'Cancel']
                        inv_action_menu_open = True
                        inv_action_selected_idx = 0

            if quest_journal_open and not inventory_open:
                # vertical navigation through quests
                if event.key == pygame.K_w or event.key == pygame.K_a:
                    if selected_quest_idx is None:
                        selected_quest_idx = 0
                    else:
                        selected_quest_idx = max(0, selected_quest_idx - 1)
                    quest_showing = False
                if event.key == pygame.K_s or event.key == pygame.K_d:
                    if selected_quest_idx is None:
                        selected_quest_idx = 0
                    else:
                        selected_quest_idx = min(len(quests) - 1, selected_quest_idx + 1)
                    quest_showing = False
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected_quest_idx is not None:
                        quest_showing = True
            
            if event.key == pygame.K_SPACE:
                # if near a chest, open it instead of rolling
                opened = False
                for ch in chests:
                    dist = math.hypot(player_rect.centerx - ch['rect'].centerx, player_rect.centery - ch['rect'].centery)
                    if dist <= TILE_SIZE * 2:
                        active_chest = ch
                        inventory_open = True
                        ch['opened'] = True
                        opened = True
                        # cancel actions
                        attacking = False
                        rolling = False
                        direction = False
                        break
                # if not opened a chest, check for NPC interaction
                if not opened:
                    area_npcs = npcs_by_area.get(current_area, [])
                    for npc in area_npcs:
                        dist = math.hypot(player_rect.centerx - npc['rect'].centerx, player_rect.centery - npc['rect'].centery)
                        if dist <= TILE_SIZE * 2:
                            # open npc dialog box (dialog can be a list of lines)
                            try:
                                dlg = npc.get('dialog', [])
                                if isinstance(dlg, str):
                                    dlg = [dlg]
                                dialog_lines = list(dlg)
                                dialog_index = 0
                                # only open dialog if there is at least one line
                                if dialog_lines:
                                    dialog_open = True
                                else:
                                    dialog_open = False
                            except Exception:
                                dialog_lines = []
                                dialog_index = 0
                                dialog_open = False
                            opened = True
                            break
                if not opened and not rolling and roll_cooldown <= 0:
                    rolling = True
                    roll_timer = 0
                    roll_cooldown = roll_cooldown_ms
            if event.key == pygame.K_l:
                # toggle inventory
                inventory_open = not inventory_open
                # when opening inventory, cancel actions
                if inventory_open:
                    attacking = False
                    rolling = False
                    direction = False
                    inv_selected_idx = 0
                else:
                    # if toggling inventory closed, clear active chest
                    active_chest = None
            # Save / Load keys
            if event.key == pygame.K_F5:
                try:
                    save_game()
                    msg_text = "Game saved."
                    msg_timer = MSG_MS
                except Exception:
                    pass
            if event.key == pygame.K_F9:
                try:
                    load_game()
                    msg_text = "Game loaded."
                    msg_timer = MSG_MS
                except Exception:
                    pass
            if event.key == pygame.K_y:
                # resync camera to follow player
                camera_follow = True
                cam_x = player_rect.centerx
                cam_y = player_rect.centery
            if event.key == pygame.K_F11:
                # toggle fullscreen
                try:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
                        WIDTH, HEIGHT = screen.get_size()
                    else:
                        screen = pygame.display.set_mode((640, 640))
                        WIDTH, HEIGHT = 640, 640
                except Exception:
                    pass


    print("DEBUG: after event loop, before inventory check")
    sys.stdout.flush()
    # Helper: wrap text to fit a pixel width using given font
    def wrap_text(font_obj, text, max_width):
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip() if cur else w
            if font_obj.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # If quest journal is open, pause game updates and render journal
    if quest_journal_open:
        screen.fill((20, 20, 40))
        panel_w, panel_h = 360, 340
        panel_x = (WIDTH - panel_w) // 2
        panel_y = (HEIGHT - panel_h) // 2
        pygame.draw.rect(screen, (30, 30, 60), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (200, 200, 255), (panel_x, panel_y, panel_w, panel_h), 2)
        font = pygame.font.SysFont(None, 28)
        title_font = pygame.font.SysFont(None, 32, bold=True)
        # Draw quest titles (or focused quest)
        if not quest_showing:
            for idx, quest in enumerate(quests):
                qy = panel_y + 16 + idx * 36
                color = (255,255,0) if selected_quest_idx == idx else (255,255,255)
                txt = title_font.render(quest['title'], True, color)
                screen.blit(txt, (panel_x + 16, qy))
            # Draw quest details if selected (small preview)
            if selected_quest_idx is not None:
                quest = quests[selected_quest_idx]
                sy = panel_y + 16 + len(quests) * 36 + 12
                # wrap preview to two lines max and truncate with ellipsis if needed
                preview_max_w = panel_w - 32
                preview_lines = wrap_text(font, quest['summary'], preview_max_w)
                if len(preview_lines) > 2:
                    # truncate to two lines with ellipsis
                    first = preview_lines[0]
                    second = preview_lines[1]
                    # ensure second fits with ellipsis
                    el = '...'
                    while font.size(second + el)[0] > preview_max_w and len(second) > 0:
                        second = second[:-1]
                    preview_lines = [first, second + el]
                for pl in preview_lines:
                    screen.blit(font.render(pl, True, (200,200,200)), (panel_x + 16, sy))
                    sy += 28
                obj_font = pygame.font.SysFont(None, 24)
                for obj in quest['objectives']:
                    obj_txt = obj_font.render(f"- {obj}", True, (180,255,180))
                    screen.blit(obj_txt, (panel_x + 32, sy))
                    sy += 28
        else:
            # Focused quest view: larger box with title + full summary
            quest = quests[selected_quest_idx] if selected_quest_idx is not None else quests[0]
            big_w, big_h = panel_w - 40, panel_h - 40
            big_x = panel_x + 20
            big_y = panel_y + 20
            pygame.draw.rect(screen, (20,20,40), (big_x, big_y, big_w, big_h))
            pygame.draw.rect(screen, (200,200,255), (big_x, big_y, big_w, big_h), 2)
            title_surf = pygame.font.SysFont(None, 30, bold=True).render(quest['title'], True, (255,255,200))
            screen.blit(title_surf, (big_x + 12, big_y + 12))
            # wrap summary text to fit the focused box
            small_font = pygame.font.SysFont(None, 22)
            max_text_w = big_w - 24
            summary_lines = wrap_text(small_font, quest['summary'], max_text_w)
            sy = big_y + 48
            for l in summary_lines:
                screen.blit(small_font.render(l, True, (200,200,200)), (big_x + 12, sy))
                sy += 26
            sy += 6
            obj_font = pygame.font.SysFont(None, 20)
            for obj in quest['objectives']:
                screen.blit(obj_font.render(f"- {obj}", True, (180,255,180)), (big_x + 16, sy))
                sy += 22
        pygame.display.flip()
        # Handle quest journal events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    quest_journal_open = False
                    selected_quest_idx = None
                    quest_showing = False
                elif event.key == pygame.K_ESCAPE:
                    # close focused view first, then journal
                    if quest_showing:
                        quest_showing = False
                        selected_quest_idx = None
                    else:
                        quest_journal_open = False
                        selected_quest_idx = None
                        quest_showing = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if not quest_showing:
                    for idx, quest in enumerate(quests):
                        qy = panel_y + 16 + idx * 36
                        if panel_x + 16 <= mx <= panel_x + panel_w - 16 and qy <= my <= qy + 32:
                            selected_quest_idx = idx
                            quest_showing = True
                            break
                else:
                    # if focused, clicking outside the big box closes it
                    big_x = panel_x + 20
                    big_y = panel_y + 20
                    big_w = panel_w - 40
                    big_h = panel_h - 40
                    if not (big_x <= mx <= big_x + big_w and big_y <= my <= big_y + big_h):
                        quest_showing = False
                        selected_quest_idx = None
        continue
        # Open/close quest journal with 'q'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            quest_journal_open = not quest_journal_open
            selected_quest_idx = None
    # If inventory is open, pause game updates and render a frozen frame
    if inventory_open:
        # build camera view centered on current camera coords
        camera_surf.fill((0,0,0))
        cam_left = int(cam_x - CAM_W // 2)
        cam_top = int(cam_y - CAM_H // 2)
        # draw map into camera surface
        for row in range(len(tilemap)):
            for col in range(len(tilemap[row])):
                tile_type = tilemap[row][col]
                px = col * TILE_SIZE - cam_left
                py = row * TILE_SIZE - cam_top
                # only blit visible tiles
                if px + TILE_SIZE < 0 or py + TILE_SIZE < 0 or px > CAM_W or py > CAM_H:
                    continue
                # If we're in area 1 and a tavern is defined, blit tavern subsurface where it belongs
                if current_area == 1 and tavern_origin and tavern_subs:
                    ox, oy = tavern_origin
                    bx = col - ox
                    by = row - oy
                    key = (bx, by)
                    subimg = tavern_subs.get(key)
                    if subimg:
                        camera_surf.blit(subimg, (px, py))
                        continue
                camera_surf.blit(tiles[tile_type], (px, py))

        # draw enemies (frozen) into camera surface
        for e in enemies:
            er = e['rect']
            dx_e = player_rect.centerx - er.centerx
            dy_e = player_rect.centery - er.centery
            angle = (math.degrees(math.atan2(dy_e, dx_e)) + 360) % 360
            dir_idx = int((angle + 22.5) // 45) % 8
            frame = enemy_dir_frames[dir_idx][e['frame_idx']]
            ex = er.left - cam_left
            ey = er.top - cam_top
            if ex + er.width < 0 or ey + er.height < 0 or ex > CAM_W or ey > CAM_H:
                continue
            camera_surf.blit(frame, (ex, ey))
            # draw enemy health bar
            eh = e.get('health', 100)
            eh_max = 100
            hb_w, hb_h = er.width, 6
            hb_x = ex
            hb_y = ey - 10
            pygame.draw.rect(camera_surf, (60,60,60), (hb_x, hb_y, hb_w, hb_h))
            fill = int((eh / eh_max) * hb_w)
            pygame.draw.rect(camera_surf, (180,40,40), (hb_x, hb_y, fill, hb_h))
            pygame.draw.rect(camera_surf, (200,200,200), (hb_x, hb_y, hb_w, hb_h), 1)
        # update and draw NPCs for current area into camera surface
        area_npcs = npcs_by_area.get(current_area, [])
        for npc in area_npcs:
            try:
                npc_update(npc, dt)
            except Exception:
                pass
            nr = npc['rect']
            # choose dir index from npc state (default 0)
            dir_idx = npc.get('dir_idx', npc.get('facing', 0)) % len(npc_dir_frames)
            fi = npc.get('frame_idx', 0) % len(npc_dir_frames[0])
            surf = npc_dir_frames[dir_idx][fi]
            # rotate based on facing if desired (kept simple here)
            nx = nr.left - cam_left
            ny = nr.top - cam_top
            # skip if offscreen
            if nx + nr.width < 0 or ny + nr.height < 0 or nx > CAM_W or ny > CAM_H:
                continue
            camera_surf.blit(surf, (nx, ny))

        # blit player (frozen) into camera surface
        px = player_rect.left - cam_left
        py = player_rect.top - cam_top
        camera_surf.blit(player_img, (px, py))
        # now draw camera surface centered on the main screen
        sx = (WIDTH - CAM_W) // 2
        sy = (HEIGHT - CAM_H) // 2
        screen.fill((0,0,0))
        screen.blit(camera_surf, (sx, sy))

        # draw inventory UI: player's inventory on the left; chest (if active) on the right
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # left panel: player inventory (scaled to fit)
        layout = get_inventory_layout()
        left_x = layout['left_x']
        left_y = layout['left_y']
        left_w = layout['panel_w']
        left_h = layout['panel_h']
        slot = layout['slot']
        padding = layout['padding']
        cols = layout['cols']
        rows = layout['rows']
        pygame.draw.rect(screen, (40, 40, 40), (left_x, left_y, left_w, left_h))
        pygame.draw.rect(screen, (200, 200, 200), (left_x, left_y, left_w, left_h), 2)
        for idx in range(cols * rows):
            col = idx % cols
            row = idx // cols
            slot_x = left_x + padding + col * (slot + padding)
            slot_y = left_y + padding + row * (slot + padding)
            pygame.draw.rect(screen, (80, 80, 80), (slot_x, slot_y, slot, slot))
            pygame.draw.rect(screen, (120, 120, 120), (slot_x, slot_y, slot, slot), 2)
            # highlight selected inventory slot
            if inv_selected_idx is not None and idx == inv_selected_idx:
                pygame.draw.rect(screen, (255, 215, 0), (slot_x-2, slot_y-2, slot+4, slot+4), 3)
            if idx < len(inventory):
                it = inventory[idx]
                img = item_images.get(it['id'])
                if img:
                    icon = pygame.transform.scale(img, (slot-8, slot-8))
                    screen.blit(icon, (slot_x+4, slot_y+4))
                font = pygame.font.SysFont(None, max(12, slot//4))
                # draw count in black for 'link' items, white otherwise
                color = (0,0,0) if it['id'] == 'link' else (0,0,0)
                txt = font.render(str(it['count']), True, color)
                screen.blit(txt, (slot_x+slot-10, slot_y+slot-14))
        # draw inventory action menu if open
        if inv_action_menu_open and inv_pending_slot is not None:
            # Increased menu size and spacing to fit extra options (e.g. 'Eat')
            menu_w, menu_h = 220, 110
            menu_x = left_x + left_w + 12
            menu_y = left_y + 16
            pygame.draw.rect(screen, (30,30,40), (menu_x, menu_y, menu_w, menu_h))
            pygame.draw.rect(screen, (200,200,200), (menu_x, menu_y, menu_w, menu_h), 2)
            mfont = pygame.font.SysFont(None, 22)
            # compute vertical spacing based on number of options
            spacing = max(28, (menu_h - 24) // max(1, len(inv_action_options)))
            for i, opt in enumerate(inv_action_options):
                col = (255,255,0) if i == inv_action_selected_idx else (255,255,255)
                screen.blit(mfont.render(opt, True, col), (menu_x + 12, menu_y + 12 + i*spacing))
        # draw confirmation dialog
        if inv_confirm_open and inv_pending_slot is not None:
            menu_w, menu_h = 300, 120
            menu_x = (WIDTH - menu_w) // 2
            menu_y = (HEIGHT - menu_h) // 2
            pygame.draw.rect(screen, (40,40,40), (menu_x, menu_y, menu_w, menu_h))
            pygame.draw.rect(screen, (200,200,200), (menu_x, menu_y, menu_w, menu_h), 2)
            cf = pygame.font.SysFont(None, 22)
            screen.blit(cf.render('Discard this item?', True, (255,255,255)), (menu_x + 12, menu_y + 12))
            opt_yes = 'Yes'
            opt_no = 'No'
            ycol = (255,255,0) if inv_confirm_selected_idx == 0 else (255,255,255)
            ncol = (255,255,0) if inv_confirm_selected_idx == 1 else (255,255,255)
            screen.blit(cf.render(opt_yes, True, ycol), (menu_x + 40, menu_y + 60))
            screen.blit(cf.render(opt_no, True, ncol), (menu_x + 160, menu_y + 60))
       
        # show gold
        txtg = font.render(f"Gold: {gold}", True, (255,215,0))
        screen.blit(txtg, (left_x + 120, left_y - 24))

        # right panel: chest contents when active (scaled)
        if active_chest:
            right_x = layout['right_x']
            right_y = layout['right_y']
            right_w = layout['panel_w']
            right_h = layout['panel_h']
            pygame.draw.rect(screen, (40, 40, 40), (right_x, right_y, right_w, right_h))
            pygame.draw.rect(screen, (200, 200, 200), (right_x, right_y, right_w, right_h), 2)
            for idx in range(cols * rows):
                col = idx % cols
                row = idx // cols
                slot_x = right_x + padding + col * (slot + padding)
                slot_y = right_y + padding + row * (slot + padding)
                pygame.draw.rect(screen, (80, 80, 80), (slot_x, slot_y, slot, slot))
                pygame.draw.rect(screen, (120, 120, 120), (slot_x, slot_y, slot, slot), 2)
                if idx < len(active_chest['items']):
                    it = active_chest['items'][idx]
                    img = item_images.get(it['id'])
                    if img:
                        icon = pygame.transform.scale(img, (slot-8, slot-8))
                        screen.blit(icon, (slot_x+4, slot_y+4))
                    font = pygame.font.SysFont(None, max(12, slot//4))
                    # chest item count: black for 'link'
                    color = (0,0,0) if it['id'] == 'link' else (255,255,255)
                    txt = font.render(str(it['count']), True, color)
                    screen.blit(txt, (slot_x+slot-10, slot_y+slot-14))

        # draw dragging icon if any
        if dragging:
            mx, my = pygame.mouse.get_pos()
            img = item_images.get(dragging['id'])
            layout = get_inventory_layout()
            slot = layout['slot']
            if img:
                icon = pygame.transform.scale(img, (max(8, slot-8), max(8, slot-8)))
                screen.blit(icon, (mx - (slot-8)//2, my - (slot-8)//2))

        pygame.display.flip()

        # while paused allow clicking to transfer items from chest to player inventory
        mouse_pressed = pygame.mouse.get_pressed()
        if active_chest and any(mouse_pressed):
            mx, my = pygame.mouse.get_pos()
            # check right panel slots using layout
            layout = get_inventory_layout()
            right_x = layout['right_x']
            right_y = layout['right_y']
            slot = layout['slot']
            padding = layout['padding']
            cols = layout['cols']
            rows = layout['rows']
            for idx in range(min(len(active_chest['items']), cols * rows)):
                col = idx % cols
                row = idx // cols
                slot_x = right_x + padding + col * (slot + padding)
                slot_y = right_y + padding + row * (slot + padding)
                slot_rect = pygame.Rect(slot_x, slot_y, slot, slot)
                if slot_rect.collidepoint(mx, my):
                    # transfer one item to player inventory
                    item = active_chest['items'][idx]
                    add_item(item['id'], 1)
                    item['count'] -= 1
                    if item['count'] <= 0:
                        del active_chest['items'][idx]
                    break

        # skip all state updates while inventory is open
        continue

    # --- Cooldown timer ---
    if roll_cooldown > 0 and not dialog_open:
        roll_cooldown -= dt

    # --- Movement and Direction Update ---
    dx = dy = 0
    keys = pygame.key.get_pressed()

    # If a dialog is open, pause player movement and most game updates
    if dialog_open:
        dx = dy = 0
        # do not overwrite `keys` — leave key state intact but suppress movement via dx/dy

    # If inventory is open, ignore movement input
    if inventory_open:
        dx = dy = 0
    else:

        # Always check for direction changes, regardless of state
        if keys[pygame.K_w] and keys[pygame.K_a]:
            dy = -player_speed
            dx = -player_speed
            direction = "upleft"
        elif keys[pygame.K_w] and keys[pygame.K_d]:
            dy = -player_speed
            dx = player_speed
            direction = "upright"
        elif keys[pygame.K_s] and keys[pygame.K_a]:
            dy = player_speed
            dx = -player_speed
            direction = "downleft"
        elif keys[pygame.K_s] and keys[pygame.K_d]:
            dy = player_speed
            dx = player_speed
            direction = "downright"
        elif keys[pygame.K_w]:
            dy = -player_speed
            direction = "up"
        elif keys[pygame.K_s]:
            dy = player_speed
            direction = "down"
        elif keys[pygame.K_a]:
            dx = -player_speed
            direction = "left"
        elif keys[pygame.K_d]:
            dx = player_speed
            direction = "right"
    
    # If the player is rolling, override the speed
    if rolling:
        if direction == "up":
            dy = -roll_speed
            dx = 0
        elif direction == "down":
            dy = roll_speed
            dx = 0
        elif direction == "left":
            dx = -roll_speed
            dy = 0
        elif direction == "right":
            dx = roll_speed
            dy = 0
        elif direction == "upleft":
            dx = -roll_speed
            dy = -roll_speed
        elif direction == "upright":
            dx = roll_speed
            dy = -roll_speed
        elif direction == "downleft":
            dx = -roll_speed
            dy = roll_speed
        elif direction == "downright":
            dx = roll_speed
            dy = roll_speed
    elif attacking:
        #If attacking, the player shouldn't move
        dx = dy = 0
    else:
        # If not rolling or attacking, use normal speed
        if not (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]):
            dx = dy = 0

    # slow player on lava: if player's hitbox overlaps lava, halve movement
    try:
        if rect_overlaps_lava(player_hitbox):
            dx *= 0.5
            dy *= 0.5
    except Exception:
        pass

    # --- Build solid tiles list (for collisions) ---
    solid_tiles = []
    for row in range(len(tilemap)):
        for col in range(len(tilemap[row])):
            t = tilemap[row][col]
            if t in (1, 2, 4):
                solid_tiles.append(pygame.Rect(col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # --- Move X and check collisions ---
    player_rect.x += dx
    for tile in solid_tiles:
        if player_rect.colliderect(tile):
            if dx > 0:
                player_rect.right = tile.left
            elif dx < 0:
                player_rect.left = tile.right

    # prevent overlapping NPCs on X axis
    try:
        area_npcs = npcs_by_area.get(current_area, [])
        for npc in area_npcs:
            nr = npc.get('rect')
            if nr and player_rect.colliderect(nr):
                if dx > 0:
                    player_rect.right = nr.left
                elif dx < 0:
                    player_rect.left = nr.right
    except Exception:
        pass

    # --- Move Y and check collisions ---
    player_rect.y += dy
    for tile in solid_tiles:
        if player_rect.colliderect(tile):
            if dy > 0:
                player_rect.bottom = tile.top
            elif dy < 0:
                player_rect.top = tile.bottom

    # prevent overlapping NPCs on Y axis
    try:
        area_npcs = npcs_by_area.get(current_area, [])
        for npc in area_npcs:
            nr = npc.get('rect')
            if nr and player_rect.colliderect(nr):
                if dy > 0:
                    player_rect.bottom = nr.top
                elif dy < 0:
                    player_rect.top = nr.bottom
    except Exception:
        pass

    # --- Keep player inside world bounds ---
    world_w = len(tilemap[0]) * TILE_SIZE
    world_h = len(tilemap) * TILE_SIZE
    player_rect.left = max(0, player_rect.left)
    player_rect.right = min(world_w, player_rect.right)
    player_rect.top = max(0, player_rect.top)
    player_rect.bottom = min(world_h, player_rect.bottom)

    # --- Area transition triggers ---
    # If we're in area 0 and player reaches the rightmost pathway tiles, switch to area 1
    try:
        if current_area == 0:
            # check tile under player's center
            pc_r = player_rect.centery // TILE_SIZE
            pc_c = player_rect.centerx // TILE_SIZE
            if pc_c >= 0 and pc_r >= 0 and pc_r < len(tilemap_area0) and pc_c < len(tilemap_area0[pc_r]):
                if tilemap_area0[pc_r][pc_c] == 5 and player_rect.centerx >= (len(tilemap_area0[0]) - 2) * TILE_SIZE:
                    # move to area 1, spawn near left pathway
                    switch_area(1, spawn_pos=(TILE_SIZE * 2, TILE_SIZE * 8))
        elif current_area == 1:
            # if in area1 and player reaches left pathway, go back to area0
            pc_r = player_rect.centery // TILE_SIZE
            pc_c = player_rect.centerx // TILE_SIZE
            if pc_c >= 0 and pc_r >= 0 and pc_r < len(tilemap_area1) and pc_c < len(tilemap_area1[pc_r]):
                if tilemap_area1[pc_r][pc_c] == 5 and player_rect.centerx <= TILE_SIZE * 3:
                    # back to area 0, spawn at rightmost pathway entry point (approx)
                    # find a pathway tile near the right edge in area0 to place the player
                    spawn_x = (len(tilemap_area0[0]) - 3) * TILE_SIZE
                    spawn_y = TILE_SIZE * 8
                    switch_area(0, spawn_pos=(spawn_x, spawn_y))
    except Exception:
        pass

    # --- Camera panning / follow logic ---
    # if camera is following, center on player; otherwise allow arrow-key panning
    # pan camera with arrow keys; pressing arrows disables follow
    pan_dx = pan_dy = 0
    if not dialog_open:
        if keys[pygame.K_LEFT]:
            camera_follow = False
            pan_dx = -CAM_PAN_SPEED * (dt / 1000.0)
        if keys[pygame.K_RIGHT]:
            camera_follow = False
            pan_dx = CAM_PAN_SPEED * (dt / 1000.0)
        if keys[pygame.K_UP]:
            camera_follow = False
            pan_dy = -CAM_PAN_SPEED * (dt / 1000.0)
        if keys[pygame.K_DOWN]:
            camera_follow = False
            pan_dy = CAM_PAN_SPEED * (dt / 1000.0)

    if camera_follow:
        # center on player but clamp to world bounds (do not disable follow)
        target_x = player_rect.centerx
        target_y = player_rect.centery
        max_w = len(tilemap[0]) * TILE_SIZE
        max_h = len(tilemap) * TILE_SIZE
        half_w = CAM_W // 2
        half_h = CAM_H // 2
        cam_x = max(half_w, min(max_w - half_w, target_x))
        cam_y = max(half_h, min(max_h - half_h, target_y))
    else:
        if pan_dx != 0 or pan_dy != 0:
            cam_x += pan_dx
            cam_y += pan_dy
            # ensure camera within world bounds
            max_w = len(tilemap[0]) * TILE_SIZE
            max_h = len(tilemap) * TILE_SIZE
            half_w = CAM_W // 2
            half_h = CAM_H // 2
            cam_x = max(half_w, min(max_w - half_w, cam_x))
            cam_y = max(half_h, min(max_h - half_h, cam_y))
    # (camera no longer locks; it is clamped to world bounds)

    # --- Damage / Invulnerability handling ---
    if invuln_timer > 0 and not dialog_open:
        invuln_timer -= dt
    # Passive healing removed — no automatic health regeneration

    # compute circular player hitbox (circle centered on player) and mask for per-pixel overlap
    try:
        circ_size = (PLAYER_HIT_RADIUS * 2, PLAYER_HIT_RADIUS * 2)
        circ_surf = pygame.Surface(circ_size, pygame.SRCALPHA)
        pygame.draw.circle(circ_surf, (255,255,255,255), (PLAYER_HIT_RADIUS, PLAYER_HIT_RADIUS), PLAYER_HIT_RADIUS)
        player_mask = pygame.mask.from_surface(circ_surf)
        # bounding rect used for tile/lava overlap checks
        player_hitbox = pygame.Rect(player_rect.centerx - PLAYER_HIT_RADIUS, player_rect.centery - PLAYER_HIT_RADIUS, PLAYER_HIT_RADIUS*2, PLAYER_HIT_RADIUS*2)
    except Exception:
        # fallback: use a simple square mask of radius*2
        try:
            player_mask = pygame.mask.Mask((PLAYER_HIT_RADIUS*2, PLAYER_HIT_RADIUS*2))
        except Exception:
            player_mask = pygame.mask.Mask((player_rect.width, player_rect.height))
        player_hitbox = pygame.Rect(player_rect.centerx - PLAYER_HIT_RADIUS, player_rect.centery - PLAYER_HIT_RADIUS, PLAYER_HIT_RADIUS*2, PLAYER_HIT_RADIUS*2)

    # --- Lava damage: if player's hitbox overlaps any lava tile (tile id 3) ---
    # Apply 5 damage and set invulnerability to avoid repeated ticks
    try:
        if invuln_timer <= 0 and not rolling:
            left = player_hitbox.left // TILE_SIZE
            right = (player_hitbox.right - 1) // TILE_SIZE
            top = player_hitbox.top // TILE_SIZE
            bottom = (player_hitbox.bottom - 1) // TILE_SIZE
            hit_lava = False
            for r in range(top, bottom + 1):
                if r < 0 or r >= len(tilemap):
                    continue
                for c in range(left, right + 1):
                    if c < 0 or c >= len(tilemap[r]):
                        continue
                    if tilemap[r][c] == 3:
                        hit_lava = True
                        break
                if hit_lava:
                    break
            if hit_lava:
                health = max(0, health - 5)
                invuln_timer = INVULN_MS
    except Exception:
        pass

    # Enemy AI: unified update for all enemies when dialog is not open
    if not dialog_open:
        for e in enemies[:]:
            enemy_ai_update(e, dt)

            # per-pixel collision: rect pre-check then mask.overlap with current rotated mask
            try:
                er = e.get('rect')
                if er is None:
                    continue
                if player_hitbox.colliderect(er):
                    offset = (er.left - player_hitbox.left, er.top - player_hitbox.top)
                    overlap_point = None
                    try:
                        dir_idx = e.get('dir_idx', 0)
                        if 0 <= dir_idx < len(enemy_dir_masks):
                            masks_list = enemy_dir_masks[dir_idx]
                            fi = e.get('frame_idx', 0)
                            if 0 <= fi < len(masks_list):
                                enemy_mask = masks_list[fi]
                                overlap_point = player_mask.overlap(enemy_mask, offset)
                    except Exception:
                        overlap_point = None

                    # allow damage only if masks overlap OR Kirby is within ~4 pixels of enemy (approx via inflated rect)
                    close_enough = player_hitbox.colliderect(er.inflate(8, 8))
                    if (overlap_point or close_enough):
                        if (not rolling) and invuln_timer <= 0:
                            health = max(0, health - 10)
                            invuln_timer = INVULN_MS
            except Exception:
                pass

            # --- Enemy lava damage check ---
            try:
                if e.get('lava_timer', 0) > 0:
                    e['lava_timer'] = max(0, e['lava_timer'] - dt)
                left_e = er.left // TILE_SIZE
                right_e = (er.right - 1) // TILE_SIZE
                top_e = er.top // TILE_SIZE
                bottom_e = (er.bottom - 1) // TILE_SIZE
                enemy_on_lava = False
                for rr in range(top_e, bottom_e + 1):
                    if rr < 0 or rr >= len(tilemap):
                        continue
                    for cc in range(left_e, right_e + 1):
                        if cc < 0 or cc >= len(tilemap[rr]):
                            continue
                        if tilemap[rr][cc] == 3:
                            enemy_on_lava = True
                            break
                    if enemy_on_lava:
                        break
                if enemy_on_lava and e.get('lava_timer', 0) <= 0:
                    e['health'] = e.get('health', 100) - 5
                    e['lava_timer'] = INVULN_MS
            except Exception:
                pass

        # --- Keep enemies inside world bounds (no respawning) ---
        try:
            world_w = len(tilemap[0]) * TILE_SIZE
            world_h = len(tilemap) * TILE_SIZE
            world_rect = pygame.Rect(0, 0, world_w, world_h)
            for en in enemies:
                er = en['rect']
                if not world_rect.colliderect(er):
                    # clamp inside world bounds
                    er.left = max(0, min(er.left, world_rect.width - er.width))
                    er.top = max(0, min(er.top, world_rect.height - er.height))
                    en['health'] = en.get('health', 100)
                    en['hurt_timer'] = 0
                    en['lava_timer'] = 0
                    en['frame_idx'] = 0
                    en['anim_timer'] = 0
                    en['path'] = None
                    en['path_idx'] = 0
                    en['path_timer'] = 0
                    en['roam_target'] = None
                    en['roam_timer'] = 0
        except Exception:
            pass

        # remove enemies killed by lava or other means and award gold
        remaining = []
        removed_any = False
        for en in enemies:
            if en.get('health', 100) > 0:
                remaining.append(en)
            else:
                try:
                    gold += 20
                    # determine position from enemy rect if available
                    er = en.get('rect') if isinstance(en, dict) else None
                    if isinstance(er, pygame.Rect):
                        fx = er.centerx
                        fy = er.top - 8
                    else:
                        fx = player_rect.centerx
                        fy = player_rect.top - 8
                    floating_messages.append({'text': '+20 gold!', 'timer': MSG_MS, 'x': fx, 'y': fy})
                    removed_any = True
                except Exception:
                    pass
        enemies = remaining
        if removed_any:
            save_game()

    # --- Sword hit detection: check sword_hitbox against enemies ---
    if sword_hitbox and attacking:
        dead = []
        for idx, e in enumerate(enemies):
            er = e['rect']
            # rect pre-check
            if sword_hitbox.colliderect(er):
                # only apply if enemy not recently hurt
                if e.get('hurt_timer', 0) <= 0:
                    # apply damage
                    e['health'] = e.get('health', 100) - 25
                    e['hurt_timer'] = 300
                    # apply immediate knockback away from the player
                    dx_kb = er.centerx - player_rect.centerx
                    dy_kb = er.centery - player_rect.centery
                    dist_kb = math.hypot(dx_kb, dy_kb)
                    if dist_kb == 0:
                        dist_kb = 1
                        dx_kb = 1
                    nx = dx_kb / dist_kb
                    ny = dy_kb / dist_kb
                    er.x += int(nx * ENEMY_KNOCKBACK)
                    er.y += int(ny * ENEMY_KNOCKBACK)
                    if e['health'] <= 0:
                        dead.append(idx)
                        try:
                            gold += 20
                            floating_messages.append({'text': '+20 gold!', 'timer': MSG_MS, 'x': er.centerx, 'y': er.top - 8})
                        except Exception:
                            pass
                        save_game()
        # remove dead enemies (from end to start)
        for i in sorted(dead, reverse=True):
            del enemies[i]

    # --- Handle animations ---
    sword_hitbox = None
    if attacking:
        attack_timer += dt
        frame_index = int(attack_timer / frame_time_ms)
        if frame_index >= len(swing_right):
            attacking = False
            attack_timer = 0
        else:
            if direction == "right":
                player_img = swing_right[frame_index]
                w, h = player_img.get_size()
                sword_hitbox = pygame.Rect(player_rect.right + SWORD_HIT_OFFSET, player_rect.centery - h//4, w//2, h//2)
            elif direction == "left":
                player_img = swing_left[frame_index]
                w, h = player_img.get_size()
                sword_hitbox = pygame.Rect(player_rect.left - w//2 - SWORD_HIT_OFFSET, player_rect.centery - h//4, w//2, h//2)
            elif direction == "up":
                player_img = swing_up[frame_index]
                w, h = player_img.get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx - w//4, player_rect.top - h//2 - SWORD_HIT_OFFSET, w//2, h//2)
            elif direction == "down":
                player_img = swing_down[frame_index]
                w, h = player_img.get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx - w//4, player_rect.bottom + SWORD_HIT_OFFSET, w//2, h//2)
            elif direction == "upleft":
                player_img = swing_up_left[frame_index]
                w, h = swing_right[frame_index].get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx - w//2 - SWORD_DIAG_OFFSET//2, player_rect.centery - h//4 - SWORD_DIAG_OFFSET//2, w//2, h//2)
            elif direction == "upright":
                player_img = swing_up_right[frame_index]
                w, h = swing_right[frame_index].get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx + SWORD_DIAG_OFFSET//2, player_rect.centery - h//4 - SWORD_DIAG_OFFSET//2, w//2, h//2)
            elif direction == "downleft":
                player_img = swing_down_left[frame_index]
                w, h = swing_right[frame_index].get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx - w//2 - SWORD_DIAG_OFFSET//2, player_rect.centery + SWORD_DIAG_OFFSET//2, w//2, h//2)
            elif direction == "downright":
                player_img = swing_down_right[frame_index]
                w, h = swing_right[frame_index].get_size()
                sword_hitbox = pygame.Rect(player_rect.centerx + SWORD_DIAG_OFFSET//2, player_rect.centery + SWORD_DIAG_OFFSET//2, w//2, h//2)
    elif rolling:
        roll_timer += dt
        frame_index = int((roll_timer / roll_time_ms) * len(roll_right))
        if frame_index >= len(roll_right):
            rolling = False
            roll_timer = 0
        else:
            if direction == "right":
                player_img = roll_right[frame_index]
            elif direction == "left":
                player_img = roll_left[frame_index]
            elif direction == "up":
                player_img = roll_up[frame_index]
            elif direction == "down":
                player_img = roll_down[frame_index]
            elif direction == "upleft":
                player_img = roll_up_left[frame_index]
            elif direction == "upright":
                player_img = roll_up_right[frame_index]
            elif direction == "downleft":
                player_img = roll_down_left[frame_index]
            elif direction == "downright":
                player_img = roll_down_right[frame_index]
    else:
        # Walking / idle animation
        if dx != 0 or dy != 0:
            current_frame += animation_speed
            if direction == "down":
                player_img = walk_down[int(current_frame) % len(walk_down)]
            elif direction == "up":
                player_img = walk_up[int(current_frame) % len(walk_up)]
            elif direction == "right":
                player_img = walk_right[int(current_frame) % len(walk_right)]
            elif direction == "left":
                player_img = walk_left[int(current_frame) % len(walk_left)]
            elif direction == "upleft":
                player_img = walk_up_left[int(current_frame) % len(walk_up_left)]
            elif direction == "upright":
                player_img = walk_up_right[int(current_frame) % len(walk_up_right)]
            elif direction == "downright":
                player_img = walk_down_right[int(current_frame) % len(walk_down_right)]
            elif direction == "downleft":
                player_img = walk_down_left[int(current_frame) % len(walk_down_left)]
        else:
            current_frame = 0
            if direction == "down": 
                player_img = walk_down[0]
            elif direction == "up": 
                player_img = walk_up[0]
            elif direction == "right": 
                player_img = walk_right[0]
            elif direction == "left": 
                player_img = walk_left[0]
            elif direction == "upleft":
                player_img = walk_up_left[0]
            elif direction == "upright":
                player_img = walk_up_right[0]
            elif direction == "downleft":
                player_img = walk_down_left[0]
            elif direction == "downright":
                player_img = walk_down_right[0]

    # --- Draw map & player via camera surface ---
    camera_surf.fill((0,0,0))
    cam_left = int(cam_x - CAM_W // 2)
    cam_top = int(cam_y - CAM_H // 2)
    # draw tiles into camera
    for row in range(len(tilemap)):
        for col in range(len(tilemap[row])):
            tile_type = tilemap[row][col]
            px = col * TILE_SIZE - cam_left
            py = row * TILE_SIZE - cam_top
            if px + TILE_SIZE < 0 or py + TILE_SIZE < 0 or px > CAM_W or py > CAM_H:
                continue
            if current_area == 1 and tavern_origin and tavern_subs:
                ox, oy = tavern_origin
                bx = col - ox
                by = row - oy
                subimg = tavern_subs.get((bx, by))
                if subimg:
                    camera_surf.blit(subimg, (px, py))
                    continue
            camera_surf.blit(tiles[tile_type], (px, py))

    # draw enemies
    for e in enemies:
        er = e['rect']
        dx_e = player_rect.centerx - er.centerx
        dy_e = player_rect.centery - er.centery
        angle = (math.degrees(math.atan2(dy_e, dx_e)) + 360) % 360
        dir_idx = int((angle + 22.5) // 45) % 8
        frame = enemy_dir_frames[dir_idx][e['frame_idx']]
        ex = er.left - cam_left
        ey = er.top - cam_top
        if ex + er.width < 0 or ey + er.height < 0 or ex > CAM_W or ey > CAM_H:
            continue
        camera_surf.blit(frame, (ex, ey))
        # draw enemy health bar
        eh = e.get('health', 100)
        eh_max = 100
        hb_w, hb_h = er.width, 6
        hb_x = ex
        hb_y = ey - 10
        pygame.draw.rect(camera_surf, (60,60,60), (hb_x, hb_y, hb_w, hb_h))
        fill = int((eh / eh_max) * hb_w)
        pygame.draw.rect(camera_surf, (180,40,40), (hb_x, hb_y, fill, hb_h))
        pygame.draw.rect(camera_surf, (200,200,200), (hb_x, hb_y, hb_w, hb_h), 1)
    # draw NPCs for current area
    area_npcs = npcs_by_area.get(current_area, [])
    for npc in area_npcs:
        try:
            npc_update(npc, dt)
        except Exception:
            pass
        nr = npc['rect']
        dir_idx = npc.get('dir_idx', npc.get('facing', 0)) % len(npc_dir_frames)
        fi = npc.get('frame_idx', 0) % len(npc_dir_frames[0])
        surf = npc_dir_frames[dir_idx][fi]
        nx = nr.left - cam_left
        ny = nr.top - cam_top
        if nx + nr.width < 0 or ny + nr.height < 0 or nx > CAM_W or ny > CAM_H:
            continue
        camera_surf.blit(surf, (nx, ny))

    # draw player
    px = player_rect.left - cam_left
    py = player_rect.top - cam_top
    camera_surf.blit(player_img, (px, py))

    # blit camera to main screen centered
    sx = (WIDTH - CAM_W) // 2
    sy = (HEIGHT - CAM_H) // 2
    screen.fill((0,0,0))
    screen.blit(camera_surf, (sx, sy))

    # --- Debug: draw sword hitbox if active ---
    if sword_hitbox:
        # translate to camera coords
        sb_x = sword_hitbox.left - cam_left + sx
        sb_y = sword_hitbox.top - cam_top + sy
        pygame.draw.rect(screen, (255, 0, 0), (sb_x, sb_y, sword_hitbox.width, sword_hitbox.height), 2)

    # --- Inventory UI ---
    if inventory_open:
        # translucent background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        # Use get_inventory_layout for all inventory/chest UI and dragging icon
        layout = get_inventory_layout()
        left_x = layout['left_x']
        left_y = layout['left_y']
        right_x = layout['right_x']
        right_y = layout['right_y']
        slot = layout['slot']
        padding = layout['padding']
        cols = layout['cols']
        rows = layout['rows']
        panel_w = layout['panel_w']
        panel_h = layout['panel_h']

        # left panel (player inventory)
        pygame.draw.rect(screen, (40, 40, 40), (left_x, left_y, panel_w, panel_h))
        pygame.draw.rect(screen, (200, 200, 200), (left_x, left_y, panel_w, panel_h), 2)
        for idx in range(cols * rows):
            col = idx % cols
            row = idx // cols
            slot_x = left_x + padding + col * (slot + padding)
            slot_y = left_y + padding + row * (slot + padding)
            pygame.draw.rect(screen, (80, 80, 80), (slot_x, slot_y, slot, slot))
            pygame.draw.rect(screen, (120, 120, 120), (slot_x, slot_y, slot, slot), 2)
            if idx < len(inventory):
                it = inventory[idx]
                img = item_images.get(it['id'])
                if img:
                    icon = pygame.transform.scale(img, (max(8, slot-8), max(8, slot-8)))
                    screen.blit(icon, (slot_x+4, slot_y+4))
                font = pygame.font.SysFont(None, max(12, slot//4))
                color = (0,0,0) if it['id'] == 'link' else (255,255,255)
                txt = font.render(str(it['count']), True, color)
                screen.blit(txt, (slot_x+slot-10, slot_y+slot-14))

        # right panel (chest contents if active, otherwise empty)
        pygame.draw.rect(screen, (40, 40, 40), (right_x, right_y, panel_w, panel_h))
        pygame.draw.rect(screen, (200, 200, 200), (right_x, right_y, panel_w, panel_h), 2)
        if active_chest:
            for idx in range(cols * rows):
                col = idx % cols
                row = idx // cols
                slot_x = right_x + padding + col * (slot + padding)
                slot_y = right_y + padding + row * (slot + padding)
                pygame.draw.rect(screen, (80, 80, 80), (slot_x, slot_y, slot, slot))
                pygame.draw.rect(screen, (120, 120, 120), (slot_x, slot_y, slot, slot), 2)
                if idx < len(active_chest['items']):
                    it = active_chest['items'][idx]
                    img = item_images.get(it['id'])
                    if img:
                        icon = pygame.transform.scale(img, (max(8, slot-8), max(8, slot-8)))
                        screen.blit(icon, (slot_x+4, slot_y+4))
                    font = pygame.font.SysFont(None, max(12, slot//4))
                    color = (0,0,0) if it['id'] == 'link' else (255,255,255)
                    txt = font.render(str(it['count']), True, color)
                    screen.blit(txt, (slot_x+slot-10, slot_y+slot-14))

        # show totals above left panel
        total_links = sum(it['count'] for it in inventory if it['id'] == 'link')
        font = pygame.font.SysFont(None, 22)
        txt2 = font.render(f"Links: {total_links}", True, (255,255,255))
        screen.blit(txt2, (left_x + 6, left_y - 24))
        txtg = font.render(f"Gold: {gold}", True, (255,215,0))
        screen.blit(txtg, (left_x + 120, left_y - 24))

        # draw dragging icon if any
        if dragging:
            mx, my = pygame.mouse.get_pos()
            img = item_images.get(dragging['id'])
            if img:
                icon = pygame.transform.scale(img, (max(8, slot-8), max(8, slot-8)))
                screen.blit(icon, (mx - (slot-8)//2, my - (slot-8)//2))

    # --- Health Bar (top-left) - only when inventory closed ---
    if not inventory_open:
        bar_x, bar_y = 12, 12
        bar_w, bar_h = 200, 20
        # background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        # filled
        fill_w = int((health / max_health) * (bar_w - 4))
        pygame.draw.rect(screen, (200, 30, 30), (bar_x+2, bar_y+2, fill_w, bar_h-4))
        # border
        pygame.draw.rect(screen, (220, 220, 220), (bar_x, bar_y, bar_w, bar_h), 2)
        # text
        font = pygame.font.SysFont(None, 20)
        hp_text = font.render(f"HP: {int(health)}/{max_health}", True, (255,255,255))
        screen.blit(hp_text, (bar_x + 6, bar_y + 1))

    # draw temporary message if any (overlayed before final flip)
    if msg_timer > 0:
        msg_timer -= dt
        if msg_timer > 0 and msg_text:
            fontm = pygame.font.SysFont(None, 28)
            m = fontm.render(msg_text, True, (255,255,255))
            mx = (WIDTH - m.get_width()) // 2
            my = 24
            screen.blit(m, (mx, my))

    # update and draw floating messages (each has its own timer and position)
    if floating_messages:
        fm_font = pygame.font.SysFont(None, 22)
        to_keep = []
        # compute camera-to-screen offsets
        cam_screen_x = (WIDTH - CAM_W) // 2
        cam_screen_y = (HEIGHT - CAM_H) // 2
        cam_left = int(cam_x - CAM_W // 2)
        cam_top = int(cam_y - CAM_H // 2)
        for msg in floating_messages:
            try:
                msg['timer'] -= dt
                # move message upward slowly (pixels per second)
                msg['y'] -= (dt / 1000.0) * 20
                if msg.get('timer', 0) > 0:
                    txts = fm_font.render(msg.get('text', ''), True, (255, 215, 0))
                    screen_x = int(msg.get('x', 0) - cam_left + cam_screen_x)
                    screen_y = int(msg.get('y', 0) - cam_top + cam_screen_y)
                    # draw if on screen, otherwise fallback to top center
                    try:
                        if 0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT:
                            screen.blit(txts, (screen_x - txts.get_width()//2, screen_y))
                        else:
                            screen.blit(txts, ((WIDTH - txts.get_width())//2, 48))
                    except Exception:
                        screen.blit(txts, ((WIDTH - txts.get_width())//2, 48))
                    to_keep.append(msg)
            except Exception:
                pass
        floating_messages = to_keep

    # draw dialog box if open (centered at bottom)
    if dialog_open:
        try:
            box_w = min(WIDTH - 80, 560)
            box_h = 120
            box_x = (WIDTH - box_w) // 2
            box_y = HEIGHT - box_h - 24
            # background
            pygame.draw.rect(screen, (20,20,30), (box_x, box_y, box_w, box_h))
            pygame.draw.rect(screen, (220,220,220), (box_x, box_y, box_w, box_h), 2)
            df = pygame.font.SysFont(None, 24)
            # render current line with word-wrap
            line = dialog_current_line()
            # simple wrap
            words = line.split()
            lines = []
            cur = ''
            for w in words:
                test = (cur + ' ' + w).strip() if cur else w
                if df.size(test)[0] <= box_w - 24:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            sy = box_y + 12
            for ln in lines[:4]:
                screen.blit(df.render(ln, True, (240,240,240)), (box_x + 12, sy))
                sy += 26
            # hint: press SPACE to continue/close
            hint = pygame.font.SysFont(None, 18).render('Press SPACE to continue', True, (180,180,180))
            screen.blit(hint, (box_x + box_w - hint.get_width() - 12, box_y + box_h - hint.get_height() - 8))
        except Exception:
            import traceback
            traceback.print_exc()
            try:
                print(f"DEBUG dialog_index={dialog_index} dialog_len={dialog_len()} dialog_lines={dialog_lines}")
            except Exception:
                pass
            # close the dialog to avoid repeated errors
            dialog_open = False
            dialog_lines = []
            dialog_index = 0

    # final flip: present composed frame (camera + UI + messages/dialog)
    pygame.display.flip()

    # --- Game over state handling ---
    if health <= 0 and not game_over:
        game_over = True

    if game_over:
        go_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        go_overlay.fill((0,0,0,200))
        screen.blit(go_overlay, (0,0))
        font = pygame.font.SysFont(None, 64)
        txt = font.render("GAME OVER", True, (255, 50, 50))
        tx = (WIDTH - txt.get_width()) // 2
        ty = (HEIGHT - txt.get_height()) // 2 - 40
        screen.blit(txt, (tx, ty))
        font2 = pygame.font.SysFont(None, 28)
        t2 = font2.render("Press R to Restart or Q to Quit", True, (255,255,255))
        screen.blit(t2, ((WIDTH - t2.get_width()) // 2, ty + 80))
        pygame.display.flip()
        # pause loop until input handled by event loop
        continue
