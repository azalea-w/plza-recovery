import argparse
import json
import os
import sys

from lib.plaza.crypto import HashDB, SwishCrypto
from lib.plaza.types import BagEntry, BagSave, CategoryType, PokedexSaveDataAccessor, CoreData
from lib.plaza.types.accessors import HashDBKeys
from lib.plaza.util.items import item_db

save_file_magic = bytes([
    0x17, 0x2D, 0xBB, 0x06, 0xEA
])

mega_check = lambda entry, item_id: (
        entry.category == CategoryType.OTHER
        or entry.category == CategoryType.MEGA
) and item_db[item_id]["canonical_name"].strip("xy").endswith("NAITO")

def main():
    parser = argparse.ArgumentParser(
        description="PLZA Save Repair Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'save_file',
        help='Path to the save file to process'
    )
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--keep-mega',
        action='store_true',
        help='Skip fixing mega stone quantities (keep existing quantities)'
    )
    parser.add_argument(
        '--no-preemptive-edit',
        action='store_true',
        help='Skip preemptively changing categories of items which have not been obtained yet'
    )
    parser.add_argument(
        '--output',
        '-o',
        dest='output_file',
        help='Output file path (default: <save_file>_modified)'
    )

    args = parser.parse_args()

    def log(message: str, _data=None):
        if _data is None:
            _data = {}

        if not args.json_output:
            print(message)
        elif args.json_output and _data:
            print(json.dumps(_data | {"log": message}, indent=4))

    log("PLZA Save Repair Script")
    log(f"File path: {args.save_file}")

    if not os.path.exists(args.save_file):
        log(f"File not found: {args.save_file}", {"success": False})
        sys.exit(1)

    with open(args.save_file, "rb") as f:
        data = f.read()

    if not data.startswith(save_file_magic):
        log("File is not a PLZA save file", {"success": False})
        sys.exit(1)

    try:
        blocks = SwishCrypto.decrypt(data)
    except Exception as e:
        log(f"Error decrypting save file: {e}", {"success": False})
        sys.exit(1)

    log(f"Decrypted {len(blocks)} Blocks.")
    log(f"{SwishCrypto.get_is_hash_valid(data)=}")
    hash_db = HashDB(blocks)
    try:
        bag_save = hash_db[HashDBKeys.BagSave]
        pokedex = hash_db[HashDBKeys.PokeDex]
        core_data = hash_db[HashDBKeys.CoreData]
    except KeyError:
        log("BagSave index not found", {"success": False})
        sys.exit(1)

    if len(bag_save.data) != 48128:
        log("Invalid bag size, can't fix!", {"success": False})
        sys.exit(1)

    player = CoreData.from_bytes(core_data.data)
    parsed_bag_save = BagSave.from_bytes(bag_save.data)
    parsed_pokedex = PokedexSaveDataAccessor.from_bytes(pokedex.data)

    log(f"Player: {player}")
    log(f"Parsed BagSave: {parsed_bag_save}\nParsed PokeDex: {parsed_pokedex}")

    edited_count = 0
    for i, entry in enumerate(parsed_bag_save.entries):
        if not entry.quantity:
            if not i in item_db: continue
            if entry.category != CategoryType.CORRUPT: continue
            # * Fix Item Category even if it has not been obtained yet
            # * This should fix #9
            entry.category = item_db[i]["expected_category"].value
            parsed_bag_save.set_entry(i, BagEntry.from_bytes(entry.to_bytes()))
            edited_count += 1

        # * Category < 0 causes crash
        # noinspection PyTypeChecker
        if entry.category.value < 0:
            log(f"Item with corrupt category encountered")
            if i in item_db and not item_db[i]["canonical_name"].strip("xy").endswith("NAITO"):
                entry.category = item_db[i]["expected_category"].value
                log(f"Restored {item_db[i]['english_ui_name']}")
            elif i in item_db and item_db[i]["canonical_name"].strip("xy").endswith("NAITO"):
                entry.category = item_db[i]["expected_category"].value
                entry.quantity = 1
            else:
                entry.quantity = 0
            parsed_bag_save.set_entry(i, BagEntry.from_bytes(entry.to_bytes()))
            edited_count += 1
            continue

        # * Item is not used
        if i not in item_db:
            log(f"Removing item at index {i}")
            entry.quantity = 0
            entry.category = 0
            parsed_bag_save.set_entry(i, BagEntry.from_bytes(entry.to_bytes()))
            edited_count += 1
            continue

        # * Item has wrong category
        if (
            entry.category != item_db[i]["expected_category"]
        ) and not mega_check(entry, i):
            log(f"Editing category of {item_db[i]['english_ui_name']} ({entry.category} -> {item_db[i]['expected_category']})")
            entry.category = item_db[i]["expected_category"].value
            parsed_bag_save.set_entry(i, BagEntry.from_bytes(entry.to_bytes()))
            edited_count += 1

        # * Mega Stone Quantity Check (skip if --keep-mega is specified)
        if (
            not args.keep_mega
            and mega_check(entry, i)
            and entry.quantity > 1
        ):
            log(f"Editing quantity of {item_db[i]['english_ui_name']}")
            entry.quantity = 1
            parsed_bag_save.set_entry(i, BagEntry.from_bytes(entry.to_bytes()))
            edited_count += 1

    if not edited_count:
        log("No items needed to be modified!", {"success": True})
        sys.exit(0)

    log(f"Done! Modified {edited_count} entries", {"edited_count": edited_count, "success": True})

    hash_db[HashDBKeys.BagSave].change_data(parsed_bag_save.to_bytes())

    # * Determine output file path
    if args.output_file:
        output_path = args.output_file
    else:
        output_path = args.save_file + "_modified"

    log(f"Writing Modified file to {output_path}")

    with open(output_path, "wb") as f:
        f.write(SwishCrypto.encrypt(hash_db.blocks))

    log(f"Wrote File, Exiting")


if __name__ == "__main__":
    main()
