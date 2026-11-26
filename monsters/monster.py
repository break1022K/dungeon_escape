"""
monsters/monster.py - 몬스터 (② 몬스터 담당)

Monster(Unit) ─┬ Goblin : 약하지만 재빠름 (30% 확률 2연타)
               ├ Orc    : HP 40% 이하에서 분노 (공격력 증가)
               ├ Ogre   : 3번째 공격마다 내려찍기 (2배)
               └ Boss   : 오크 대족장, HP 50% 이하에서 2페이즈

게임은 create_monsters(floor) 만 부르면 된다.
"""
import random

from core.unit import Unit
from core.ui import say, josa


# =========================================================
# 게임 밸런스 설정값 (숫자만 바꿔서 난이도 조절 가능)
# =========================================================
BOSS_FLOOR = 5          # 보스가 등장하는 층 (= 마지막 층)
FLOOR_SCALE = 0.15      # 층이 1 올라갈 때마다 몬스터 능력치 15%씩 증가


# =========================================================
# Monster : 모든 몬스터의 부모 클래스 (Unit 상속)
# =========================================================
class Monster(Unit):
    is_boss = False

    def __init__(self, name, hp, atk, defense, exp, gold, floor=1):
        # 층수에 따라 능력치를 강하게 만든다 (1층 = 1.0배, 2층 = 1.15배 ...)
        scale = 1 + FLOOR_SCALE * (floor - 1)
        super().__init__(name, int(hp * scale), int(atk * scale), defense)

        self.exp = int(exp * scale)    # 처치 시 주는 경험치
        self.gold = int(gold * scale)  # 처치 시 주는 골드

    @staticmethod
    def roll(power):
        """공격력에 랜덤 ±2 흔들기 (최소 1)"""
        return max(1, power + random.randint(-2, 2))

    def attack(self, target):
        """기본 공격 (자식 클래스에서 오버라이딩해서 특수 공격을 만든다)
        반환값: 실제로 준 데미지(int). 방어력은 target.take_damage 가 계산."""
        say(f"👊 {self.name}의 공격!")
        return self.strike(target, self.roll(self.atk))

    def drop_reward(self):
        """처치 보상을 딕셔너리로 반환"""
        return {"exp": self.exp, "gold": self.gold}

    def __str__(self):
        return f"{self.name} (HP {self.hp}/{self.max_hp}, 공격력 {self.atk})"


# =========================================================
# Goblin : 약하지만 재빠름 → 30% 확률로 2연속 공격
# =========================================================
class Goblin(Monster):
    def __init__(self, name="고블린", floor=1):
        super().__init__(name, hp=30, atk=12, defense=1, exp=25, gold=12, floor=floor)

    def attack(self, target):
        damage = super().attack(target)          # 1타 (부모의 기본 공격 재사용)
        if random.random() < 0.3 and target.is_alive():
            say(f"🗡️  {josa(self.name, '이/가')} 재빠르게 한 번 더 찌른다!")
            damage += self.strike(target, self.roll(self.atk))
        return damage


# =========================================================
# Orc : 균형형 → HP가 40% 이하가 되면 분노해서 공격력 증가 (1번만)
# =========================================================
class Orc(Monster):
    def __init__(self, name="오크", floor=1):
        super().__init__(name, hp=50, atk=15, defense=3, exp=40, gold=22, floor=floor)
        self.enraged = False

    def attack(self, target):
        if not self.enraged and self.hp <= self.max_hp * 0.4:
            self.enraged = True
            self.atk += 4
            say(f"💢 {josa(self.name, '이/가')} 분노했다! 공격력이 {self.atk}(으)로 올랐다!")
        return super().attack(target)


# =========================================================
# Ogre : 느리지만 강력 → 3번째 공격마다 '내려찍기'(데미지 2배)
# =========================================================
class Ogre(Monster):
    def __init__(self, name="오우거", floor=1):
        super().__init__(name, hp=80, atk=18, defense=4, exp=60, gold=35, floor=floor)
        self.turn_count = 0

    def attack(self, target):
        self.turn_count += 1
        if self.turn_count % 3 == 0:            # 3, 6, 9번째 공격
            say(f"💥 {self.name}의 내려찍기!!")
            return self.strike(target, self.roll(self.atk * 2))
        damage = super().attack(target)
        if self.turn_count % 3 == 2:            # 내려찍기 예고 (플레이어가 숨기로 대비)
            say(f"⚠️  {josa(self.name, '이/가')} 몽둥이를 높이 치켜든다... (땅속에 숨을 때다!)")
        return damage


# =========================================================
# Boss : 오크 대족장 → HP 50% 이하에서 2페이즈 돌입
#   - 1페이즈: 기본 공격
#   - 2페이즈: 공격력 증가 + 40% 확률로 '전쟁 도끼 휘두르기'(1.5배)
# =========================================================
class Boss(Monster):
    is_boss = True

    def __init__(self, name="오크 대족장", floor=BOSS_FLOOR):
        super().__init__(name, hp=160, atk=16, defense=4, exp=150, gold=100, floor=floor)
        self.phase = 1

    def attack(self, target):
        if self.phase == 1 and self.hp <= self.max_hp * 0.5:
            self.phase = 2
            self.atk += 5
            say(f"🔥 {self.name}: \"하찮은 두더지 놈들이...! 진짜 힘을 보여주마!\"")
            say(f"🔥 {josa(self.name, '이/가')} 2페이즈에 돌입했다! (공격력 {self.atk})")

        if self.phase == 2 and random.random() < 0.4:
            say(f"🪓 {self.name}의 전쟁 도끼 휘두르기!")
            return self.strike(target, self.roll(int(self.atk * 1.5)))

        return super().attack(target)


# =========================================================
# create_monsters(floor) : 층수에 맞는 몬스터 리스트를 만들어 반환
# =========================================================
def create_monsters(floor):
    if not isinstance(floor, int) or floor < 1:
        raise ValueError(f"층수는 1 이상의 정수여야 합니다: {floor}")

    if floor >= BOSS_FLOOR:
        return [Boss(floor=floor)]

    if floor == 1:
        pool, counts = [Goblin], (1, 2)
    elif floor == 2:
        pool, counts = [Goblin, Goblin, Orc], (2, 3)   # 고블린이 더 자주 나오도록 2번
    elif floor == 3:
        pool, counts = [Goblin, Orc, Orc], (2, 3)
    else:                                              # 4층
        pool, counts = [Orc, Ogre], (2, 3)

    count = random.randint(*counts)
    monsters = []
    for i in range(count):
        monster = random.choice(pool)(floor=floor)
        if count > 1:   # 여러 마리면 이름 뒤에 A, B, C
            monster.name = f"{monster.name} {chr(65 + i)}"
        monsters.append(monster)
    return monsters


# 단독 테스트용 (python -m monsters.monster)
if __name__ == "__main__":
    class Dummy(Unit):
        def attack(self, target):
            return 0

    dummy = Dummy("허수아비 두더지", 2000, 0)
    for f in range(1, BOSS_FLOOR + 1):
        print(f"\n===== {f}층 =====")
        for m in create_monsters(f):
            print(m)
            for _ in range(3):
                m.attack(dummy)
    print(f"\n남은 HP: {dummy.hp}")
