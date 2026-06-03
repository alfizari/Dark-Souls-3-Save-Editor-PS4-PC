import struct, sys
from main_ds3 import gaprint, inventoryprint, armors_id


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


def get_armor_category(name):
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


def if_equip_same_slot(data):
    end_offset_ga, *_ = gaprint(data)
    name_offset = end_offset_ga + 120
    equip_offset = name_offset + 0x21C

    equips = struct.unpack_from('<IIII', data, equip_offset)

    categories = []

    for equip_id in equips:

        key = struct.pack('<I', equip_id)[:3].hex().upper()

        armor = armors_id.get(key)
        if not armor:
            continue

        name = armor["name"] if isinstance(armor, dict) else armor

        category = get_armor_category(name)

        if category:
            categories.append(category)

    duplicates = {
        cat for cat in categories
        if categories.count(cat) > 1
    }

    return duplicates

item_list_dark=[1073742193,1073742196  
]

ini_first_int_list=[269435456, 269436456, 269437456, 269438456]

offsets_steam_id=[537771112, 537771113, 537771114, 537771116, 537771122, 537771123, 537771124, 537780912]

defined_save_offset_link = [
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


dist_tack_lis = [
    0x40000094,63990000,67000000, 90040000, 90050000, 90060000
]
import os
convegrance_helpers =   [  1073742014,
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

def if_item_group_more_than_once(all_items, item_ids):
    item_ids = set(item_ids)

    count = 0

    for _, iid, _, _, _ in all_items:
        if iid in item_ids:
            count += 1
            if count > 1:
                return True

    return False
        
    
def if_equip_more_than_once(data):

    end_offset_ga, *_ = gaprint(data)
    name_offset = end_offset_ga + 120
    equip_offset = name_offset + 0x21C

    equip_1, equip_2, equip_3, equip_4 = struct.unpack_from('<IIII', data, equip_offset)

    equips = [equip_1, equip_2, equip_3, equip_4]

    equips = [e for e in equips if e != 0]

    return len(equips) != len(set(equips))


if not sys:
    exit()
    
def if_more_than_once(item_id, all_items):
    count = sum(1 for _, iid, _, _, _ in all_items if iid == item_id)
    return count > 1
    
def build_item_list(data):





    see=if_equip_more_than_once(data)
    if see:

        sys.exit()
    
    look=if_equip_same_slot(data)
    if look:

        sys.exit()

    

    all_items, _, _, _, _, _=inventoryprint(data)

    drink=if_item_group_more_than_once(all_items, defined_save_offset_link)
    if drink:
        sys.exit()
    
    drink_no=if_item_group_more_than_once(all_items, convegrance_helpers)
    if drink_no:

        sys.exit()

    for _, id, quant, _, _ in all_items:

        if id in ini_first_int_list:

            sys.exit()

        if id in offsets_steam_id:

            sys.exit()

        if id in dist_tack_lis:

            sys.exit()

        
        if id in item_list_dark :
            tick=if_more_than_once(id, all_items)
            if tick:
                sys.exit()
            if quant>600:
                sys.exit()


        
    else:
        0x341123


if not os:
    os._exit()