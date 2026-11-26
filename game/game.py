"""
game/game.py - 게임 전체 진행 (④ 게임 진행·전투 담당)

메인 메뉴 → 캐릭터 선택 → 층마다 캠프 [전투/가방/상점/상태] → 5층 보스 → 엔딩 → 기록 저장
"""
from characters import JOBS, create_player
from monsters import create_monsters, BOSS_FLOOR
from shop import Shop, record
from core.ui import clear, say, pause, ask_number, ask_yes_no, josa, hp_bar, LINE, THIN
from game.battle import Battle, WIN, LOSE, RUN, use_item_menu

MAX_FLOOR = BOSS_FLOOR
FLOOR_HEAL_RATIO = 0.3      # 다음 층으로 내려갈 때 회복하는 HP 비율
FLOOR_MP_RATIO = 0.5        # 다음 층으로 내려갈 때 회복하는 MP 비율

TITLE = r"""
   ____                                      _____
  |  _ \ _   _ _ __   __ _  ___  ___  _ __  | ____|___  ___ __ _ _ __   ___
  | | | | | | | '_ \ / _` |/ _ \/ _ \| '_ \ |  _| / __|/ __/ _` | '_ \ / _ \
  | |_| | |_| | | | | (_| |  __/ (_) | | | || |___\__ \ (_| (_| | |_) |  __/
  |____/ \__,_|_| |_|\__, |\___|\___/|_| |_||_____|___/\___\__,_| .__/ \___|
                     |___/                                      |_|
            ~ 두더지 원정대, 오크 대족장의 던전을 탈출하라! ~
"""

HOW_TO_PLAY = """
  [게임 방법]

  • 던전은 5층. 각 층의 몬스터를 모두 쓰러뜨리면 다음 층으로 내려간다.
  • 5층에는 보스 '오크 대족장'이 기다린다. 쓰러뜨리면 탈출 성공!

  [전투 행동]
   1. 발톱 할퀴기  : 기본 공격 (비용 없음)
   2. 앞니 던지기  : 공격력 1.5배, 앞니 1개 소모 (층을 내려가면 다시 자람)
   3. 땅속 숨기    : MP 소모, 다음 공격 1번을 완전히 회피
                     → 오우거가 몽둥이를 치켜들면 숨을 때!
   4. 특수 기술    : 직업마다 다른 필살기 (MP 소모)
   5. 가방         : 물약 사용 (턴 소모)
   6. 도망         : 50% 확률. 보스전에서는 불가

  [팁]
  • 몬스터를 쓰러뜨리면 경험치와 골드를 얻는다. 경험치 100마다 레벨 업!
  • 캠프의 상점에서 물약과 직업 전용 무기를 살 수 있다.
  • '불사조 깃털'을 가지고 있으면 쓰러질 때 자동으로 부활한다.
  • 층을 내려갈 때 앞니가 다시 자라고, HP 30% / MP 50%가 회복된다.
"""


class Game:
    def __init__(self):
        self.player = None
        self.floor = 1
        self.shop = Shop()

    # ───────────── 메인 메뉴 ─────────────
    def run(self):
        while True:
            clear()
            print(TITLE)
            print("   1. 새 게임")
            print("   2. 게임 방법")
            print("   3. 명예의 전당")
            print("   0. 종료")
            pick = ask_number("\n   > ", 0, 3)

            if pick == 1:
                self.new_game()
            elif pick == 2:
                clear()
                print(HOW_TO_PLAY)
                pause("Enter를 눌러 돌아가기")
            elif pick == 3:
                clear()
                record.show_ranking()
                pause("Enter를 눌러 돌아가기")
            else:
                print("\n  다음 모험에서 만나요! 🐾\n")
                break

    def new_game(self):
        self.player = self._create_player()
        self.floor = 1
        self._intro()
        cleared = self._play()
        self._ending(cleared)
        floor = MAX_FLOOR if cleared else self.floor
        record.save_record(self.player.name, self.player.job, floor, cleared, self.player.level)

    # ───────────── 캐릭터 생성 ─────────────
    def _create_player(self):
        clear()
        print(f"\n{LINE}\n  [두더지 원정대원 선택]\n{LINE}")
        for key, cls in JOBS.items():
            tmp = cls("미리보기")
            print(f"\n   {key}. {cls.job}  - {cls.description}")
            print(f"      HP {tmp.max_hp} / MP {tmp.max_mp} / 공격 {tmp.atk} / "
                  f"방어 {tmp.defense} / 앞니 {tmp.max_teeth}")
            print(f"      특수 기술: {cls.special_name} - {cls.special_desc} (MP {cls.special_cost})")
        choice = str(ask_number("\n  누구와 함께 모험할까? > ", 1, len(JOBS)))

        while True:
            name = input(f"\n  {JOBS[choice].job}의 이름을 지어 주세요 > ").strip()
            try:
                return create_player(choice, name[:10])
            except ValueError as e:
                print(f"  ❌ {e}")

    def _intro(self):
        clear()
        p = self.player
        say(f"\n  두더지 왕국의 {josa(p.job, '이/가')} 오크 대족장에게 붙잡혀")
        say("  깊은 던전의 꼭대기에 갇히고 말았다...")
        say(f"\n  \"{p.name}, 여기서 나가야 해. 땅속 5층 아래로 파고 내려가자!\"")
        pause()

    # ───────────── 층 진행 ─────────────
    def _play(self):
        """return: True=클리어, False=게임오버/포기"""
        while True:
            if self._camp() == "quit":
                return False

            monsters = create_monsters(self.floor)
            result = Battle(self.player, monsters, self.floor).run()

            if result == LOSE:
                return False
            if result == WIN:
                if self.floor >= MAX_FLOOR:
                    return True
                self._next_floor()
            # RUN 이면 같은 층에 머무름 (다음 전투 때 몬스터가 새로 등장)

    def _next_floor(self):
        self.floor += 1
        p = self.player
        clear()
        say(f"\n  ⛏️  {josa(p.name, '이/가')} 땅을 파고 {self.floor}층으로 내려간다...\n")
        p.regrow_teeth()
        healed = p.heal(int(p.max_hp * FLOOR_HEAL_RATIO))
        restored = p.restore_mp(int(p.max_mp * FLOOR_MP_RATIO))
        say(f"💚 잠깐 숨을 돌렸다. HP +{healed}, MP +{restored}")
        if self.floor == MAX_FLOOR:
            say("\n  ...땅 아래에서 무시무시한 기운이 느껴진다. 보스의 방이다!")
        pause()

    def _camp(self):
        """층 사이 캠프. 'battle' 또는 'quit' 을 돌려줌"""
        msg = ""
        while True:
            self._show_camp(msg)
            msg = ""
            fight = "👑 보스에게 도전" if self.floor == MAX_FLOOR else "⚔  전투 시작"
            print(f"   1. {fight}")
            print("   2. 🎒 가방")
            print("   3. 🏪 상점")
            print("   4. 📜 상태 보기")
            print("   0. 포기하기")
            pick = ask_number("\n  > ", 0, 4)

            if pick == 1:
                return "battle"
            if pick == 2:
                _, msg = use_item_menu(self.player, allow_unequip=True)
            elif pick == 3:
                self.shop.open(self.player)
            elif pick == 4:
                self._show_status()
            elif ask_yes_no("\n  정말 포기할까요? (y/n) > "):
                return "quit"

    def _show_camp(self, msg=""):
        clear()
        p = self.player
        title = f"{self.floor}층 - 보스의 방 앞" if self.floor == MAX_FLOOR else f"{self.floor}층 / {MAX_FLOOR}층"
        print(LINE)
        print(f"  🏕️  캠프 | {title}")
        print(LINE)
        print(f"  {p.name} [{p.job}] Lv.{p.level}   💰 {p.gold}G")
        print(f"  HP [{hp_bar(p.hp, p.max_hp)}] {p.hp}/{p.max_hp}")
        print(f"  MP {p.mp}/{p.max_mp}   앞니 {p.teeth}/{p.max_teeth}")
        print(THIN)
        if msg:
            print(f"  ▶ {msg}\n")

    def _show_status(self):
        clear()
        p = self.player
        print(f"\n{LINE}\n  📜 상태\n{LINE}")
        print(f"  {p}")
        print(f"  특수 기술 : {p.special_name} - {p.special_desc} (MP {p.special_cost})")
        print(f"  땅속 숨기 : MP {p.burrow_cost}")
        print(f"  장착 무기 : {p.weapon if p.weapon else '없음'}")
        print(f"  골드      : {p.gold}G\n")
        p.inventory.show()
        pause("Enter를 눌러 돌아가기")

    # ───────────── 엔딩 ─────────────
    def _ending(self, cleared):
        clear()
        p = self.player
        print(LINE)
        if cleared:
            say("\n  ★★★  축하합니다!  ★★★\n")
            say(f"  {p.job} {josa(p.name, '이/가')} 오크 대족장을 쓰러뜨리고")
            say("  마침내 던전을 탈출했다! 두더지 왕국에 햇살이 비친다. ☀️")
        else:
            say("\n  💀  GAME OVER  💀\n")
            say(f"  {p.name}의 모험은 {self.floor}층에서 끝났다...")
        print(f"\n  최종 기록: Lv.{p.level} / {self.floor}층 / {p.gold}G")
        print(LINE)
        pause()
