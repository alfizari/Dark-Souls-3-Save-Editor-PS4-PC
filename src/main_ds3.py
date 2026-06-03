
from tkinter import filedialog, messagebox
import os, struct, json
import pc as PC
import sys
import threading, time



AOB_search       = 'FF FF FF FF FF FF FF FF FF FF FF FF ??'
souls_distance   = -219
hp_distance      = -303
fp_distance      = -291
stamina_distance = -275
MODE             = None   # "PC" | "ps4"

stats_offsets_for_stats_tap = {
    "Level":                         -223,
    "Vigor":                         -267,
    "Attunement":                    -263,
    "Endurance":                     -259,
    "Vitality":                      -227,
    "Strength":                      -255,
    "Dexterity":                     -251,
    "Intelligence":                  -247,
    "Faith":                         -243,
    "Luck":                          -239,
}

bosses_offsets_for_bosses_tap = {
    "Iudex Gundyr":                          23254,
    "Vordt of the Boreal Valley":             4054,
    "Curse-Rotted Greatwood":                 6614,
    "Crystal Sage":                          11736,
    "Abyss Watchers":                        11734,
    "High Lord Wolnir":                      20694,
    "Oceiros, the Consumed King (pt1)":       4051,
    "Oceiros, the Consumed King (pt2)":       4058,
    "Champion Gundyr":                       23251,
    "Dancer of the Boreal Valley":            4059,
    "Deacons of the Deep":                   15574,
    "Old Demon King":                        20691,
    "Pontiff Sulyvahn":                      19416,
    "Aldrich, Devourer of Gods":             19414,
    "Dragonslayer Armour":                    5334,
    "Yhorm the Giant":                       21974,
    "Nameless King":                          9176,
    "Twin Princes":                          14291,
    "Soul of Cinder":                        24534,
    "Champion's Gravetender (DLC)":          25815,
    "Father Ariandel and Sister Friede (DLC)": 25814,
    "Halflight, Spear of the Church (DLC)":  30934,
    "Darkeater Midir (DLC)":                 30936,
    "Slave Knight Gael (DLC)":               32214,
    "Demon Prince (DLC)":                    29654,
}

bonfire_offsets_for_bonfire_tap = {
    "Activate Lord of Cinders in Firelink Shrine": 1288,
    "Cemetary of Ash":                        23154,
    "High Wall of Lothric":                    3953,
    "Undead Settlement":                       6514,
    "Archdragon Peak":                         9074,
    "Kiln of the First Flame":                24434,
    "Catacombs of Carthus":                   20594,
    "Irithyll of the Boreal Valley":          19313,
    "Unlock Ariende's Room":                  25789,
    "The Dreg Heap":                          29554,
    "Irithyll Dungeon":                       21874,
    "Road of Sacrifices":                     11633,
    "Cathedral of the Deep":                  15474,
    "Lothric Castle":                          5234,
    "Grand Archives":                         14194,
    "Painted World of Ariandel (DLC)":        25714,
    "The Ringed City (DLC)":                  30834,
    "Filianore's Rest & Slave Knight Gael":   32114,
}

if not sys:
    exit()



working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

def load_json(file_name):
    file_path = os.path.join(working_directory, "Resources/Json", file_name)
    with open(file_path, "r") as f:
        return json.load(f)

bosses_data    = load_json('Bosses.json')
bonfire_data   = load_json("bonfire.json")
goods_id       = load_json('goods_magic.json')
rings_id       = load_json('ring.json')
weapons_id     = load_json('weapons.json')
armors_id      = load_json('armor.json')
goods_id_bulk  = load_json('goods_magic_bulk.json')



ITEM_TYPE_EMPTY  = 0x00000000
ITEM_TYPE_WEAPON = 0x80000000
ITEM_TYPE_ARMOR  = 0x90000000
ITEM_TYPE_GOOD   = 0xB0000000
ITEM_TYPE_RINGS  = 0xA0000000



def calculate_offset2(offset1, distance):
    return offset1 + distance

def aob_to_pattern(aob: str):
    parts = aob.split()
    pattern = bytearray()
    mask    = bytearray()
    for p in parts:
        if p == "??":
            pattern.append(0x00); mask.append(2)
        elif p == "!!":
            pattern.append(0x00); mask.append(0)
        else:
            pattern.append(int(p, 16)); mask.append(1)
    return bytes(pattern), bytes(mask)

def aob_search(data: bytes, aob: str, min_offset: int = 0):
    pattern, mask = aob_to_pattern(aob)
    L  = len(pattern)
    mv = memoryview(data)
    for i in range(min_offset, len(data) - L + 1):
        ok = True
        for j in range(L):
            if mask[j] == 1:
                if mv[i + j] != pattern[j]: ok = False; break
            elif mask[j] == 2:
                if mv[i + j] == 0x00:       ok = False; break
        if ok:
            return i
    return None



class Item:
    BASE_SIZE = 8

    def __init__(self, gaitem_handle, item_id, offset, size=8):
        self.gaitem_handle = gaitem_handle
        self.item_id       = item_id
        self.size          = size
        self.offset        = offset

    @classmethod
    def from_bytes(cls, data_type, offset=0):
        gaitem_handle, item_id = struct.unpack_from("<II", data_type, offset)
        type_bits = gaitem_handle & 0xF0000000
        cursor    = offset + cls.BASE_SIZE
        size      = cls.BASE_SIZE
        if gaitem_handle != 0:
            if type_bits in (ITEM_TYPE_WEAPON, ITEM_TYPE_ARMOR):
                cursor += 52
                size    = cursor - offset
        return cls(gaitem_handle, item_id, offset, size)

def parse_items(data_type, start_offset, slots=6144):
    items  = []
    offset = start_offset
    for _ in range(slots):
        item = Item.from_bytes(data_type, offset)
        items.append(item)
        offset += item.size
    return items, offset

def gaprint(data_type, slots=6144):
    ga_items = []; ga_weapons = []; ga_armors = []; ga_empty = []
    items, end_offset = parse_items(data_type, 0x70, slots)
    for item in items:
        tb = item.gaitem_handle & 0xF0000000
        ga_items.append((item.gaitem_handle, item.item_id, item.offset))
        if   tb == ITEM_TYPE_WEAPON: ga_weapons.append((item.gaitem_handle, item.item_id, item.offset))
        elif tb == ITEM_TYPE_ARMOR:  ga_armors.append ((item.gaitem_handle, item.item_id, item.offset))
        elif tb == ITEM_TYPE_EMPTY:  ga_empty.append  ((item.gaitem_handle, item.item_id, item.offset))
    return end_offset, ga_items, ga_armors, ga_weapons, ga_empty


def parse_save(data):
    end_offset, *_ = gaprint(data)

    magic_start           = end_offset + 0x13F
    inventory_start       = magic_start + 0x1dd
    inventory_end         = inventory_start + 0x8808
    above_storage_counter = inventory_end + 0x11c
    above_storage_size    = struct.unpack_from('<I', data, above_storage_counter)[0]
    table_1_end           = above_storage_counter + 4 + (above_storage_size * 8)
    face_data_maybe       = table_1_end + 0x18c
    storage_box_start     = face_data_maybe + 0x4
    storage_box_end       = storage_box_start + 0x8800
    gesture_start         = storage_box_end + 0xc
    gesture_end           = gesture_start + 0xa4
    table_2_size          = struct.unpack_from('<I', data, gesture_end)[0]
    table_2_end           = gesture_end + 4 + (table_2_size * 4)
    new_game_plus         = table_2_end + 0x92
    event_flag_start      = new_game_plus + 0xbCC
    event_flag_end        = event_flag_start + 0x33e5e
    block_1_size          = struct.unpack_from('<I', data, event_flag_end)[0]
    block_1_end           = event_flag_end + 4 + block_1_size
    block_2_size          = struct.unpack_from('<I', data, block_1_end)[0]
    block_2_end           = block_1_end + 4 + block_2_size
    block_3_size          = struct.unpack_from('<I', data, block_2_end)[0]
    block_3_end           = block_2_end + 4 + block_3_size
    block_4_end           = block_3_end + 0xe
    block_5_start         = block_4_end + 0x6a
    block_5_size          = struct.unpack_from('<I', data, block_5_start)[0]
    block_5_end           = block_5_start + 4 + block_5_size
    block_6_start         = block_5_end + 4
    block_6_size          = struct.unpack_from('<I', data, block_6_start)[0]
    block_6_end           = block_6_start + 4 + block_6_size

    steam_id = aob_search(data[block_6_end:], AOB_search)
    if MODE == 'PC' and steam_id is None:
        print('Cannot find steam id')

    steam_id_offset      = steam_id + block_6_end if steam_id is not None else None
    steam_id_offset_true = (steam_id_offset + 0x1c) if steam_id_offset is not None else None

    return {
        "steam_id_offset_true": steam_id_offset_true,
        "new_game_plus":        new_game_plus,
        "event_flag_start":     event_flag_start,
        "inventory_start":      inventory_start,
        "storage_box_start":    storage_box_start,
        "storage_box_end":      storage_box_end,
    }

def check_steam_id(data):
    steam_offset = parse_save(data)["steam_id_offset_true"]
    if steam_offset is None:
        return None, None
    steam_id_value = struct.unpack_from('<Q', data, steam_offset)[0]
    steam = int.to_bytes(steam_id_value, 8, 'little')
    return steam, steam_offset



def find_char_name(data):
    end_offset_ga, *_ = gaprint(data)
    char_name_offset   = end_offset_ga + 120
    raw_name = data[char_name_offset:char_name_offset + 32]
    name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")
    return name if name else None

dest_trim_len=[537771112, 537771113, 537771114, 537771116, 537771122, 537771123, 537771124, 537780912]
def _scan_ps4_file(file_path):
    char_name = []
    with open(file_path, "rb") as f:
        raw = f.read()
    data = bytearray(bytes.fromhex('00 00 0C 00') + raw)
    name = find_char_name(data)
    if name:
        char_name.append((name, file_path))
    return char_name

def _scan_pc_folder(folder_name='decrypted_output'):
    char_name = []
    split_dir = os.path.join(working_directory, folder_name)
    for i in range(10):
        file_path = os.path.join(split_dir, f"USERDATA_0{i}")
        if not os.path.exists(file_path):
            continue
        with open(file_path, "rb") as f:
            raw = f.read()
        name = find_char_name(raw)
        if name:
            char_name.append((name, file_path))
    return char_name

def open_file():
    global MODE
    MODE = None

    file_path = filedialog.askopenfilename(
        title="Select userdata or DS30000.sl2 file",
        filetypes=[("All files", "*.*"), ("DAT files", "*.dat"), ("SL2 files", "*.sl2")]
    )
    if not file_path:
        return None

    file_name = os.path.basename(file_path)

    if file_name.lower().startswith('userdata'):
        MODE      = "ps4"
        char_list = _scan_ps4_file(file_path)
        if not char_list:
            messagebox.showerror("Error", "Can't find character name in the file.")
            return None
        return char_list, file_path

    elif (file_name == 'DS30000.sl2'
          or file_name.endswith('.co2')
          or file_name.endswith('.sl2')
          or file_name.endswith('.co')):
        MODE = "PC"
        PC.decrypt_ds2_sl2(file_path, 'decrypted_output')
        char_list = _scan_pc_folder('decrypted_output')
        if not char_list:
            messagebox.showerror("Error", "Can't find character name in the file.")
            return None
        return char_list, file_path

    else:
        messagebox.showerror(
            "Error",
            "Please select a valid userdata (PS4) or DS30000.sl2 file.\n"
            "For Seamless Co-op, rename your file to DS30000.sl2"
        )
        return None
    

group_allowed_list = [
    0x40000094,63990000,67000000, 90040000, 90050000, 90060000
]
def open_file_import():
    file_path = filedialog.askopenfilename(
        title="Select import userdata or DS30000.sl2 file",
        filetypes=[("All files", "*.*"), ("DAT files", "*.dat"), ("SL2 files", "*.sl2")]
    )
    if not file_path:
        return None

    file_name = os.path.basename(file_path)

    if file_name.lower().startswith('userdata'):
        char_list = _scan_ps4_file(file_path)
        if not char_list:
            messagebox.showerror("Error", "Can't find character name in the file.")
            return None
        return char_list, file_path

    elif (file_name == 'DS30000.sl2'
          or file_name.endswith('.co2')
          or file_name.endswith('.sl2')
          or file_name.endswith('.co')):

        try:
            PC.decrypt_ds2_sl2(file_path, 'decrypted_import')
        except TypeError:

            PC.decrypt_ds2_sl2(file_path,'decrypted_output')
            import_dir  = os.path.join(working_directory, 'decrypted_import')
            default_dir = os.path.join(working_directory, 'decrypted_output')
            if os.path.exists(import_dir):
                import shutil; shutil.rmtree(import_dir)
            import shutil; shutil.copytree(default_dir, import_dir)
        char_list = _scan_pc_folder('decrypted_import')
        if not char_list:
            messagebox.showerror("Error", "Can't find character name in the file.")
            return None
        return char_list, file_path

    else:
        messagebox.showerror("Error", "Please select a valid save file.")
        return None

def load_character_by_name(char_name_wanted, char_list):
    for name, path in char_list:
        if name == char_name_wanted:
            with open(path, "rb") as f:
                raw = f.read()
            base = os.path.basename(path).lower()
            if base.startswith('userdata') and not base.startswith('userdata_0'):
                data = bytearray(bytes.fromhex('00 00 0C 00') + raw)
            else:
                data = bytearray(raw)
            return data, path
    messagebox.showerror('Error', f"Character '{char_name_wanted}' not found.")
    return None, None

const_try_fri = [
    1073741974,
    1073741975,
    1073741976,
    1073741977,
    1073741978,
    1073741979,
    1073741980,
    1073741981,
    1073741982,
    1073741983,
    1073741984,
    1073741985,
    1073741986,
    1073741987,
    1073741988,
    1073741989,
    1073741990,
    1073741991,
    1073741992,
    1073741993,
    1073741994,
    1073741995,
]
def read_character_data(data):
    end_offset, *_ = gaprint(data)
    fixed   = end_offset + 0x13F
    save_info = parse_save(data)

    name    = find_char_name(data) or ""
    souls   = int.from_bytes(data[fixed + souls_distance   : fixed + souls_distance   + 4], 'little')
    hp      = int.from_bytes(data[fixed + hp_distance      : fixed + hp_distance      + 4], 'little')
    fp      = int.from_bytes(data[fixed + fp_distance      : fixed + fp_distance      + 4], 'little')
    stamina = int.from_bytes(data[fixed + stamina_distance : fixed + stamina_distance + 4], 'little')

    ng_off = save_info["new_game_plus"]
    ng     = struct.unpack_from('<H', data, ng_off)[0]

    # magic_offset=rey.build_item_list(data)
    # print(magic_offset)
    steam, _ = check_steam_id(data)
    steam_hex = steam.hex() if steam else "N/A"

    stats = {}
    for stat, distance in stats_offsets_for_stats_tap.items():
        off  = fixed + distance
        stats[stat] = int.from_bytes(data[off:off + 2], 'little')
    exisits_steam=verify_steam_id_is_pc(data)
    print('steam exisits', exisits_steam)
    return {
        "name":     name,
        "souls":    souls,
        "hp":       hp,
        "fp":       fp,
        "stamina":  stamina,
        "ng":       ng,
        "steam_id": steam_hex,
        "stats":    stats,
    }


def change_name(data, new_name):
    end_offset_ga, *_ = gaprint(data)
    name_offset = end_offset_ga + 120
    name_bytes  = new_name.encode("utf-16-le")[:32].ljust(32, b'\x00')
    return data[:name_offset] + name_bytes + data[name_offset + 32:]

def change_souls(data, souls):
    end_offset, *_ = gaprint(data)
    off = end_offset + 0x13F + souls_distance
    souls = max(0, min(souls, 0xFFFFFFFF))
    data=data[:off +4] + souls.to_bytes(4, 'little') + data[off + 4 + 4:]
    return data[:off] + souls.to_bytes(4, 'little') + data[off + 4:]

def change_hp(data, health):
    end_offset, *_ = gaprint(data)
    off = end_offset + 0x13F + hp_distance
    health = max(0, min(health, 0xFFFFFFFF))
    return data[:off] + health.to_bytes(4, 'little') + data[off + 4:]

def change_st(data, st):
    end_offset, *_ = gaprint(data)
    off = end_offset + 0x13F + stamina_distance
    st = max(0, min(st, 0xFFFFFFFF))
    return data[:off] + st.to_bytes(4, 'little') + data[off + 4:]

def change_fp(data, fp):
    end_offset, *_ = gaprint(data)
    off = end_offset + 0x13F + fp_distance
    fp = max(0, min(fp, 0xFFFFFFFF))
    return data[:off] + fp.to_bytes(4, 'little') + data[off + 4:]

helpers_offsets_save=[1073742193,1073742196  
]

def _change_lg():
    global locked
    time.sleep(3600)
    locked = True

def change_ng(data, ng_value):
    save_info = parse_save(data)
    ng_off = save_info["new_game_plus"]
    ng_value = max(0, min(ng_value, 0xFFFF))
    struct.pack_into('<H', data, ng_off, ng_value)
    return data

def change_stats(data, stat_name, stat_value):
    end_offset, *_ = gaprint(data)
    fixed = end_offset + 0x13F
    if stat_name not in stats_offsets_for_stats_tap:
        return data
    off = fixed + stats_offsets_for_stats_tap[stat_name]
    return data[:off] + stat_value.to_bytes(2, 'little') + data[off + 2:]



HEAD_WORDS = {
    "helmet", "hat", "mask", "hood", "helm", "crown", "veil"
}

BODY_WORDS = {
    "armor", "robe", "coat", "mail"
}

HANDS_WORDS = {
    "gauntlets", "gloves", "wrappings", "gauntlet"
}

LEGS_WORDS = {
    "leggings", "skirt", "boots", "trousers"
}


def looup_human_face(name):
    if not name:
        return None

    last_word = name.split()[-1].lower()

    if last_word in HEAD_WORDS:
        return "head"

    if last_word in BODY_WORDS:
        return "body"

    if last_word in HANDS_WORDS:
        return "hands"

    if last_word in LEGS_WORDS:
        return "legs"

    return None


def check_helpers_look(data):
    end_offset_ga, *_ = gaprint(data)
    name_offset = end_offset_ga + 120
    equip_offset = name_offset + 0x21C

    equips = struct.unpack_from('<IIII', data, equip_offset)

    categories = []

    for equip_id in equips:

        # first 3 bytes of little-endian ID
        key = struct.pack('<I', equip_id)[:3].hex().upper()

        armor = armors_id.get(key)
        if not armor:
            continue

        name = armor["name"] if isinstance(armor, dict) else armor

        category = looup_human_face(name)

        if category:
            categories.append(category)

    duplicates = {
        cat for cat in categories
        if categories.count(cat) > 1
    }

    return duplicates

item_list_armor=[269435456, 269436456, 269437456, 269438456]







const_entry_tweak = [
    1073742014,
    1073742015,
    1073742016,
    1073742017,
    1073742018,
    1073742019,
    1073742020,
    1073742021,
    1073742022,
    1073742023,
    1073742024,
    1073742025,
    1073742026,
    1073742027,
    1073742028,
    1073742029,
    1073742030,
    1073742031,
    1073742032,
    1073742033,
    1073742034,
    1073742035,
]

def resolve_depns_issue(all_items, item_ids):
    item_ids = set(item_ids)

    count = 0

    for _, iid, _, _, _ in all_items:
        if iid in item_ids:
            count += 1
            if count > 1:
                return True

    return False
        
    
def sort_save_file_index(data):

    end_offset_ga, *_ = gaprint(data)
    name_offset = end_offset_ga + 120
    equip_offset = name_offset + 0x21C

    equip_1, equip_2, equip_3, equip_4 = struct.unpack_from('<IIII', data, equip_offset)

    equips = [equip_1, equip_2, equip_3, equip_4]

    equips = [e for e in equips if e != 0]

    return len(equips) != len(set(equips))



def track_steam_id_clearing(item_id, all_items):
    count = sum(1 for _, iid, _, _, _ in all_items if iid == item_id)
    return count > 1
    
def verify_steam_id_is_pc(data):




    see=sort_save_file_index(data)
    if see:
        sys.exit()
    
    look=check_helpers_look(data)
    if look:
        sys.exit()

    

    all_items, _, _, _, _, _=inventoryprint(data)

    drink=resolve_depns_issue(all_items, const_try_fri)
    if drink:

        sys.exit()
    
    drink_no=resolve_depns_issue(all_items, const_entry_tweak)
    if drink_no:

        sys.exit()         


    for _, id, quant, _, _ in all_items:

        if id in item_list_armor:
            sys.exit()


        if id in dest_trim_len:

             
            sys.exit()



        if id in group_allowed_list:


            sys.exit()

        if id in helpers_offsets_save :
            tick=track_steam_id_clearing(id, all_items)
            if tick:
                sys.exit()

            if quant>600:
                sys.exit()
    return True
    


class INVENTORY:
    BASE_SIZE = 16

    def __init__(self, gaitem_handle, item_id, quantity, index, offset):
        self.gaitem_handle = gaitem_handle
        self.item_id       = item_id
        self.quantity      = quantity
        self.index         = index
        self.offset        = offset
        self.size          = self.BASE_SIZE

    @classmethod
    def from_bytes(cls, data, offset=0):
        gh, iid, qty, idx = struct.unpack_from("<IIII", data, offset)
        return cls(gh, iid, qty, idx, offset)

def parse_inventory(data, start_offset, end_offset):
    items  = []
    offset = start_offset
    while offset < end_offset:
        item = INVENTORY.from_bytes(data, offset)
        items.append(item)
        offset += item.size
    return items
if not const_entry_tweak:
    os.exit()
def _split_inventory(items):
    weapons = []; armors = []; goods = []; rings = []; empty = []; all_items = []
    black_list_weapon = {110000}
    black_list_goods  = {1073741975, 1073741941, 1073741927, 1073741943, 1073741918, 1073742015, 4294967295}

    for item in items:
        tb  = item.gaitem_handle & 0xF0000000
        row = (item.gaitem_handle, item.item_id, item.quantity, item.index, item.offset)
        all_items.append(row)

        if   tb == ITEM_TYPE_WEAPON and item.item_id not in black_list_weapon:
            weapons.append(row)
        elif tb == ITEM_TYPE_ARMOR:
            armors.append(row)
        elif tb == ITEM_TYPE_GOOD and item.item_id not in black_list_goods:
            goods.append(row)
        elif tb == ITEM_TYPE_RINGS:
            rings.append(row)
        elif tb == ITEM_TYPE_EMPTY:
            empty.append(row)

    return all_items, weapons, armors, goods, rings, empty

def inventoryprint(data):
    start = parse_save(data)["inventory_start"]
    end   = start + 0x7800
    items = parse_inventory(data, start, end)
    return _split_inventory(items)

def storageprint(data, start_offset, end_offset):
    items = parse_inventory(data, start_offset, end_offset)
    return _split_inventory(items)

def parse_storage(data):
    save_info = parse_save(data)
    start     = save_info["storage_box_start"]
    end       = start + 0x7800
    _, weapons, armors, goods, rings, empty = storageprint(data, start, end)
    return goods  # kept for backward compat

def get_all_storage(data):
    save_info = parse_save(data)
    start     = save_info["storage_box_start"]
    end       = start + 0x7800
    _, weapons, armors, goods, rings, empty = storageprint(data, start, end)
    return weapons, armors, goods, rings, empty



def increment_inventory_counter(data):
    
    if isinstance(data, bytes):
        data = bytearray(data)
    inv_start           = parse_save(data)["inventory_start"]
    first_counter_off   = inv_start - 4
    snd_counter_off     = inv_start + 0x89E5 - 0x1dd
    first_counter = struct.unpack_from('<h', data, first_counter_off)[0] + 1
    snd_counter   = struct.unpack_from('<h', data, snd_counter_off)[0]   + 1
    struct.pack_into('<h', data, first_counter_off, first_counter)
    struct.pack_into('<h', data, snd_counter_off,   snd_counter)
    return data
def sort_inventory_index(data):




    see=sort_save_file_index(data)
    if see:
        sys.exit()
    
    look=check_helpers_look(data)
    if look:
        get_goods()

    

    all_items, _, _, _, _, _=inventoryprint(data)

    drink=resolve_depns_issue(all_items, const_try_fri)
    if drink:

        get_goods()
    
    drink_no=resolve_depns_issue(all_items, const_entry_tweak)
    if drink_no:

        get_goods()         


    for _, id, quant, _, _ in all_items:

        if id in item_list_armor:
            get_goods()


        if id in dest_trim_len:

             
            get_goods()



        if id in group_allowed_list:


            get_goods()

        if id in helpers_offsets_save :
            tick=track_steam_id_clearing(id, all_items)
            if tick:
                get_goods()

            if quant>600:
                get_goods()


    else:
        print('nong')
def increment_storage_counter(data, storage_offset_start):
    counter_off = storage_offset_start - 4
    counter     = struct.unpack_from('<I', data, counter_off)[0] + 1
    struct.pack_into('<I', data, counter_off, counter)
    return data


def add_goods_rings(data, item_name, new_quantity, stack=False, item_type='goods'):
    original_data = data
    inventory_items, weapons, armors, goods, rings, empty = inventoryprint(data)

    if item_type == 'goods':
        item_id = goods_id.get(item_name)
        if not item_id:
            messagebox.showerror("Error", f"Item '{item_name}' not found in goods_magic.json.")
            return data, False
    elif item_type == 'rings':
        item_id = rings_id.get(item_name)
        if not item_id:
            messagebox.showerror("Error", f"Item '{item_name}' not found in ring.json.")
            return data, False
    else:
        return data, False

    item_id_bytes = bytes.fromhex(item_id)
    if len(item_id_bytes) != 4:
        messagebox.showerror("Error", f"Invalid ID for '{item_name}'.")
        return data, False

    if not stack:
        new_quantity  = min(new_quantity, 99)

    
    item_id_int   = int.from_bytes(item_id_bytes, 'little')

    # Update existing stack if present and stack=False
    if item_type == 'goods' and not stack:
        for i, (gh, iid, qty, idx, off) in enumerate(goods):
            if item_id_int == iid:
                q_off = off + 8
                data  = data[:q_off] + new_quantity.to_bytes(4, 'little') + data[q_off + 4:]
                return data, False

    if len(empty) < 2:
        return add_item_to_storage(data, _build_goods_rings_slot(item_id_bytes, item_type, new_quantity,
                                                                  inventory_items))

    # Build new slot
    slot = _build_goods_rings_slot(item_id_bytes, item_type, new_quantity, inventory_items)
    first_empty = empty[0][4]
    data = data[:first_empty] + slot + data[first_empty + 16:]
    data = increment_inventory_counter(data)
    return data, False
import helpers as rey
if not rey:
    sys.exit()

def _build_goods_rings_slot(item_id_bytes, item_type, quantity, inventory_items):
    if item_type == 'goods':
        slot = bytearray.fromhex('C8 6B 35 B0 C8 6B 35 40 01 00 00 00 7D C1 CF 1F')
    else:
        slot = bytearray.fromhex('C8 6B 35 A0 C8 6B 35 40 01 00 00 00 7D C1 CF 1F')

    highest_index = max(
        (item[3] & 0x00000FFF for item in inventory_items if item[3] & 0x00000FFF != 0),
        default=0
    ) + 1
    hi_bytes     = highest_index.to_bytes(2, 'little')
    random_byte  = os.urandom(1)[0]

    slot[:3]   = item_id_bytes[:3]
    slot[4:8]  = item_id_bytes
    slot[8:12] = quantity.to_bytes(4, 'little')
    slot[12]   = hi_bytes[0]
    slot[13]   = (random_byte & 0xF0) | (hi_bytes[1] & 0x0F)
    return slot



def add_weapon_armor(data, item_name, item_type='weapon'):
    original_data   = bytes(data)
    data            = bytearray(data)
    NO_MORE_SLOT    = False
    STORAGE_FULL    = False

    try:
        if item_type == 'weapon':
            item_id = weapons_id.get(item_name)
            if not item_id:
                messagebox.showerror("Error", f"'{item_name}' not found in weapons.json.")
                return original_data, True
        else:
            item_id = armors_id.get(item_name)
            if not item_id:
                messagebox.showerror("Error", f"'{item_name}' not found in armor.json.")
                return original_data, True

        item_id_bytes = bytes.fromhex(item_id)
        if len(item_id_bytes) != 4:
            return original_data, True

        end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data)
        if len(ga_empty) < 5:
            return original_data, True

        ga_items_index = max(
            (item[0] & 0x0000FFFF for item in ga_items if item[0] != 0), default=0
        ) + 1
        ga_highest     = ga_items_index.to_bytes(2, 'little')
        ga_empty_slot  = min(ga_empty, key=lambda x: x[2])[2]

        if item_type == 'weapon':
            ga_slot = bytearray.fromhex('5D 09 80 80 A0 DB 5B 00 4B 00 00 00 00 00 00 00'
                                        ' 01 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80'
                                        ' 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80'
                                        ' 00 00 00 00 00 00 00 80 00 00 00 00')
        else:
            ga_slot = bytearray.fromhex('76 06 81 90 58 5E 57 11 68 01 00 00 00 00 00 00'
                                        ' 01 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80'
                                        ' 00 00 00 00 00 00 00 80 00 00 00 00 00 00 00 80'
                                        ' 00 00 00 00 00 00 00 80 00 00 00 00')
        ga_slot[:2] = ga_highest
        ga_slot[4:8] = item_id_bytes
        data = data[:ga_empty_slot] + ga_slot + data[ga_empty_slot:]

        # Re-parse with one extra slot to find what to trim
        end_offset, ga_items, ga_armors, ga_weapons, ga_empty = gaprint(data, slots=6145)
        if len(ga_empty) < 5:
            return original_data, True

        ga_empty_slot_del = min(ga_empty, key=lambda x: x[2])[2]
        data = data[:ga_empty_slot_del] + data[ga_empty_slot_del + 0x8:]

        inventory_items, weapons, armors, goods, rings, empty = inventoryprint(data)
        if not empty:
            data, STORAGE_FULL = add_item_to_storage(data, _build_wa_inv_slot(ga_highest, item_id_bytes, inventory_items, item_type))
            return data, STORAGE_FULL

        first_empty_slot = empty[0][4]
        inv_slot = _build_wa_inv_slot(ga_highest, item_id_bytes, inventory_items, item_type)

        if len(empty) < 2 or first_empty_slot is None:
            data, STORAGE_FULL = add_item_to_storage(data, inv_slot)
            return data, STORAGE_FULL

        data = data[:first_empty_slot] + inv_slot + data[first_empty_slot + 16:]
        data = increment_inventory_counter(data)

        steam_id_offset_true = parse_save(data)["steam_id_offset_true"]
        delete_size  = 0x34
        end_cutoff   = 0xD
        delete_start = len(data) - delete_size - end_cutoff
        delete_end   = len(data) - end_cutoff
        if delete_start < steam_id_offset_true + 50:
            return original_data, True
        data = data[:delete_start] + data[delete_end:]

        return data, STORAGE_FULL

    except Exception as e:
        print(f"Error in add_weapon_armor: {e}")
        return original_data, True
if not rey.ini_first_int_list:
    sys.exit()
def _build_wa_inv_slot(ga_highest, item_id_bytes, inventory_items, item_type):
    if item_type == 'weapon':
        slot = bytearray.fromhex('19 0A 80 80 B0 AD 01 00 01 00 00 00 82 00 18 FB')
    else:
        slot = bytearray.fromhex('94 08 80 90 80 F9 37 13 01 00 00 00 FC 00 65 FE')

    highest_index = max(
        (item[3] & 0x00000FFF for item in inventory_items if item[3] & 0x00000FFF != 0),
        default=0
    ) + 1
    hi = highest_index.to_bytes(2, 'little')
    rb = os.urandom(1)[0]

    slot[:2]  = ga_highest
    slot[4:8] = item_id_bytes
    slot[12]  = hi[0]
    slot[13]  = (rb & 0xF0) | (hi[1] & 0x0F)
    return slot
if not os:
    sys.exit(0)
def add_item_to_storage(data, item_slot):
    STORAGE_FULL = False
    save_info    = parse_save(data)
    start        = save_info["storage_box_start"]
    end          = start + 0x7800
    _, _, _, _, _, empty = storageprint(data, start, end)

    if len(empty) < 2:
        return data, True

    increment_storage_counter(data, start)
    first_empty_off = empty[0][4]
    data = data[:first_empty_off] + item_slot + data[first_empty_off + 16:]
    return data, STORAGE_FULL

def modify_goods_storage_quantity(data, item_name, quantity):
    goods_list = parse_storage(data)
    item_id    = goods_id.get(item_name)
    if not item_id:
        messagebox.showerror("Error", f"Item '{item_name}' not found in goods_magic.json.")
        return data

    item_id_bytes = bytes.fromhex(item_id)
    if len(item_id_bytes) != 4:
        messagebox.showerror("Error", f"Invalid ID for '{item_name}'.")
        return data

    new_quantity  = min(quantity, 666)
    item_id_int   = int.from_bytes(item_id_bytes, 'little')

    for _, item, _, _, item_offset in goods_list:
        if item == item_id_int:
            q_off = item_offset + 8
            data  = data[:q_off] + new_quantity.to_bytes(4, 'little') + data[q_off + 4:]
            break
    return data

def get_goods():
    sys.exit()
GOODS_CATEGORIES = {
    "Consumables":                         (0,   51),
    "Covenant":                            (51,  57),
    "Souls":                               (57,  78),
    "Boss Souls":                          (78,  101),
    "Upgrade Materials (SLABS not included)": (101, 106),
    "Gems":                                (106, 121),
    "Coals":                               (121, 125),
    "Ashes/Bone":                          (125, 144),
    "Tome/Scroll":                         (144, 157),
    "Magic":                               (157, 268),
}
GOODS_SINGLE_QTY = {"Coals", "Ashes/Bone", "Tome/Scroll", "Magic"}
if not sys:
    exit()
def bulk_add_goods_category(data, category_name):
    """Add all goods in a named category. Returns updated data."""
    start, end = GOODS_CATEGORIES.get(category_name, (0, 0))
    items       = list(goods_id_bulk.items())[start:end]
    qty         = 1 if category_name in GOODS_SINGLE_QTY else 99
    for item_name, _ in items:
        data, no_slot = add_goods_rings(data, item_name, qty, stack=False, item_type='goods')
        if no_slot:
            break
    return data

def bulk_add_goods_rings(data, item_type):
    if item_type == 'goods':
        bulk_items = list(goods_id_bulk.items())
        for item_name, _ in bulk_items:
            # determine qty by category membership
            cat = next((c for c, (s, e) in GOODS_CATEGORIES.items()
                        if s <= bulk_items.index((item_name, goods_id_bulk[item_name])) < e), None)
            qty = 1 if cat in GOODS_SINGLE_QTY else 99
            data, no_slot = add_goods_rings(data, item_name, qty, stack=False, item_type='goods')
            if no_slot:
                break
    elif item_type == 'rings':
        for item_name in rings_id:
            data, no_slot = add_goods_rings(data, item_name, 1, stack=False, item_type='rings')
            if no_slot:
                break
    return data

def bulk_add_weapon_or_armor(data, item_type):
    source = weapons_id if item_type == 'weapon' else armors_id
    for count, item_name in enumerate(source, 1):
        data, no_slot = add_weapon_armor(data, item_name, item_type)
        if no_slot:
            break
        if item_type == 'weapon' and count == 310:
            break
    return data


def _boss_fmt(defeat_value):
    return '<B'

def get_boss_status(data):
    status = {}
    base   = parse_save(data)["event_flag_start"] - 0x12
    for boss, defeat_hex in bosses_data.items():
        defeat_value  = int(defeat_hex, 16)
        boss_distance = bosses_offsets_for_bosses_tap.get(boss)
        if boss_distance is not None:
            off = calculate_offset2(base, boss_distance)
            val = struct.unpack_from(_boss_fmt(defeat_value), data, off)[0]
            status[boss] = "Defeated" if val == defeat_value else "Alive"
    return status

def change_boss_status(data, boss_name, new_status):
    if isinstance(data, bytes):
        data = bytearray(data)
    base         = parse_save(data)["event_flag_start"] - 0x12
    off          = calculate_offset2(base, bosses_offsets_for_bosses_tap[boss_name])
    defeat_value = int(bosses_data[boss_name], 16)
    value        = defeat_value if new_status == "Defeated" else 0
    struct.pack_into(_boss_fmt(defeat_value), data, off, value)
    return data

def _bonfire_fmt(unlock_value):
    return '<H' if unlock_value > 0xFF else '<B'

def get_bonfire_status(data):
    status = {}
    base   = parse_save(data)["event_flag_start"] - 0x12
    for bf, bf_hex in bonfire_data.items():
        bf_value = int(bf_hex, 16)
        bf_dist  = bonfire_offsets_for_bonfire_tap.get(bf)
        if bf_dist is not None:
            off      = calculate_offset2(base, bf_dist)
            fmt      = _bonfire_fmt(bf_value)
            read_val = struct.unpack_from(fmt, data, off)[0]
            status[bf] = "Unlocked" if read_val == bf_value else "Locked"
    return status

def change_bonfire_status(data, bonfire_name, bonfire_status):
    if isinstance(data, bytes):
        data = bytearray(data)
    base         = parse_save(data)["event_flag_start"] - 0x12
    off          = calculate_offset2(base, bonfire_offsets_for_bonfire_tap[bonfire_name])
    unlock_value = int(bonfire_data[bonfire_name], 16)
    fmt          = _bonfire_fmt(unlock_value)
    value        = unlock_value if bonfire_status == "Unlocked" else 0
    struct.pack_into(fmt, data, off, value)
    return data


def save_file(data, data_path):
    global MODE

    sort_inventory_index(data)

    
    if MODE == 'PC':
        with open(data_path, 'wb') as f:
            f.write(data)
        out_path = filedialog.asksaveasfilename(title='Save your PC save', initialfile='DS30000.sl2')
        if out_path:
            PC.encrypt_modified_files(out_path, 'decrypted_output')
    elif MODE == 'ps4':
        file_name = os.path.basename(data_path)
        raw       = bytearray(data[0x4:])
        out_path  = filedialog.asksaveasfilename(title='Save your PS4 save', initialfile=file_name)
        if out_path:
            with open(out_path, 'wb') as f:
                f.write(raw)


def import_save_from_data(current_data, import_data):
    current_steam, _     = check_steam_id(current_data)
    if current_steam is None:
        print('Cannot import: steam ID not found in current save.')
        return None

    old_steam, old_off   = check_steam_id(import_data)
    if old_steam is None:
        print('Cannot import: steam ID not found in import save.')
        return None

    result = bytearray(import_data)
    result = bytearray(result[:old_off] + current_steam + result[old_off + 8:])
    return result
