import random

from core.unit import Unit


# =========================================================
# 게임 밸런스 설정값 (숫자만 바꿔서 난이도 조절 가능)
# =========================================================
BOSS_FLOOR = 5          # 보스가 등장하는 층
FLOOR_SCALE = 0.15      # 층이 1 올라갈 때마다 몬스터 능력치 15%씩 증가


# =========================================================
# Monster : 모든 몬스터의 부모 클래스 (Unit 상속)
# =========================================================
class Monster(Unit):
    def __init__(self, name, hp, atk, exp, gold, floor=1):
        # 층수에 따라 능력치를 강하게 만든다 (1층 = 1.0배, 2층 = 1.15배 ...)
        scale = 1 + FLOOR_SCALE * (floor - 1)
        hp = int(hp * scale)
        atk = int(atk * scale)

        # Unit의 생성자 호출 → name, hp(비공개 __hp), atk 설정
        super().__init__(name, hp, atk)

        self.max_hp = hp              # 최대 HP (HP 바 표시, 분노 조건 계산용)
        self.exp = int(exp * scale)   # 처치 시 주는 경험치 (캐릭터/게임 담당이 사용)
        self.gold = int(gold * scale) # 처치 시 주는 골드 (상점 담당이 사용)

    def calc_damage(self, target, power):
        """실제로 들어갈 데미지 계산 (랜덤 ±2, 방어력 적용, 최소 1)"""
        variance = random.randint(-2, 2)
        # 캐릭터에 defense가 있을지 모르니 없으면 0으로 처리 (팀원 코드와 충돌 방지)
        defense = getattr(target, "defense", 0)
        return max(1, power + variance - defense)

    def attack(self, target):
        """기본 공격 (자식 클래스에서 오버라이딩해서 특수 공격을 만든다)
        반환값: 실제로 준 데미지(int) → 전투 담당이 필요하면 사용"""
        damage = self.calc_damage(target, self.atk)
        target.take_damage(damage)    # HP는 반드시 take_damage로만 변경
        print(f"{self.name}의 공격! {target.name}에게 {damage}의 피해!")
        return damage

    def drop_reward(self):
        """처치 보상을 딕셔너리로 반환 (게임/상점 담당이 꺼내 쓰기 쉽게)"""
        return {"exp": self.exp, "gold": self.gold}

    def __str__(self):
        # print(monster) 했을 때 보여줄 정보
        return f"{self.name} (HP {self.hp}/{self.max_hp}, 공격력 {self.atk})"


# =========================================================
# Goblin : 약하지만 재빠름 → 30% 확률로 2연속 공격
# =========================================================
class Goblin(Monster):
    def __init__(self, name="고블린", floor=1):
        super().__init__(name, hp=30, atk=6, exp=10, gold=8, floor=floor)

    def attack(self, target):
        damage = super().attack(target)          # 1타 (부모의 기본 공격 재사용)
        if random.random() < 0.3 and target.is_alive():
            print(f"{self.name}이(가) 재빠르게 한 번 더 찌른다!")
            damage += super().attack(target)     # 2타
        return damage


# =========================================================
# Orc : 균형형 → HP가 40% 이하가 되면 분노해서 공격력 증가 (1번만)
# =========================================================
class Orc(Monster):
    def __init__(self, name="오크", floor=1):
        super().__init__(name, hp=50, atk=9, exp=20, gold=15, floor=floor)
        self.enraged = False    # 분노 상태인지 기록

    def attack(self, target):
        # 아직 분노 안 했고, HP가 40% 이하라면 분노 발동
        if not self.enraged and self.hp <= self.max_hp * 0.4:
            self.enraged = True
            self.atk += 4
            print(f"{self.name}이(가) 분노했다! 공격력이 {self.atk}(으)로 올랐다!")
        return super().attack(target)


# =========================================================
# Ogre : 느리지만 강력 → 3번째 공격마다 '내려찍기'(데미지 2배)
# =========================================================
class Ogre(Monster):
    def __init__(self, name="오우거", floor=1):
        super().__init__(name, hp=80, atk=12, exp=35, gold=25, floor=floor)
        self.turn_count = 0     # 몇 번 공격했는지 세는 변수

    def attack(self, target):
        self.turn_count += 1
        if self.turn_count % 3 == 0:            # 3, 6, 9번째 공격
            damage = self.calc_damage(target, self.atk * 2)
            target.take_damage(damage)
            print(f"{self.name}의 내려찍기!! {target.name}에게 {damage}의 큰 피해!")
            return damage
        if self.turn_count % 3 == 2:            # 내려찍기 직전 예고 (플레이어가 대비하도록)
            print(f"{self.name}이(가) 몽둥이를 높이 치켜든다...")
        return super().attack(target)


# =========================================================
# Boss : 오크 대족장 → HP 50% 이하에서 2페이즈 돌입
#   - 1페이즈: 기본 공격
#   - 2페이즈: 공격력 증가 + 40% 확률로 '전쟁 도끼 휘두르기'(1.5배)
# =========================================================
class Boss(Monster):
    def __init__(self, name="오크 대족장", floor=BOSS_FLOOR):
        super().__init__(name, hp=200, atk=15, exp=150, gold=100, floor=floor)
        self.phase = 1

    def attack(self, target):
        # 2페이즈 진입 체크 (1번만 발동)
        if self.phase == 1 and self.hp <= self.max_hp * 0.5:
            self.phase = 2
            self.atk += 5
            print(f"\n🔥 {self.name}: \"하찮은 동물 놈들이...! 진짜 힘을 보여주마!\"")
            print(f"{self.name}이(가) 2페이즈에 돌입했다! (공격력 {self.atk})\n")

        if self.phase == 2 and random.random() < 0.4:
            damage = self.calc_damage(target, int(self.atk * 1.5))
            target.take_damage(damage)
            print(f"{self.name}의 전쟁 도끼 휘두르기! {target.name}에게 {damage}의 피해!")
            return damage

        return super().attack(target)


# =========================================================
# create_monsters(floor) : 층수에 맞는 몬스터 리스트를 만들어 반환
#   게임 담당은 이 함수만 호출하면 됨 → monsters = create_monsters(3)
# =========================================================
def create_monsters(floor):
    # 잘못된 층수 방지
    if not isinstance(floor, int) or floor < 1:
        raise ValueError(f"층수는 1 이상의 정수여야 합니다: {floor}")

    # 보스 층이면 보스 1마리만 등장
    if floor >= BOSS_FLOOR:
        return [Boss(floor=floor)]

    # 층별로 등장 가능한 몬스터 종류
    if floor == 1:
        pool = [Goblin]
    elif floor == 2:
        pool = [Goblin, Goblin, Orc]     # 고블린이 더 자주 나오도록 2번 넣음
    elif floor == 3:
        pool = [Goblin, Orc, Orc]
    else:                                # 4층
        pool = [Orc, Ogre]

    count = random.randint(1, 3)         # 1~3마리 등장
    monsters = []
    for i in range(count):
        monster_class = random.choice(pool)
        monster = monster_class(floor=floor)
        # 같은 몬스터가 여러 마리면 구분되게 이름 뒤에 A, B, C 붙이기
        if count > 1:
            monster.name = f"{monster.name} {chr(65 + i)}"
        monsters.append(monster)
    return monsters


# =========================================================
# 단독 테스트용 (python -m monsters.monster 로 실행)
# 합칠 때 다른 파일에서 import하면 이 부분은 실행되지 않음
# =========================================================
if __name__ == "__main__":
    # 캐릭터 담당 코드가 아직 없으니 임시 허수아비로 테스트
    class Dummy(Unit):
        def attack(self, target):
            pass

    dummy = Dummy("허수아비 두더지", 500, 0)

    for f in range(1, 6):
        print(f"\n===== {f}층 =====")
        for m in create_monsters(f):
            print(m)
            for _ in range(3):
                m.attack(dummy)
    print(f"\n남은 HP: {dummy.hp}")