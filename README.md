# PLZA Save Recovery Tool
<sub>This project is not associated with TPC (The Pokémon Company), GameFreak, Nintendo nor any other entity.</sub>

---

## What's this?
This is a tool you can use to repair corrupted save files for Pokémon Legends Z-A written in Python.
Currently, it only handles bag corruption, however I plan on adding different kinds of recovery methods for
other inconsistencies.

## Dependencies
- Python 3.13 (other versions of Python 3 should work too)

## How to use

1. Dump your save file using JKSV or similar
2. Copy your save file to your PC
3. Download latest release ZIP from the [Releases](https://github.com/azalea-w/plza-recovery/releases) Section
4. Open your shell (powershell or cmd for windows)
5. Run the Script like `python <path/to/main.py> <path/to/save/main>`!

It will output a new file with `_modified` appended to the filename, just restore that save using JKSV or similar and you should be good to go! 

## Thanks to:
- The maintainers of [PKHeX](https://github.com/kwsch/PKHeX/) for implementing SwishCrypto

- GameFreak for creating the game
