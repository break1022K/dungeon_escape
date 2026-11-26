"""
game/battle.py - 턴제 전투 (④ 게임 진행·전투 담당)

한 턴의 흐름
    1. 화면에 몬스터/플레이어 상태 표시
    2. 플레이어 행동 선택
         1~4 : 캐릭터 행동 (Player.do_action → 할퀴기/앞니/숨기/특수기술)
         5   : 가방 (아이템 사용, 턴 소모)
         6   : 도망 (보스전 불가, 50%)
       행동이 실패(MP 부족 등)하면 턴을 쓰지 않고 다시 고른다.
    3. 몬스터가 살아 있으면 반격, 쓰러졌으면 경험치·골드 획득
    4. 플레이어가 쓰러지면 가방의 불사조 깃털 자동 사용, 없으면 패배
"""
import random

from core.exceptions import GameError
from core.ui import clear, say, pause, ask_number, josa, hp_bar, LINE, THIN
from items import Revive

WIN, LOSE, RUN = "win", "lose", "run"
RUN_CHANCE = 0.5


# ───────────────────────── 가방 메뉴 (전투/캠프 공용) ─────────────────────────
def use_item_menu(player, allow_unequip=False):
    """
    가방을 열어 아이템 1개를 사용한다.
    return: (사용했는지 bool, 보여줄 메시지 str)
    """
    inv = player.inventory
    print()
    inv.show()
    weapon = getattr(player, "weapon", None)
    print(f"  ⚔ 장착 무기: {weapon.name if weapon else '없음'}")
    if inv.is_empty() and not (allow_unequip and weapon):
        return False, "가방이 비어 있다!"

    extra = ""
    if allow_unequip and weapon:
        extra = f"  {len(inv) + 1}. 무기 해제 ({weapon.name})"
        print(extra)
    print("  0. 닫기")
    hi = len(inv) + (1 if extra else 0)
    choice = ask_number("  번호 선택 > ", 0, hi)
    if choice == 0:
        return False, ""

    try:
        if extra and choice == hi:
            return True, inv.unequip(player)
        return True, inv.use(choice - 1, player)
    except GameError as e:          # 체력 가득, 직업 불일치, 가방 가득 등
        return False, f"❌ {e}"


# ───────────────────────────── 전투 ─────────────────────────────
class Battle:
    def __init__(self, player, monsters, floor=1):
        if not monsters:
            raise ValueError("전투할 몬스터가 없습니다.")
        self.player = player
        self.monsters = list(monsters)
        self.floor = floor
        self.gold_earned = 0
        self.exp_earned = 0

    @property
    def enemy(self):
        """지금 싸우는 몬스터 (살아 있는 첫 번째)"""
        for m in self.monsters:
            if m.is_alive():
                return m
        return None

    @property
    def can_run(self):
        return not any(getattr(m, "is_boss", False) for m in self.monsters)

    # ── 화면 ──
    def render(self):
        clear()
        p = self.player
        current = self.enemy
        alive = sum(m.is_alive() for m in self.monsters)
        print(LINE)
        print(f"  ⚔  {self.floor}층 전투   (남은 몬스터 {alive}/{len(self.monsters)})")
        print(THIN)
        for m in self.monsters:
            mark = "▶" if m is current else " "
            boss = " 👑BOSS" if getattr(m, "is_boss", False) else ""
            status = f"HP [{hp_bar(m.hp, m.max_hp, 16)}] {m.hp:>3}/{m.max_hp}" if m.is_alive() else "쓰러짐"
            print(f"  {mark} {m.name:<10}{boss} {status}")
        print(THIN)
        burrow = "  🕳️ 땅속" if p.burrowed else ""
        print(f"  🐾 {p.name} [{p.job}] Lv.{p.level}{burrow}")
        print(f"     HP [{hp_bar(p.hp, p.max_hp, 16)}] {p.hp}/{p.max_hp}")
        print(f"     MP {p.mp}/{p.max_mp}   앞니 {p.teeth}/{p.max_teeth}   공격 {p.atk}  방어 {p.defense}")
        print(LINE)

    # ── 메인 루프 ──
    def run(self):
        self.render()
        names = ", ".join(m.name for m in self.monsters)
        say(f"앗! {josa(names, '이/가')} 나타났다!")
        if self.monsters[0].is_boss:
            say(f"👑 {self.monsters[0].name}: \"감히 내 던전에서 탈출하겠다고? 어림없다!\"")
        pause()

        while True:
            enemy = self.enemy
            if enemy is None:
                self.player.unburrow()
                say(f"🎊 {self.floor}층의 몬스터를 모두 물리쳤다! "
                    f"(경험치 +{self.exp_earned}, 골드 +{self.gold_earned}G)")
                pause()
                return WIN

            self.render()
            if self._player_phase(enemy) == RUN:
                self.player.unburrow()
                pause()
                return RUN

            if enemy.is_alive():
                print()
                enemy.attack(self.player)
                if not self.player.is_alive() and not self._auto_revive():
                    say(f"\n💀 {josa(self.player.name, '은/는')} 쓰러졌다...")
                    pause()
                    return LOSE
            else:
                self._on_enemy_down(enemy)
            pause()

    # ── 플레이어 차례 ──
    def _player_phase(self, enemy):
        """행동을 성공할 때까지 고른다. 도망 성공 시 RUN 반환."""
        p = self.player
        menu = p.action_menu() + ["가방", "도망" if self.can_run else "도망 (불가)"]
        while True:
            print("  무엇을 할까?")
            for i, label in enumerate(menu, 1):
                print(f"   {i}. {label}", end="\n" if i % 2 == 0 else "\t")
            choice = ask_number("\n  > ", 1, len(menu))

            if choice <= 4:
                print()
                if p.do_action(str(choice), enemy) is not None:
                    return "acted"
                continue            # 실패 → 턴 소모 없이 다시 선택

            if choice == 5:
                used, msg = use_item_menu(p)
                if msg:
                    say(msg)
                if used:
                    return "acted"
                continue

            # 6. 도망
            if not self.can_run:
                say("❌ 보스에게서는 도망칠 수 없다!")
                continue
            if random.random() < RUN_CHANCE:
                say("💨 무사히 도망쳤다! (이 층의 몬스터가 새로 나타난다)")
                return RUN
            say("❌ 도망칠 수 없었다!")
            return "acted"

    # ── 결과 처리 ──
    def _on_enemy_down(self, enemy):
        say(f"\n💥 {josa(enemy.name, '은/는')} 쓰러졌다!")
        reward = enemy.drop_reward()
        self.player.earn_gold(reward["gold"])
        self.gold_earned += reward["gold"]
        self.exp_earned += reward["exp"]
        say(f"💰 {reward['gold']}G를 얻었다! (보유 {self.player.gold}G)")
        self.player.gain_exp(reward["exp"])
        nxt = self.enemy
        if nxt:
            say(f"👣 {josa(nxt.name, '이/가')} 다가온다!")

    def _auto_revive(self):
        """쓰러졌을 때 가방에 부활 아이템이 있으면 자동으로 사용"""
        inv = self.player.inventory
        for index, (item, _) in enumerate(inv):
            if isinstance(item, Revive):
                say(f"\n🔥 {josa(self.player.name, '이/가')} 쓰러지려는 순간, {josa(item.name, '이/가')} 빛난다!")
                say(inv.use(index, self.player))
                return True
        return False
