"""
game.py - 게임 전체 진행 (④ 게임 진행·전투 담당)

메인 메뉴 → 캐릭터 선택 → 층마다 [전투/가방/상점/상태] → 최상층 보스 → 클리어/게임오버

[다른 팀원 코드에 기대하는 것]
  characters.player : Warrior(name), Mage(name), Archer(name)
  monsters.monster  : create_monsters(floor) -> 몬스터 리스트
  (5인 팀이면) shop.shop.Shop().open(player)
              shop.record.save_record(name, job, floor, cleared), show_ranking()
"""
from characters.player import Warrior, Mage, Archer
from monsters.monster import create_monsters

from game.battle import (
    Battle, WIN, LOSE, RUN,
    clear, ask_number, hp_bar, get_max_hp, ensure_max_hp, use_item_menu,
)

# 상점/기록은 5인 팀만 있으므로 없으면 메뉴에서 숨김
try:
    from shop.shop import Shop
except ImportError:
    Shop = None
try:
    from shop import record
except ImportError:
    record = None


MAX_FLOOR = 5

# (클래스, 화면 이름, 설명)
CHARACTERS = [
    (Warrior, "두더지 전사", "땅을 파고 돌진! 근거리 공격, 튼튼한 체력"),
    (Mage,    "부엉이 마법사", "밤의 마력을 다룬다. 강한 마법, MP 사용"),
    (Archer,  "여우 궁수", "재빠른 몸놀림. 원거리 공격, 높은 속도"),
]

TITLE = r"""
   ____                                      _____
  |  _ \ _   _ _ __   __ _  ___  ___  _ __  | ____|___  ___ __ _ _ __   ___
  | | | | | | | '_ \ / _` |/ _ \/ _ \| '_ \ |  _| / __|/ __/ _` | '_ \ / _ \
  | |_| | |_| | | | | (_| |  __/ (_) | | | || |___\__ \ (_| (_| | |_) |  __/
  |____/ \__,_|_| |_|\__, |\___|\___/|_| |_||_____|___/\___\__,_| .__/ \___|
                     |___/                                      |_|
              ~ 동물 원정대, 오크의 던전을 탈출하라! ~
"""


class Game:
    def __init__(self):
        self.player = None
        self.job = ""
        self.floor = 1

    # ───────────── 메인 메뉴 ─────────────
    def run(self):
        while True:
            clear()
            print(TITLE)
            menus = ["새 게임"]
            if record and hasattr(record, "show_ranking"):
                menus.append("랭킹 보기")
            menus.append("종료")
            for i, m in enumerate(menus, 1):
                print(f"   {i}. {m}")
            pick = menus[ask_number("\n   > ", 1, len(menus)) - 1]

            if pick == "새 게임":
                self.new_game()
            elif pick == "랭킹 보기":
                clear()
                record.show_ranking()
                input("\n(Enter를 눌러 돌아가기)")
            else:
                print("\n  다음 모험에서 만나요!")
                break

    def new_game(self):
        self.player = self._create_player()
        self.floor = 1
        cleared = self._play()
        self._ending(cleared)
        self._save_record(cleared)

    # ───────────── 캐릭터 생성 ─────────────
    def _create_player(self):
        clear()
        print("\n  [캐릭터 선택]\n")
        for i, (_, label, desc) in enumerate(CHARACTERS, 1):
            print(f"   {i}. {label:<8} - {desc}")
        idx = ask_number("\n  누구와 함께 모험할까? > ", 1, len(CHARACTERS)) - 1
        cls, label, _ = CHARACTERS[idx]

        name = ""
        while not name:
            name = input(f"\n  {label}의 이름을 지어주세요 > ").strip()
        self.job = label
        player = cls(name)
        ensure_max_hp(player)
        return player

    # ───────────── 층 진행 ─────────────
    def _play(self):
        """return: True=클리어, False=게임오버/포기"""
        while self.floor <= MAX_FLOOR:
            action = self._floor_menu()

            if action == "quit":
                return False

            monsters = create_monsters(self.floor)
            result = Battle(self.player, monsters, self.floor).run()

            if result == LOSE:
                return False
            if result == WIN:
                self.floor += 1
            # RUN이면 같은 층에 머무름 (다음 전투 때 몬스터 새로 등장)
        return True

    def _floor_menu(self):
        """층 사이 쉬는 곳. '전투' 또는 'quit' 을 돌려줌"""
        msg = ""
        while True:
            self._show_camp(msg)
            msg = ""
            menus = ["전투 시작", "가방", "상태 보기"]
            if Shop:
                menus.insert(2, "상점")
            menus.append("포기하기")
            for i, m in enumerate(menus, 1):
                print(f"   {i}. {m}")
            pick = menus[ask_number("\n  > ", 1, len(menus)) - 1]

            if pick == "전투 시작":
                return "battle"
            if pick == "가방":
                _, msg = use_item_menu(self.player, lambda: self._show_camp())
            elif pick == "상점":
                self._open_shop()
            elif pick == "상태 보기":
                self._show_status()
            elif pick == "포기하기":
                if input("\n  정말 포기할까요? (y/n) > ").strip().lower() == "y":
                    return "quit"

    def _show_camp(self, msg=""):
        clear()
        p = self.player
        if self.floor == MAX_FLOOR:
            title = f"{self.floor}층 - 보스의 방 앞"
        else:
            title = f"{self.floor}층 / {MAX_FLOOR}층"
        print("=" * 50)
        print(f"  {title}")
        print("=" * 50)
        print(f"  {p.name} ({self.job})")
        print(f"  HP [{hp_bar(p.hp, get_max_hp(p))}] {p.hp}/{get_max_hp(p)}")
        if hasattr(p, "gold"):
            print(f"  골드 {p.gold}")
        print("-" * 50)
        if msg:
            print(f"  ▶ {msg}\n")

    def _show_status(self):
        clear()
        p = self.player
        print("\n  [상태]")
        print(f"  이름   : {p.name}")
        print(f"  직업   : {self.job}")
        print(f"  HP     : {p.hp}/{get_max_hp(p)}")
        if hasattr(p, "mp"):
            print(f"  MP     : {p.mp}/{getattr(p, 'max_mp', p.mp)}")
        print(f"  공격력 : {p.atk}")
        for attr, label in [("speed", "속도"), ("gold", "골드"), ("skill_name", "스킬")]:
            if hasattr(p, attr):
                print(f"  {label:<5}: {getattr(p, attr)}")
        input("\n(Enter를 눌러 돌아가기)")

    def _open_shop(self):
        shop = Shop()
        for method in ("open", "run", "enter"):
            if hasattr(shop, method):
                getattr(shop, method)(self.player)
                return

    # ───────────── 엔딩/기록 ─────────────
    def _ending(self, cleared):
        clear()
        if cleared:
            print("\n  ★ 축하합니다! ★")
            print(f"  {self.player.name}({self.job})이(가) 오우거를 쓰러뜨리고 던전을 탈출했다!")
        else:
            print("\n  GAME OVER")
            print(f"  {self.player.name}의 모험은 {self.floor}층에서 끝났다...")
        input("\n(Enter를 눌러 계속)")

    def _save_record(self, cleared):
        if record and hasattr(record, "save_record"):
            floor = MAX_FLOOR if cleared else self.floor
            record.save_record(self.player.name, self.job, floor, cleared)
