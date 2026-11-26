# characters/player.py — 두더지 캐릭터 (① 캐릭터 담당)
#
# ┌──────────── 이 파일에 들어간 4가지 조건 ────────────┐
# │ 1. 캡슐화   : __mp, __teeth, __level, __exp, __burrowed │
# │              → @property(getter) / @setter 로만 접근   │
# │ 2. 상속     : Unit → Player → Warrior / Mage / Archer  │
# │ 3. 오버라이딩: take_damage(), special(), __str__()      │
# │ 4. 예외처리 : raise 로 예외 던지기 +                    │
# │              do_action() 안의 try / except / else / finally │
# └─────────────────────────────────────────────────┘
#
# 수치는 모두 임시값이에요. 팀 테스트 후 조정해요.

from core.unit import Unit
from core.exceptions import (
    GameError,
    UnitDeadError,
    InvalidActionError,
    NotEnoughMPError,
    NoTeethError,
)

EXP_PER_LEVEL = 100      # 경험치 100마다 레벨 업


# ════════════════ [상속] Unit을 물려받은 두더지 공통 클래스 ════════════════

class Player(Unit):
    """모든 두더지 캐릭터의 공통 부모 클래스"""

    job = "두더지"
    special_name = "특수 기술"
    special_cost = 0
    burrow_cost = 5          # 땅속 숨기에 드는 MP

    def __init__(self, name, hp, attack, defense, mp, teeth=2):
        # [상속] 이름·HP·공격·방어는 부모(Unit)의 __init__이 저장해요.
        super().__init__(name, hp, attack, defense)

        # [캡슐화] 밑줄 두 개(__)로 숨겨서 밖에서 직접 못 바꾸게 해요.
        self.max_mp = mp
        self.__mp = mp
        self.max_teeth = teeth
        self.__teeth = teeth
        self.__level = 1
        self.__exp = 0
        self.__burrowed = False   # True면 땅속에 숨어 있는 상태

    # ─────────── [캡슐화] getter / setter ───────────
    @property
    def mp(self):
        """MP 읽기 (getter)"""
        return self.__mp

    @mp.setter
    def mp(self, value):
        """MP 바꾸기 (setter): 0 ~ 최대 MP 사이로만 들어가요."""
        if not isinstance(value, (int, float)):
            raise TypeError("MP는 숫자만 넣을 수 있어요.")
        self.__mp = max(0, min(int(value), self.max_mp))

    @property
    def teeth(self):
        """남은 앞니 개수 (getter)"""
        return self.__teeth

    @teeth.setter
    def teeth(self, value):
        """앞니 개수 바꾸기 (setter): 0 ~ 최대 앞니 사이로만"""
        if not isinstance(value, int):
            raise TypeError("앞니 개수는 정수만 넣을 수 있어요.")
        self.__teeth = max(0, min(value, self.max_teeth))

    @property
    def level(self):
        """레벨은 읽기만 가능 (setter 없음 → 밖에서 못 바꿈)"""
        return self.__level

    @property
    def exp(self):
        """경험치도 읽기만 가능. 올릴 때는 gain_exp()를 써요."""
        return self.__exp

    @property
    def burrowed(self):
        """땅속에 숨어 있는지 (읽기만 가능). 숨을 때는 burrow()를 써요."""
        return self.__burrowed

    # ─────────── 내부 도우미 (이름 앞 _ 는 "안에서만 쓰는 것") ───────────
    def _check_alive(self):
        if not self.is_alive:
            raise UnitDeadError(f"{self.name}은(는) 쓰러져서 행동할 수 없어요.")

    def _check_target(self, target):
        if not target.is_alive:
            raise UnitDeadError(f"{target.name}은(는) 이미 쓰러졌어요.")

    def _use_mp(self, cost):
        # [예외처리] 조건이 안 맞으면 예외를 던져요(raise).
        if self.mp < cost:
            raise NotEnoughMPError(f"MP가 부족해요! (필요 {cost}, 현재 {self.mp})")
        self.mp -= cost

    def _use_tooth(self):
        if self.teeth <= 0:
            raise NoTeethError("던질 앞니가 없어요! 다음 층에서 다시 자라요.")
        self.teeth -= 1

    # ─────────── ① 발톱 할퀴기 (기본 공격, 비용 없음) ───────────
    def claw_attack(self, target):
        """발톱으로 할퀴기. 상대에게 준 피해량을 돌려준다."""
        self._check_alive()
        self._check_target(target)
        print(f"🐾 {self.name}의 발톱 할퀴기!")
        return target.take_damage(self.attack)

    # ─────────── ② 앞니 던지기 (공격력 1.5배, 앞니 1개) ───────────
    def throw_tooth(self, target):
        """앞니를 뽑아 창처럼 던진다. 앞니가 없으면 NoTeethError."""
        self._check_alive()
        self._check_target(target)
        self._use_tooth()
        print(f"🦷 {self.name}이(가) 앞니를 뽑아 창처럼 던졌다! (남은 앞니 {self.teeth}개)")
        return target.take_damage(int(self.attack * 1.5))

    def regrow_teeth(self):
        """앞니가 다시 자란다. (층을 넘어갈 때 게임 담당이 불러 줌)"""
        self.teeth = self.max_teeth
        print(f"🦷 {self.name}의 앞니가 다시 자랐다! ({self.teeth}/{self.max_teeth})")

    # ─────────── ③ 땅속 숨기 (다음 공격 1번 회피) ───────────
    def burrow(self):
        """땅속으로 숨는다. 다음에 받는 공격 1번을 피한다."""
        self._check_alive()
        if self.__burrowed:
            raise InvalidActionError("이미 땅속에 숨어 있어요.")
        self._use_mp(self.burrow_cost)
        self.__burrowed = True
        print(f"🕳️  {self.name}이(가) 땅속으로 숨었다! 다음 공격을 피해요.")

    # [오버라이딩] 부모 Unit의 take_damage를 두더지에 맞게 다시 만들어요.
    def take_damage(self, amount):
        """땅속에 숨어 있으면 피해 0으로 피하고 다시 나온다."""
        if self.__burrowed:
            self.__burrowed = False
            print(f"  💨 {self.name}이(가) 땅속에서 공격을 피하고 튀어나왔다!")
            return 0
        return super().take_damage(amount)    # 숨지 않았으면 부모(Unit) 방식 그대로

    # ─────────── ④ 특수 기술 (직업마다 다르게) ───────────
    def special(self, target):
        """[오버라이딩] 자식 클래스(Warrior, Mage, Archer)가 다시 만든다."""
        raise NotImplementedError("직업 클래스에서 special()을 만들어 주세요.")

    # ─────────── [예외처리] try / except / else / finally ───────────
    def do_action(self, choice, target=None):
        """메뉴 번호로 행동하기. 전투 담당이 이것 하나만 불러도 돼요.

        "1" 발톱 할퀴기, "2" 앞니 던지기, "3" 땅속 숨기, "4" 특수 기술
        성공하면 준 피해량(숨기는 0), 실패하면 None을 돌려줘요.
        예외가 나도 게임이 멈추지 않고 메시지만 보여 줘요.
        """
        actions = {
            "1": self.claw_attack,
            "2": self.throw_tooth,
            "3": self.burrow,
            "4": self.special,
        }
        try:
            action = actions[str(choice).strip()]       # 없는 번호면 KeyError
            if action == self.burrow:
                action()
                result = 0
            else:
                if target is None:
                    raise InvalidActionError("공격할 대상이 없어요.")
                result = action(target)
        except KeyError:
            print(f"❌ '{choice}'는 없는 행동이에요. 1~4 중에서 골라 주세요.")
            return None
        except GameError as e:          # MP 부족, 앞니 없음, 쓰러짐 등 게임 예외 전부
            print(f"❌ {e}")
            return None
        else:                           # 예외 없이 성공했을 때만 실행
            return result
        finally:                        # 성공하든 실패하든 항상 실행
            print(f"   └ {self.name} 상태: HP {self.hp}/{self.max_hp}, "
                  f"MP {self.mp}/{self.max_mp}, 앞니 {self.teeth}개")

    # ─────────── 성장 ───────────
    def gain_exp(self, amount):
        """경험치를 얻는다. 100이 모이면 레벨 업. (몬스터를 잡은 뒤 불러 줌)"""
        if amount < 0:
            raise ValueError("경험치는 0 이상이어야 해요.")
        self.__exp += amount
        print(f"✨ 경험치 +{amount} ({self.__exp}/{EXP_PER_LEVEL})")
        while self.__exp >= EXP_PER_LEVEL:
            self.__exp -= EXP_PER_LEVEL
            self._level_up()

    def _level_up(self):
        self.__level += 1
        self.max_hp += 10
        self.attack += 2
        self.defense += 1
        self.hp = self.max_hp      # HP·MP 가득 채움
        self.mp = self.max_mp
        print(f"🎉 레벨 업! {self.name} Lv.{self.__level} "
              f"(HP {self.max_hp}, 공격 {self.attack}, 방어 {self.defense})")

    # [오버라이딩] 부모 Unit의 __str__을 두더지용으로 다시 만들어요.
    def __str__(self):
        state = " [땅속]" if self.__burrowed else ""
        return (f"[{self.job}] {self.name} Lv.{self.level}{state} | "
                f"HP {self.hp}/{self.max_hp} | MP {self.mp}/{self.max_mp} | "
                f"공격 {self.attack} 방어 {self.defense} | "
                f"앞니 {self.teeth}/{self.max_teeth} | EXP {self.exp}/{EXP_PER_LEVEL}")


# ════════════════ [상속] 직업 3종: Player를 물려받아요 ════════════════

class Warrior(Player):
    """발톱 전사: HP 120, MP 30, 공격 14, 방어 6, 앞니 2"""

    job = "발톱 전사"
    special_name = "강철 발톱 연타"
    special_cost = 10

    def __init__(self, name):
        super().__init__(name, hp=120, attack=14, defense=6, mp=30, teeth=2)

    # [오버라이딩] Player의 special을 전사 기술로 다시 만들어요.
    def special(self, target):
        """강철 발톱 연타: 2번 연속 공격. MP 10"""
        self._check_alive()
        self._check_target(target)
        self._use_mp(self.special_cost)
        print(f"⚔️  {self.name}의 {self.special_name}!")
        total = 0
        for _ in range(2):
            if not target.is_alive:      # 첫 타에 쓰러지면 멈춤
                break
            total += target.take_damage(self.attack)
        return total


class Mage(Player):
    """흙마법사: HP 85, MP 60, 공격 10, 방어 3, 앞니 2"""

    job = "흙마법사"
    special_name = "지진"
    special_cost = 15
    burrow_cost = 3          # 땅에 익숙해서 숨기 MP가 적음

    def __init__(self, name):
        super().__init__(name, hp=85, attack=10, defense=3, mp=60, teeth=2)

    # [오버라이딩] Player의 special을 마법사 기술로 다시 만들어요.
    def special(self, target):
        """지진: 공격력 2배, 상대 방어 무시. MP 15"""
        self._check_alive()
        self._check_target(target)
        self._use_mp(self.special_cost)
        print(f"🌋 {self.name}의 {self.special_name}! 땅이 흔들린다!")
        # take_damage가 방어력만큼 빼므로, 그만큼 미리 더해서 방어를 무시해요.
        return target.take_damage(self.attack * 2 + target.defense)


class Archer(Player):
    """앞니 투척수: HP 95, MP 40, 공격 12, 방어 4, 앞니 4"""

    job = "앞니 투척수"
    special_name = "관통 앞니 창"
    special_cost = 12

    def __init__(self, name):
        super().__init__(name, hp=95, attack=12, defense=4, mp=40, teeth=4)

    # [오버라이딩] Player의 special을 투척수 기술로 다시 만들어요.
    def special(self, target):
        """관통 앞니 창: 공격력 2.5배. MP 12 + 앞니 1개"""
        self._check_alive()
        self._check_target(target)
        if self.teeth <= 0:              # MP만 날아가지 않게 앞니부터 확인
            raise NoTeethError("관통 앞니 창에 쓸 앞니가 없어요!")
        self._use_mp(self.special_cost)
        self._use_tooth()
        print(f"🏹 {self.name}의 {self.special_name}! (남은 앞니 {self.teeth}개)")
        return target.take_damage(int(self.attack * 2.5))


# ════════════════ 캐릭터 만들기 (게임 담당이 사용) ════════════════

JOBS = {"1": Warrior, "2": Mage, "3": Archer}


def create_player(choice, name):
    """"1" 발톱 전사, "2" 흙마법사, "3" 앞니 투척수. 없는 번호는 ValueError."""
    # [예외처리] 이름이 비어 있거나 번호가 틀리면 예외를 던져요.
    if not str(name).strip():
        raise ValueError("이름을 입력해 주세요.")
    job_class = JOBS.get(str(choice).strip())
    if job_class is None:
        raise ValueError(f"'{choice}'는 없는 직업이에요. 1, 2, 3 중에서 골라 주세요.")
    return job_class(name)