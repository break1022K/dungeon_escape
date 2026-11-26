"""
battle.py - 포켓몬식 턴제 전투 (④ 게임 진행·전투 담당)

[다른 팀원 코드에 기대하는 것]  ※ 없는 기능은 자동으로 건너뜀
  캐릭터/몬스터 공통 (core.unit.Unit 상속)
    - name, hp, atk, is_alive(), take_damage(amount), attack(target)
    - attack()/skill() 안에서는 print 하지 말고, 보여줄 문장이 있으면 str로 return
      (데미지 숫자는 전투 화면이 HP 변화량으로 직접 계산해서 보여줌)
  있으면 쓰는 것
    - max_hp, mp, max_mp, speed (속도 높은 쪽이 먼저 공격)
    - skill(target), skill_name  (MP 부족 등은 core.exceptions 예외를 raise)
    - 플레이어: inventory (items 리스트 + use(index, target)), gold
    - 몬스터: gold (처치 보상), is_boss (True면 도망 불가)
"""
import os
import random
import time

# core/exceptions.py 에 있는 예외는 전부 '게임 안에서 처리할 오류'로 취급
try:
    from core import exceptions as _exc
    GAME_ERRORS = tuple(
        v for v in vars(_exc).values()
        if isinstance(v, type) and issubclass(v, Exception)
    )
except ImportError:
    GAME_ERRORS = ()
GAME_ERRORS = GAME_ERRORS + (ValueError, IndexError)

WIN, LOSE, RUN = "win", "lose", "run"

TEXT_DELAY = 0.7      # 메시지 한 줄마다 기다리는 시간(초)
LOG_LINES = 4         # 화면 아래 메시지 창에 보일 줄 수
BAR_LEN = 20          # HP 바 길이
RUN_CHANCE = 0.5      # 도망 성공 확률
ENEMY_SKILL_CHANCE = 0.25


# ───────────────────────── 화면/입력 도우미 ─────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def josa(word, pair):
    """josa('고블린', '이/가') -> '고블린이' / 받침 판단 불가하면 '이(가)'"""
    with_b, without_b = pair.split("/")
    last = word[-1] if word else ""
    if "가" <= last <= "힣":
        has_batchim = (ord(last) - 0xAC00) % 28 > 0
        return word + (with_b if has_batchim else without_b)
    return f"{word}{with_b}({without_b})"


def hp_bar(cur, mx, length=BAR_LEN):
    mx = max(mx, 1)
    filled = min(length, round(length * cur / mx))
    if cur > 0:
        filled = max(filled, 1)        # 살아 있으면 최소 1칸
    return "█" * filled + "░" * (length - filled)


def ask_number(prompt, lo, hi):
    """lo~hi 사이 숫자를 받을 때까지 반복"""
    while True:
        s = input(prompt).strip()
        if s.isdigit() and lo <= int(s) <= hi:
            return int(s)
        print(f"  {lo}~{hi} 사이 숫자를 입력하세요.")


def ensure_max_hp(unit):
    """max_hp가 없는 유닛이면 현재 HP를 최대치로 기록 (HP 바 표시용)"""
    if not hasattr(unit, "max_hp"):
        try:
            unit.max_hp = unit.hp
        except AttributeError:
            pass


def get_max_hp(unit):
    return getattr(unit, "max_hp", unit.hp)


def use_item_menu(player, show):
    """
    가방을 열어 아이템 1개 사용. (전투 중/층 사이 둘 다 사용)
    show: 화면을 다시 그리는 함수
    return: (사용했는지 bool, 보여줄 메시지 str)
    """
    inv = getattr(player, "inventory", None)
    items = list(getattr(inv, "items", None) or []) if inv else []
    if not items:
        return False, "가방이 비어 있다!"

    show()
    print(" [가방]")
    for i, it in enumerate(items, 1):
        print(f"  {i}. {getattr(it, 'name', it)}")
    print("  0. 닫기")
    choice = ask_number(" 사용할 아이템 번호: ", 0, len(items))
    if choice == 0:
        return False, ""

    item = items[choice - 1]
    item_name = getattr(item, "name", str(item))
    try:
        result = inv.use(choice - 1, player)
    except GAME_ERRORS as e:
        return False, f"{item_name}: {e}"

    if isinstance(result, str) and result:
        return True, result
    return True, f"{josa(item_name, '을/를')} 사용했다!"


# ───────────────────────────── 전투 ─────────────────────────────
class Battle:
    def __init__(self, player, monsters, floor=1):
        self.player = player
        self.monsters = list(monsters)
        self.floor = floor
        self.log = []
        self.gold_earned = 0
        for unit in [player] + self.monsters:
            ensure_max_hp(unit)

    # 현재 싸우는 몬스터 (살아 있는 첫 번째)
    @property
    def enemy(self):
        for m in self.monsters:
            if m.is_alive():
                return m
        return None

    @property
    def can_run(self):
        return not any(getattr(m, "is_boss", False) for m in self.monsters)

    # ── 화면 ──
    def render(self):
        """화면을 지우고 현재 상태로 다시 그림 (refresh)"""
        clear()
        p = self.player
        e = self.enemy or self.monsters[-1]
        alive = sum(m.is_alive() for m in self.monsters)

        print("=" * 50)
        print(f"  [{self.floor}층]   남은 몬스터 {alive}/{len(self.monsters)}")
        print("-" * 50)
        boss = " (BOSS)" if getattr(e, "is_boss", False) else ""
        print(f"  {e.name}{boss}")
        print(f"  HP [{hp_bar(e.hp, get_max_hp(e))}] {e.hp}/{get_max_hp(e)}")
        print()
        pad = " " * 22
        print(f"{pad}{p.name}")
        print(f"{pad}HP [{hp_bar(p.hp, get_max_hp(p), 14)}] {p.hp}/{get_max_hp(p)}")
        if hasattr(p, "mp"):
            max_mp = getattr(p, "max_mp", p.mp)
            print(f"{pad}MP {p.mp}/{max_mp}")
        print("-" * 50)
        lines = self.log[-LOG_LINES:]
        for line in lines:
            print(f"  ▶ {line}")
        for _ in range(LOG_LINES - len(lines)):
            print()
        print("=" * 50)

    def say(self, text):
        """메시지 한 줄 추가 → 화면 새로고침 → 잠깐 대기"""
        if not text:
            return
        self.log.append(text)
        self.render()
        time.sleep(TEXT_DELAY)

    # ── 메인 루프 ──
    def run(self):
        first = self.enemy
        self.say(f"앗! {josa(first.name, '이/가')} 나타났다!")

        while self.player.is_alive():
            enemy = self.enemy
            if enemy is None:
                self.say(f"{self.floor}층의 몬스터를 모두 물리쳤다!")
                return WIN

            action = self._choose_action()

            if action == "run":
                if random.random() < RUN_CHANCE:
                    self.say("무사히 도망쳤다!")
                    return RUN
                self.say("도망칠 수 없었다!")
                self._enemy_turn(enemy)
                continue

            if action == "item":              # 아이템은 사용 즉시 적용, 턴 소모
                self._enemy_turn(enemy)
                continue

            # 공격/스킬: 속도가 같거나 빠르면 플레이어 선공
            if getattr(self.player, "speed", 0) >= getattr(enemy, "speed", 0):
                self._player_turn(action, enemy)
                if enemy.is_alive():
                    self._enemy_turn(enemy)
            else:
                self._enemy_turn(enemy)
                if self.player.is_alive():
                    self._player_turn(action, enemy)

            if not enemy.is_alive():
                self._on_enemy_down(enemy)

        self.say(f"{josa(self.player.name, '은/는')} 쓰러졌다...")
        return LOSE

    def _choose_action(self):
        while True:
            self.render()
            sname = getattr(self.player, "skill_name", "스킬")
            print(f"  무엇을 할까?")
            print(f"  1. 공격   2. {sname}   3. 가방   4. 도망")
            choice = ask_number("  > ", 1, 4)

            if choice == 1:
                return "attack"
            if choice == 2:
                if not hasattr(self.player, "skill"):
                    self.say("사용할 수 있는 스킬이 없다!")
                    continue
                return "skill"
            if choice == 3:
                used, msg = use_item_menu(self.player, self.render)
                self.say(msg)
                if used:
                    return "item"
                continue
            if choice == 4:
                if not self.can_run:
                    self.say("보스에게서는 도망칠 수 없다!")
                    continue
                return "run"

    # ── 턴 처리 ──
    def _player_turn(self, action, enemy):
        p = self.player
        before = enemy.hp
        if action == "skill":
            self.say(f"{p.name}의 {getattr(p, 'skill_name', '스킬')}!")
            try:
                result = p.skill(enemy)
            except GAME_ERRORS as e:
                self.say(f"하지만 실패했다! ({e})")
                return
        else:
            self.say(f"{p.name}의 공격!")
            result = p.attack(enemy)
        self._report(result, enemy, before)

    def _enemy_turn(self, enemy):
        p = self.player
        before = p.hp
        if hasattr(enemy, "skill") and random.random() < ENEMY_SKILL_CHANCE:
            self.say(f"{enemy.name}의 {getattr(enemy, 'skill_name', '필살기')}!")
            try:
                result = enemy.skill(p)
            except GAME_ERRORS:
                result = enemy.attack(p)
        else:
            self.say(f"{enemy.name}의 공격!")
            result = enemy.attack(p)
        self._report(result, p, before)

    def _report(self, result, target, hp_before):
        if isinstance(result, str):
            self.say(result)
        dmg = hp_before - target.hp
        if dmg > 0:
            self.say(f"{target.name}에게 {dmg}의 데미지!")
        elif dmg == 0 and not isinstance(result, str):
            self.say("하지만 아무 효과가 없었다!")

    def _on_enemy_down(self, enemy):
        self.say(f"{josa(enemy.name, '은/는')} 쓰러졌다!")
        gold = getattr(enemy, "gold", 0)
        if gold and hasattr(self.player, "gold"):
            self.player.gold += gold
            self.gold_earned += gold
            self.say(f"{gold}골드를 얻었다!")
        nxt = self.enemy
        if nxt:
            self.say(f"{josa(nxt.name, '이/가')} 다가온다!")
