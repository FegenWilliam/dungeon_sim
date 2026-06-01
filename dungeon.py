import random
import time
import os

# ---------------------------------------------------------------------------
# Weapon / Skill / Proficiency data tables
# ---------------------------------------------------------------------------

# Damage tiers: list of (min_roll, damage). Highest matching tier wins.
# NAT 1 = miss, NAT 20 = crit (max_dmg + atk + crit_dmg), handled separately.

WEAPON_DATA = {
    "Basic Spear": {
        "type":    "spear",
        "tiers":   [(2, 5), (9, 6), (15, 7), (17, 8)],
        "max_dmg": 8,
    },
}

PROFICIENCY_DATA = {
    "Spear Proficiency Lv 1": {
        "weapon_type": "spear",
        "atk_bonus":   2,
    },
}

SKILL_DATA = {
    "Strong Thrust Lv 1": {
        "weapon_type": "spear",
        "tiers":       [(2, 15), (10, 22), (18, 30)],
        "max_dmg":     30,
        "cooldown":    1,
    },
}

# ---------------------------------------------------------------------------
# Floor / enemy tables
# ---------------------------------------------------------------------------

FLOOR_ENEMIES = {
    1: ["Slime",        "Goblin",       "Rat"],
    2: ["Orc",          "Skeleton",     "Dark Elf"],
    3: ["Troll",        "Vampire",      "Wraith"],
    4: ["Dragon Whelp", "Demon Scout",  "Stone Golem"],
    5: ["Elder Demon",  "Lich",         "Titan"],
}

FLOOR_BOSSES = {
    1: "Goblin King",
    2: "Bone Colossus",
    3: "Shadow Drake",
    4: "Infernal Warlord",
    5: "The Void Ancient",
}

# [floor 0 unused, floor 1 … floor 5]
ENEMY_BASE = {
    "hp":   [0,  35,  65, 100, 150, 220],
    "atk":  [0,   6,  10,  15,  21,  28],
    "def":  [0,   1,   3,   5,   8,  12],
    "xp":   [0,  20,  40,  70, 110, 160],
    "gold": [0,  10,  22,  38,  60,  90],
}
BOSS_MULT = {"hp": 3.0, "atk": 1.6, "def": 1.5, "xp": 4.0, "gold": 5.0}

ENEMIES_PER_FLOOR = 3


# ---------------------------------------------------------------------------
# Equipment classes
# ---------------------------------------------------------------------------

class Weapon:
    def __init__(self, name: str):
        d = WEAPON_DATA[name]
        self.name    = name
        self.type    = d["type"]
        self.tiers   = d["tiers"]   # [(min_roll, dmg), ...]
        self.max_dmg = d["max_dmg"]


class Proficiency:
    def __init__(self, name: str):
        d = PROFICIENCY_DATA[name]
        self.name        = name
        self.weapon_type = d["weapon_type"]
        self.atk_bonus   = d["atk_bonus"]


class Skill:
    def __init__(self, name: str):
        d = SKILL_DATA[name]
        self.name        = name
        self.weapon_type = d.get("weapon_type")
        self.tiers       = d["tiers"]
        self.max_dmg     = d["max_dmg"]
        self.max_cd      = d["cooldown"]
        self.current_cd  = 0

    def is_ready(self) -> bool:
        return self.current_cd == 0

    def use(self):
        self.current_cd = self.max_cd

    def tick(self):
        if self.current_cd > 0:
            self.current_cd -= 1


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class Player:
    def __init__(self, name: str):
        self.name      = name
        self.level     = 1
        self.max_hp    = 55
        self.hp        = 55
        self.base_atk  = 4
        self.base_def  = 2
        self.crit_dmg  = 10
        self.xp        = 0
        self.xp_next   = 50
        self.gold      = 0
        self.floor     = 1
        self.kills     = 0

        self.weapon        = Weapon("Basic Spear")
        self.proficiencies = [Proficiency("Spear Proficiency Lv 1")]
        self.skills        = [Skill("Strong Thrust Lv 1")]

    # ---- derived stats ----

    @property
    def atk(self) -> int:
        bonus = sum(
            p.atk_bonus for p in self.proficiencies
            if self.weapon and p.weapon_type == self.weapon.type
        )
        return self.base_atk + bonus

    @property
    def def_(self) -> int:
        return self.base_def

    # ---- combat ----

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.def_)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    # ---- progression ----

    def gain_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self._level_up()

    def _level_up(self):
        self.level    += 1
        hp_gain        = 10
        self.max_hp   += hp_gain
        self.hp        = min(self.hp + hp_gain, self.max_hp)
        self.base_atk += 1
        self.base_def += 1
        self.crit_dmg += 2
        self.xp_next   = int(self.xp_next * 1.5)
        print(f"\n  *** LEVEL UP! You are now level {self.level}! ***")
        print(f"      HP +{hp_gain} | ATK +1 | DEF +1 | Crit DMG +2")

    # ---- display ----

    def hp_bar(self) -> str:
        n = 20
        f = int(n * self.hp / self.max_hp)
        return "[" + "#" * f + "." * (n - f) + "]"

    def stats_str(self) -> str:
        skill_lines = "\n".join(
            f"    {s.name}  CD: {s.current_cd}/{s.max_cd}"
            for s in self.skills
        )
        return (
            f"  Name    : {self.name}\n"
            f"  Level   : {self.level}\n"
            f"  HP      : {self.hp_bar()} {self.hp}/{self.max_hp}\n"
            f"  ATK     : {self.atk} (base {self.base_atk})\n"
            f"  DEF     : {self.def_}\n"
            f"  Crit DMG: +{self.crit_dmg}\n"
            f"  XP      : {self.xp}/{self.xp_next}\n"
            f"  Gold    : {self.gold}\n"
            f"  Floor   : {self.floor}\n"
            f"  Weapon  : {self.weapon.name}\n"
            f"  Skills  :\n{skill_lines}"
        )


# ---------------------------------------------------------------------------
# Enemy
# ---------------------------------------------------------------------------

class Enemy:
    def __init__(self, name: str, floor: int, is_boss: bool = False):
        self.name    = name
        self.is_boss = is_boss
        v = lambda base: max(1, int(base * random.uniform(0.9, 1.1)))

        if is_boss:
            self.max_hp = int(ENEMY_BASE["hp"][floor]  * BOSS_MULT["hp"])
            self.hp     = self.max_hp
            self.atk    = int(ENEMY_BASE["atk"][floor] * BOSS_MULT["atk"])
            self.def_   = int(ENEMY_BASE["def"][floor] * BOSS_MULT["def"])
            self.xp     = int(ENEMY_BASE["xp"][floor]  * BOSS_MULT["xp"])
            self.gold   = int(ENEMY_BASE["gold"][floor] * BOSS_MULT["gold"])
        else:
            self.max_hp = v(ENEMY_BASE["hp"][floor])
            self.hp     = self.max_hp
            self.atk    = v(ENEMY_BASE["atk"][floor])
            self.def_   = v(ENEMY_BASE["def"][floor])
            self.xp     = v(ENEMY_BASE["xp"][floor])
            self.gold   = v(ENEMY_BASE["gold"][floor])

        # Build attack tiers from the enemy's ATK stat
        lo = max(1, self.atk - 2)
        mid = self.atk
        hi  = self.atk + 2
        self.attack_tiers   = [(2, lo), (9, mid), (15, hi), (17, hi + 2)]
        self.attack_max_dmg = hi + 2

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.def_)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def hp_bar(self) -> str:
        n = 20
        f = int(n * self.hp / self.max_hp)
        return "[" + "#" * f + "." * (n - f) + "]"


# ---------------------------------------------------------------------------
# Attack resolution helpers
# ---------------------------------------------------------------------------

def resolve_tier(roll: int, tiers: list) -> int:
    """Return the highest matching tier damage for the given roll."""
    dmg = 0
    for min_roll, tier_dmg in tiers:
        if roll >= min_roll:
            dmg = tier_dmg
    return dmg


def player_attack(player: Player, enemy: Enemy):
    """
    Resolve one player attack.
    Auto-selects a ready skill if available; otherwise basic weapon attack.
    Returns (damage_dealt, roll, result_tag, action_name).
    result_tag: "miss" | "hit" | "crit"
    """
    # Pick action: first ready skill that matches equipped weapon, else basic
    action_skill = None
    for s in player.skills:
        if s.is_ready() and (s.weapon_type is None or s.weapon_type == player.weapon.type):
            action_skill = s
            break

    roll = random.randint(1, 20)

    if action_skill:
        tiers   = action_skill.tiers
        max_dmg = action_skill.max_dmg
        label   = action_skill.name
        action_skill.use()
    else:
        tiers   = player.weapon.tiers
        max_dmg = player.weapon.max_dmg
        label   = f"Basic Attack ({player.weapon.name})"

    if roll == 1:
        return 0, roll, "miss", label

    if roll == 20:
        raw = max_dmg + player.atk + player.crit_dmg
        dmg = max(1, raw - enemy.def_)
        return dmg, roll, "crit", label

    base = resolve_tier(roll, tiers)
    raw  = base + player.atk
    dmg  = max(1, raw - enemy.def_)
    return dmg, roll, "hit", label


def enemy_attack(enemy: Enemy, player: Player):
    """
    Resolve one enemy attack (also uses d20).
    Returns (damage_dealt, roll, result_tag).
    """
    roll = random.randint(1, 20)

    if roll == 1:
        return 0, roll, "miss"

    if roll == 20:
        raw = enemy.attack_max_dmg + 4   # enemy crit bonus
        dmg = player.take_damage(raw)
        return dmg, roll, "crit"

    base = resolve_tier(roll, enemy.attack_tiers)
    dmg  = player.take_damage(base)
    return dmg, roll, "hit"


# ---------------------------------------------------------------------------
# Battle engine
# ---------------------------------------------------------------------------

def do_battle(player: Player, enemy: Enemy) -> bool:
    tag = "[BOSS] " if enemy.is_boss else ""
    print(f"\n{'='*52}")
    print(f"  {tag}{enemy.name} appears!")
    print(f"  HP: {enemy.hp}  ATK: {enemy.atk}  DEF: {enemy.def_}")
    print(f"{'='*52}")
    time.sleep(0.6)

    turn = 1
    while player.is_alive() and enemy.is_alive():
        print(f"\n--- Turn {turn} ---")

        # ---- Player turn ----
        dmg, roll, tag_r, label = player_attack(player, enemy)

        if tag_r == "miss":
            print(f"  [d20: {roll:>2}] {label}  ->  MISS!")
        elif tag_r == "crit":
            print(f"  [d20: {roll:>2}] {label}  ->  CRIT!  {dmg} damage!")
        else:
            print(f"  [d20: {roll:>2}] {label}  ->  {dmg} damage.")

        print(f"  {enemy.name}: {enemy.hp_bar()} {enemy.hp}/{enemy.max_hp}")
        time.sleep(0.45)

        if not enemy.is_alive():
            break

        # ---- Enemy turn ----
        e_dmg, e_roll, e_tag = enemy_attack(enemy, player)

        if e_tag == "miss":
            print(f"  [d20: {e_roll:>2}] {enemy.name} attacks  ->  MISS!")
        elif e_tag == "crit":
            print(f"  [d20: {e_roll:>2}] {enemy.name} attacks  ->  CRIT!  {e_dmg} damage!")
        else:
            print(f"  [d20: {e_roll:>2}] {enemy.name} attacks  ->  {e_dmg} damage.")

        print(f"  You: {player.hp_bar()} {player.hp}/{player.max_hp}")
        time.sleep(0.45)

        # Tick skill cooldowns at end of turn
        for s in player.skills:
            s.tick()

        turn += 1

    if player.is_alive():
        print(f"\n  >> {enemy.name} defeated!")
        player.gain_xp(enemy.xp)
        player.gold += enemy.gold
        print(f"  +{enemy.xp} XP  |  +{enemy.gold} Gold")
        heal_amt = max(1, int(player.max_hp * 0.10))
        player.heal(heal_amt)
        print(f"  You recover {heal_amt} HP.")
        time.sleep(0.5)
        return True
    else:
        print(f"\n  >> You were slain by {enemy.name}...")
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
        return Enemy(FLOOR_BOSSES[floor], floor, is_boss=True)


def advance_floor(player: Player):
    print(f"\n  *** FLOOR {player.floor} CLEARED! ***")
    player.floor += 1
    player.kills  = 0
    heal_amt = int(player.max_hp * 0.5)
    player.heal(heal_amt)
    print(f"  You advance to floor {player.floor}. Restored {heal_amt} HP.")
    time.sleep(0.8)


# ---------------------------------------------------------------------------
# Menus / display
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


def dungeon_menu(player: Player) -> str:
    floor = min(player.floor, 5)
    remaining = ENEMIES_PER_FLOOR - player.kills
    if player.kills < ENEMIES_PER_FLOOR:
        fight_label = f"Fight next enemy  ({remaining} remaining + boss)"
    else:
        fight_label = f"Fight BOSS: {FLOOR_BOSSES[floor]}"

    skill_status = "  ".join(
        f"{s.name} [{'READY' if s.is_ready() else f'CD {s.current_cd}'}]"
        for s in player.skills
    )
    print(f"  Skills: {skill_status}\n")
    print(f"  1. {fight_label}")
    print( "  2. View stats")
    print( "  3. Quit to main menu")
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
        print(
            f"  Floor {player.floor}  |  {player.name}  |  "
            f"HP {player.hp}/{player.max_hp}  |  Lv {player.level}\n"
        )

        if player.floor > MAX_FLOOR:
            print("  *** YOU HAVE CONQUERED THE DUNGEON! ***")
            print(f"  Final level: {player.level}  |  Gold: {player.gold}")
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
            time.sleep(0.4)


def main():
    while True:
        clear()
        show_banner()
        print("  1. New Game")
        print("  2. Quit\n")
        choice = input("  Choice: ").strip()

        if choice == "1":
            clear()
            show_banner()
            name   = input("  Enter your hero's name: ").strip() or "Hero"
            player = Player(name)
            run_game(player)

        elif choice == "2":
            print("\n  Farewell, adventurer.\n")
            break

        else:
            print("  Invalid choice.")
            time.sleep(0.4)


if __name__ == "__main__":
    main()
