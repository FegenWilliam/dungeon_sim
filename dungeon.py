import random
import time
import os

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

FLOOR_ENEMIES = {
    1: ["Slime", "Goblin", "Rat"],
    2: ["Orc", "Skeleton", "Dark Elf"],
    3: ["Troll", "Vampire", "Wraith"],
    4: ["Dragon Whelp", "Demon Scout", "Stone Golem"],
    5: ["Elder Demon", "Lich", "Titan"],
}

FLOOR_BOSSES = {
    1: "Goblin King",
    2: "Bone Colossus",
    3: "Shadow Drake",
    4: "Infernal Warlord",
    5: "The Void Ancient",
}

# Base stats scaled by floor; bosses get a multiplier
ENEMY_BASE = {
    "hp":    [0, 20, 40, 70, 110, 160],   # indexed by floor
    "atk":   [0,  5, 10, 16,  23,  32],
    "def":   [0,  1,  3,  6,  10,  15],
    "xp":    [0, 15, 30, 55,  90, 140],
    "gold":  [0,  8, 18, 32,  52,  80],
}
BOSS_MULT = {"hp": 3.0, "atk": 1.6, "def": 1.5, "xp": 4.0, "gold": 5.0}

ENEMIES_PER_FLOOR = 3   # regular enemies before the boss


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class Player:
    def __init__(self, name: str):
        self.name   = name
        self.level  = 1
        self.max_hp = 80
        self.hp     = 80
        self.atk    = 12
        self.def_   = 4
        self.xp     = 0
        self.xp_next = 50
        self.gold   = 0
        self.floor  = 1
        self.kills  = 0     # enemies defeated on current floor
        self.boss_slain = False

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.def_)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self._level_up()

    def _level_up(self):
        self.level   += 1
        self.max_hp  += 15
        self.hp      = min(self.hp + 15, self.max_hp)
        self.atk     += 3
        self.def_    += 1
        self.xp_next  = int(self.xp_next * 1.5)
        print(f"\n  *** LEVEL UP! You are now level {self.level}! ***")
        print(f"      HP +15 | ATK +3 | DEF +1")

    def stats_str(self) -> str:
        bar_len = 20
        filled  = int(bar_len * self.hp / self.max_hp)
        bar     = "[" + "#" * filled + "." * (bar_len - filled) + "]"
        return (
            f"  Name   : {self.name}\n"
            f"  Level  : {self.level}\n"
            f"  HP     : {bar} {self.hp}/{self.max_hp}\n"
            f"  ATK    : {self.atk}   DEF: {self.def_}\n"
            f"  XP     : {self.xp}/{self.xp_next}\n"
            f"  Gold   : {self.gold}\n"
            f"  Floor  : {self.floor}"
        )


class Enemy:
    def __init__(self, name: str, floor: int, is_boss: bool = False):
        self.name    = name
        self.is_boss = is_boss
        base_hp  = ENEMY_BASE["hp"][floor]
        base_atk = ENEMY_BASE["atk"][floor]
        base_def = ENEMY_BASE["def"][floor]
        xp_val   = ENEMY_BASE["xp"][floor]
        gold_val = ENEMY_BASE["gold"][floor]

        variance = lambda base: max(1, int(base * random.uniform(0.85, 1.15)))

        if is_boss:
            self.max_hp = int(base_hp * BOSS_MULT["hp"])
            self.hp     = self.max_hp
            self.atk    = int(base_atk * BOSS_MULT["atk"])
            self.def_   = int(base_def * BOSS_MULT["def"])
            self.xp     = int(xp_val   * BOSS_MULT["xp"])
            self.gold   = int(gold_val * BOSS_MULT["gold"])
        else:
            self.hp     = variance(base_hp)
            self.max_hp = self.hp
            self.atk    = variance(base_atk)
            self.def_   = variance(base_def)
            self.xp     = variance(xp_val)
            self.gold   = variance(gold_val)

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.def_)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def hp_bar(self) -> str:
        bar_len = 20
        filled  = int(bar_len * self.hp / self.max_hp)
        return "[" + "#" * filled + "." * (bar_len - filled) + "]"


# ---------------------------------------------------------------------------
# Battle engine
# ---------------------------------------------------------------------------

def do_battle(player: Player, enemy: Enemy) -> bool:
    """
    Run one complete battle.
    Returns True if player wins, False if player dies.
    """
    tag = "[BOSS] " if enemy.is_boss else ""
    print(f"\n{'='*50}")
    print(f"  {tag}{enemy.name} appears!")
    print(f"  HP: {enemy.hp}  ATK: {enemy.atk}  DEF: {enemy.def_}")
    print(f"{'='*50}")
    time.sleep(0.6)

    turn = 1
    while player.is_alive() and enemy.is_alive():
        print(f"\n--- Turn {turn} ---")

        # Player attacks
        dmg = enemy.take_damage(player.atk)
        print(f"  You strike {enemy.name} for {dmg} damage.")
        print(f"  {enemy.name} HP: {enemy.hp_bar()} {enemy.hp}/{enemy.max_hp}")
        time.sleep(0.4)

        if not enemy.is_alive():
            break

        # Enemy attacks
        dmg = player.take_damage(enemy.atk)
        bar_len = 20
        filled  = int(bar_len * player.hp / player.max_hp)
        bar     = "[" + "#" * filled + "." * (bar_len - filled) + "]"
        print(f"  {enemy.name} strikes back for {dmg} damage.")
        print(f"  Your HP: {bar} {player.hp}/{player.max_hp}")
        time.sleep(0.4)

        turn += 1

    if player.is_alive():
        print(f"\n  >> {enemy.name} defeated!")
        player.gain_xp(enemy.xp)
        player.gold += enemy.gold
        print(f"  +{enemy.xp} XP  |  +{enemy.gold} Gold")
        # Small post-battle heal
        heal_amt = int(player.max_hp * 0.1)
        player.heal(heal_amt)
        print(f"  You catch your breath and recover {heal_amt} HP.")
        time.sleep(0.5)
        return True
    else:
        print(f"\n  >> You have been slain by {enemy.name}...")
        time.sleep(0.5)
        return False


# ---------------------------------------------------------------------------
# Floor management
# ---------------------------------------------------------------------------

def next_enemy(player: Player) -> Enemy:
    floor = min(player.floor, 5)
    if player.kills < ENEMIES_PER_FLOOR:
        name = random.choice(FLOOR_ENEMIES[floor])
        return Enemy(name, floor, is_boss=False)
    else:
        name = FLOOR_BOSSES[floor]
        return Enemy(name, floor, is_boss=True)


def advance_floor(player: Player):
    print(f"\n  *** FLOOR {player.floor} CLEARED! ***")
    player.floor += 1
    player.kills  = 0
    player.boss_slain = False
    big_heal = int(player.max_hp * 0.5)
    player.heal(big_heal)
    print(f"  You advance to floor {player.floor}.")
    print(f"  Restored {big_heal} HP.")
    time.sleep(0.8)


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

def clear():
    os.system("clear" if os.name == "posix" else "cls")


def pause():
    input("\n  [Press Enter to continue]")


def show_banner():
    print("""
  ██████  ██    ██ ███    ██  ██████  ███████  ██████  ███    ██
  ██   ██ ██    ██ ████   ██ ██       ██      ██    ██ ████   ██
  ██   ██ ██    ██ ██ ██  ██ ██   ███ █████   ██    ██ ██ ██  ██
  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██    ██ ██  ██ ██
  ██████   ██████  ██   ████  ██████  ███████  ██████  ██   ████
                         A U T O B A T T L E R
""")


def main_menu() -> str:
    print("  1. New Game")
    print("  2. Quit")
    print()
    return input("  Choice: ").strip()


def dungeon_menu(player: Player) -> str:
    enemies_left = ENEMIES_PER_FLOOR - player.kills
    if player.kills < ENEMIES_PER_FLOOR:
        next_label = f"Fight next enemy ({enemies_left} until boss)"
    else:
        floor = min(player.floor, 5)
        next_label = f"Fight BOSS: {FLOOR_BOSSES[floor]}"
    print(f"\n  1. {next_label}")
    print(  "  2. View stats")
    print(  "  3. Quit to main menu")
    print()
    return input("  Choice: ").strip()


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------

def run_game(player: Player):
    MAX_FLOOR = 5
    while True:
        clear()
        show_banner()
        print(f"  Floor {player.floor}  |  {player.name}  |  HP {player.hp}/{player.max_hp}\n")

        if player.floor > MAX_FLOOR:
            print("  *** YOU HAVE CONQUERED THE DUNGEON! ***")
            print(f"  Final level: {player.level}  |  Gold collected: {player.gold}")
            pause()
            return

        choice = dungeon_menu(player)

        if choice == "1":
            enemy = next_enemy(player)
            won   = do_battle(player, enemy)

            if not won:
                print("\n  GAME OVER. The dungeon claims another soul.")
                pause()
                return

            if enemy.is_boss:
                advance_floor(player)
            else:
                player.kills += 1

            pause()

        elif choice == "2":
            clear()
            print("\n" + player.stats_str())
            pause()

        elif choice == "3":
            return

        else:
            print("  Invalid choice.")
            time.sleep(0.5)


def main():
    while True:
        clear()
        show_banner()
        choice = main_menu()

        if choice == "1":
            clear()
            show_banner()
            name = input("  Enter your hero's name: ").strip() or "Hero"
            player = Player(name)
            run_game(player)

        elif choice == "2":
            print("\n  Farewell, adventurer.\n")
            break

        else:
            print("  Invalid choice.")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
