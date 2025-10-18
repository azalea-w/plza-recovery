import argparse
import os
import sys
import shutil

from lib.plaza.crypto import SwishCrypto, HashDB
from lib.plaza.types import PokedexSaveDataAccessor, PokedexCoreData
from lib.plaza.types.accessors import HashDBKeys

save_file_magic = bytes([
    0x17, 0x2D, 0xBB, 0x06, 0xEA
])

pokedex_ids_to_complete = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18, 23, 24, 25, 26, 35, 36, 63, 64, 65, 
    66, 67, 68, 69, 70, 71, 79, 80, 92, 93, 94, 95, 115, 120, 121, 123, 127, 129, 130, 133, 
    134, 135, 136, 142, 147, 148, 149, 150, 152, 153, 154, 158, 159, 160, 167, 168, 172, 
    173, 179, 180, 181, 196, 197, 199, 208, 212, 214, 225, 227, 228, 229, 246, 247, 248, 
    280, 281, 282, 302, 303, 304, 305, 306, 307, 308, 309, 310, 315, 318, 319, 322, 323, 
    333, 334, 353, 354, 359, 361, 362, 371, 372, 373, 374, 375, 376, 406, 407, 427, 428, 
    443, 444, 445, 447, 448, 449, 450, 459, 460, 470, 471, 475, 478, 498, 499, 500, 504, 
    505, 511, 512, 513, 514, 515, 516, 529, 530, 531, 543, 544, 545, 551, 552, 553, 559, 
    560, 568, 569, 582, 583, 584, 587, 602, 603, 604, 607, 608, 609, 618, 650, 651, 652, 
    653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 
    670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 
    687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 
    704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 
    721, 780, 870
]

new_pokedex_entries = [
    {
        "id": pkmn_id, 
        "is_captured": True, 
        "is_battled": True, 
        "is_shiny": True, 
        "capture_count": 0, 
        "defeat_count": 0
    } 
    for pkmn_id in pokedex_ids_to_complete
]

def main():
    parser = argparse.ArgumentParser(description="PLZA Complete Pokedex Script")
    parser.add_argument(
        'save_file',
        help='Path to the save file to modify'
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.save_file) 
    input_dir = os.path.dirname(input_path)
    input_filename = os.path.basename(input_path)
    
    output_path = os.path.join(input_dir, "main") 
    backup_path = os.path.join(input_dir, input_filename + "_old") 

    if not os.path.exists(input_path):
        sys.exit(1)

    try:
        if os.path.exists(backup_path):
             os.remove(backup_path) 
        shutil.move(input_path, backup_path)
    except Exception:
        sys.exit(1)

    try:
        with open(backup_path, "rb") as f:
            data = f.read()
    except Exception:
         shutil.move(backup_path, input_path) 
         sys.exit(1)


    if not data.startswith(save_file_magic):
        shutil.move(backup_path, input_path) 
        sys.exit(1)

    try:
        blocks = SwishCrypto.decrypt(data)
        hash_db = HashDB(blocks)
    except Exception:
        shutil.move(backup_path, input_path) 
        sys.exit(1)

    try:
        dex_block = hash_db[HashDBKeys.PokeDex]
        existing_dex_accessor = PokedexSaveDataAccessor.from_bytes(dex_block.raw)

        for entry_data in new_pokedex_entries:
            dev_no = int(entry_data["id"])
            if existing_dex_accessor.is_pokedex_data_out_of_range(dev_no):
                continue

            core_data = existing_dex_accessor.get_pokedex_data(dev_no)
            
            core_data.set_captured(0, bool(entry_data["is_captured"]))
            core_data.set_battled(0, bool(entry_data["is_battled"]))
            core_data.set_shiny(0, bool(entry_data["is_shiny"]))

            existing_dex_accessor.set_pokedex_data(dev_no, core_data)

        dex_block.change_data(existing_dex_accessor.to_bytes())

    except (KeyError, Exception):
        shutil.move(backup_path, input_path) 
        sys.exit(1)

    try:
        encrypted_data = SwishCrypto.encrypt(hash_db.blocks)
    except Exception:
        shutil.move(backup_path, input_path) 
        sys.exit(1)

    try:
        with open(output_path, "wb") as f:
            f.write(encrypted_data)
    except Exception:
        shutil.move(backup_path, input_path) 
        sys.exit(1)

if __name__ == "__main__":
    main()