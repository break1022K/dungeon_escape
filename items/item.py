"""
items/item.py
=============
던전 탈출(Dungeon Escape) - 아이템 모듈  (③ 아이템·인벤토리 담당)

[세계관]
    동물들이 사는 판타지 왕국. 두더지 전사, 부엉이 마법사, 여우 궁수가
    오크·고블린·오우거가 득실대는 던전을 탈출한다.
    포켓몬스터처럼 '턴제 전투' 중에 가방(인벤토리)을 열어 아이템을 쓸 수 있다.

[이 파일에 들어있는 것]
    Item        : 모든 아이템의 부모 클래스 (추상 클래스 역할)
    Potion      : HP 회복 물약 (소모품, 겹쳐 쌓기 가능)
      ├ ManaPotion : MP 회복 물약 (부엉이 마법사 같은 MP 캐릭터용)
      └ Revive     : 쓰러진 동료를 되살리는 부활 아이템 (포켓몬의 '기력의 조각')
    Weapon      : 장착하면 공격력(atk)이 오르는 무기 (직업 제한 가능)
    create_item(): 아이템 ID로 새 아이템을 만들어 주는 함수 (상점·몬스터 드롭용)

[다른 팀과의 약속 (인터페이스)]
    아이템은 core.unit.Unit 을 상속한 캐릭터에게 사용된다.
    Unit 은 기본으로 name, hp, atk, take_damage(), is_alive() 만 가지고 있으므로
    아이템이 제대로 동작하려면 ① 캐릭터 담당이 아래 속성을 만들어 주면 좋다.
        - max_hp : 최대 체력  (없으면 회복량에 상한이 없음)
        - weapon : 현재 장착한 무기, 처음에는 None  (없으면 장착 시 자동 생성)
        - mp, max_mp : 마나 (ManaPotion 을 쓰려면 필요)
    ※ 어떤 속성이 없어도 프로그램이 죽지 않도록 getattr() 로 안전하게 확인한다.

[HP 변경 규칙]
    Unit 의 __hp 는 private(이름 맹글링) 이고 "HP는 take_damage()로만 변경" 규칙이 있다.
    그래서 회복은 '음수 데미지'로 처리한다.
        target.take_damage(-30)  →  __hp = max(0, hp - (-30)) = hp + 30
    규칙을 어기지 않으면서 회복할 수 있는 방법이다.
    (팀 합의로 Unit 에 heal() 메서드가 생기면 _restore_hp() 한 곳만 고치면 된다.)
"""

# ---------------------------------------------------------------------------
# 사용자 정의 예외 가져오기
# ---------------------------------------------------------------------------
# 예외는 원래 core/exceptions.py(공통 파일)에 모아두기로 했다.
# 하지만 각 팀이 동시에 작업하다 보면 아직 그 파일에 우리가 쓸 예외가 없을 수 있다.
# 그래서 먼저 core 에서 가져와 보고, 없으면(ImportError) 여기서 임시로 정의한다.
# → 팀 합의 후 core/exceptions.py 에 아래 세 클래스를 추가하면 그쪽 것이 사용된다.
try:
    from core.exceptions import ItemUseError, InventoryFullError, ItemNotFoundError
except ImportError:
    class ItemUseError(Exception):
        """아이템을 지금 사용할 수 없을 때 (예: 체력이 이미 가득, 직업이 맞지 않는 무기)"""

    class InventoryFullError(Exception):
        """인벤토리(가방)에 빈 칸이 없을 때"""

    class ItemNotFoundError(Exception):
        """없는 칸 번호를 고르거나, 없는 아이템을 찾을 때"""


# ---------------------------------------------------------------------------
# 직업 이름 표시용 사전
# ---------------------------------------------------------------------------
# 무기의 직업 제한은 '클래스 이름(문자열)'으로 검사한다.
# characters/player.py 의 클래스 이름(Warrior, Mage, Archer)과 반드시 같아야 한다!
# 화면에 보여줄 때는 아래 한글 이름을 사용한다. (캐릭터 담당과 이름 맞추기)
CLASS_DISPLAY_NAMES = {
    "Warrior": "두더지 전사",   # 근거리 공격
    "Mage": "부엉이 마법사",    # 마법 공격 (MP 사용)
    "Archer": "여우 궁수",      # 원거리 공격
}


# ---------------------------------------------------------------------------
# 내부 도우미 함수 (이름 앞의 _ 는 "이 모듈 안에서만 쓰는 함수"라는 관례)
# ---------------------------------------------------------------------------
def _restore_hp(target, amount):
    """
    대상의 HP를 amount 만큼 회복시키고, '실제로 회복된 양'을 돌려준다.

    - max_hp 속성이 있으면 최대 체력을 넘지 않도록 회복량을 잘라낸다.
    - 회복은 take_damage(음수) 로 처리한다. (파일 맨 위 [HP 변경 규칙] 참고)
    """
    max_hp = getattr(target, "max_hp", None)   # 속성이 없으면 None
    if max_hp is not None:
        amount = min(amount, max_hp - target.hp)  # 넘치는 만큼 잘라내기
    amount = max(0, amount)                       # 음수가 되지 않도록 방어

    if amount > 0:
        target.take_damage(-amount)               # 음수 데미지 = 회복
    return amount


def _hp_text(target):
    """'HP 45/100' 처럼 화면에 보여줄 문자열을 만든다. max_hp 가 없으면 'HP 45'."""
    max_hp = getattr(target, "max_hp", None)
    if max_hp is None:
        return f"HP {target.hp}"
    return f"HP {target.hp}/{max_hp}"


# ===========================================================================
# 1. Item : 모든 아이템의 부모 클래스
# ===========================================================================
class Item:
    """
    모든 아이템의 공통 정보와 기능을 가진 부모 클래스.
    직접 쓰지 않고, Potion·Weapon 처럼 상속받아 use() 를 오버라이딩해서 쓴다.

    클래스 속성 (자식 클래스마다 다르게 덮어쓴다)
        stackable  : 같은 아이템끼리 한 칸에 겹쳐 쌓을 수 있는가? (물약 x3 처럼)
        consumable : 사용하면 사라지는가? (물약은 True, 무기는 False)
        category   : 인벤토리 정렬/표시에 쓰는 분류 이름

    인스턴스 속성
        name        : 아이템 이름
        price       : 상점 구매 가격 (골드)
        description : 아이템 설명
    """

    stackable = False
    consumable = True
    category = "기타"

    def __init__(self, name, price, description=""):
        # 잘못된 값으로 아이템이 만들어지는 것을 막는다 (방어적 프로그래밍)
        if not name:
            raise ValueError("아이템 이름은 비워둘 수 없습니다.")
        if price < 0:
            raise ValueError("아이템 가격은 0 이상이어야 합니다.")

        self.name = name
        self.price = price
        self.description = description

    @property
    def sell_price(self):
        """상점에 되팔 때 가격. 구매가의 절반 (⑤ 상점 담당이 사용)."""
        return self.price // 2

    def is_same_kind(self, other):
        """
        두 아이템이 '같은 종류'인지 확인한다. (인벤토리에서 겹쳐 쌓을 때 사용)
        클래스가 같고 이름도 같으면 같은 아이템으로 본다.
        """
        return type(self) is type(other) and self.name == other.name

    def use(self, target):
        """
        아이템을 target(캐릭터)에게 사용한다.
        - 성공하면 화면에 출력할 '메시지 문자열'을 돌려준다.
        - 사용할 수 없으면 ItemUseError 를 발생시킨다.
        자식 클래스에서 반드시 오버라이딩해야 한다. (Unit.attack 과 같은 방식)
        """
        raise NotImplementedError(f"{type(self).__name__} 클래스에 use()가 구현되지 않았습니다.")

    def __str__(self):
        """print(item) 했을 때 보이는 모습"""
        return f"{self.name} ({self.price}G) - {self.description}"

    def __repr__(self):
        """디버깅용 표현 (리스트를 print 할 때 보임)"""
        return f"{type(self).__name__}({self.name!r})"


# ===========================================================================
# 2. Potion : HP 회복 물약
# ===========================================================================
class Potion(Item):
    """
    HP를 회복시키는 소모품. 사용하면 하나 줄어들고, 같은 물약끼리 겹쳐 쌓인다.

    추가 속성
        amount : 회복량
                 (Potion 은 HP, 자식인 ManaPotion 은 MP 회복량으로 사용)
    """

    stackable = True     # 가방 한 칸에 '회복 열매 x5' 처럼 쌓인다
    consumable = True    # 쓰면 사라진다
    category = "회복"

    def __init__(self, name, price, amount, description=""):
        super().__init__(name, price, description)   # 부모(Item)의 초기화 먼저
        if amount <= 0:
            raise ValueError("회복량은 1 이상이어야 합니다.")
        self.amount = amount

    def check_usable(self, target):
        """
        지금 이 물약을 target 에게 쓸 수 있는지 검사한다.
        쓸 수 없으면 ItemUseError 를 발생시킨다. (문제 없으면 아무 일도 없음)
        자식 클래스(ManaPotion, Revive)는 이 메서드만 바꿔서 조건을 다르게 한다.
        """
        if not target.is_alive():
            raise ItemUseError(f"{target.name}은(는) 쓰러져 있어서 {self.name}을(를) 쓸 수 없다!")

        max_hp = getattr(target, "max_hp", None)
        if max_hp is not None and target.hp >= max_hp:
            raise ItemUseError(f"{target.name}의 체력은 이미 가득 차 있다!")

    def use(self, target):
        """HP를 회복시키고 결과 메시지를 돌려준다."""
        self.check_usable(target)              # 못 쓰면 여기서 예외 발생 → 아래 실행 안 됨
        healed = _restore_hp(target, self.amount)
        return (f"{target.name}은(는) {self.name}을(를) 사용했다! "
                f"HP가 {healed} 회복되었다. ({_hp_text(target)})")

    def __str__(self):
        return f"{self.name} ({self.price}G) - HP {self.amount} 회복 | {self.description}"


# ---------------------------------------------------------------------------
# 2-1. ManaPotion : MP 회복 물약 (Potion 상속)
# ---------------------------------------------------------------------------
class ManaPotion(Potion):
    """
    MP를 회복시키는 물약. 부엉이 마법사처럼 mp 속성이 있는 캐릭터만 쓸 수 있다.

    대상 캐릭터에게 필요한 것 (캐릭터 담당과 약속)
        - mp, max_mp 속성
        - (선택) restore_mp(amount) 메서드가 있으면 그것을 우선 사용한다.
    """

    def check_usable(self, target):
        if not target.is_alive():
            raise ItemUseError(f"{target.name}은(는) 쓰러져 있어서 {self.name}을(를) 쓸 수 없다!")

        # hasattr(객체, "속성이름") : 그 속성이 있는지 True/False 로 알려준다
        if not hasattr(target, "mp"):
            raise ItemUseError(f"{target.name}은(는) 마나를 쓰지 않는다. {self.name}은(는) 효과가 없다!")

        max_mp = getattr(target, "max_mp", None)
        if max_mp is not None and target.mp >= max_mp:
            raise ItemUseError(f"{target.name}의 마나는 이미 가득 차 있다!")

    def use(self, target):
        self.check_usable(target)
        before = target.mp

        if hasattr(target, "restore_mp"):
            # 캐릭터 쪽에 MP 회복 메서드가 있으면 그것을 존중한다 (캡슐화)
            target.restore_mp(self.amount)
        else:
            max_mp = getattr(target, "max_mp", None)
            new_mp = before + self.amount
            target.mp = new_mp if max_mp is None else min(new_mp, max_mp)

        restored = target.mp - before
        max_mp = getattr(target, "max_mp", None)
        mp_text = f"MP {target.mp}" if max_mp is None else f"MP {target.mp}/{max_mp}"
        return (f"{target.name}은(는) {self.name}을(를) 사용했다! "
                f"MP가 {restored} 회복되었다. ({mp_text})")

    def __str__(self):
        return f"{self.name} ({self.price}G) - MP {self.amount} 회복 | {self.description}"


# ---------------------------------------------------------------------------
# 2-2. Revive : 부활 아이템 (Potion 상속)
# ---------------------------------------------------------------------------
class Revive(Potion):
    """
    쓰러진(HP 0) 동료를 되살리는 아이템. 포켓몬의 '기력의 조각'과 같은 역할.
    일반 물약과 반대로 '쓰러진 대상에게만' 쓸 수 있다.

    추가 속성
        ratio : 최대 체력의 몇 % 로 되살릴지 (0.5 = 50%)
        amount: 대상에게 max_hp 가 없을 때 대신 회복시킬 고정 HP
    """

    def __init__(self, name, price, ratio=0.5, description="", fallback_heal=30):
        super().__init__(name, price, fallback_heal, description)
        if not 0 < ratio <= 1:
            raise ValueError("부활 비율(ratio)은 0보다 크고 1 이하여야 합니다.")
        self.ratio = ratio

    def check_usable(self, target):
        if target.is_alive():
            raise ItemUseError(f"{target.name}은(는) 아직 쓰러지지 않았다! {self.name}은(는) 쓰러진 동료에게만 쓸 수 있다.")

    def use(self, target):
        self.check_usable(target)
        max_hp = getattr(target, "max_hp", None)
        # max_hp 가 있으면 비율로, 없으면 고정 회복량(amount)으로 되살린다.
        # int() 결과가 0 이 되면 부활이 안 되므로 최소 1 을 보장한다.
        heal = max(1, int(max_hp * self.ratio)) if max_hp is not None else self.amount
        _restore_hp(target, heal)   # HP 0 → take_damage(-heal) → HP heal
        return f"{self.name}의 힘으로 {target.name}이(가) 다시 일어났다! ({_hp_text(target)})"

    def __str__(self):
        return (f"{self.name} ({self.price}G) - 쓰러진 동료를 최대 HP의 "
                f"{int(self.ratio * 100)}%로 부활 | {self.description}")


# ===========================================================================
# 3. Weapon : 장착형 무기
# ===========================================================================
class Weapon(Item):
    """
    장착하면 공격력(atk)이 atk_bonus 만큼 오르는 무기.
    사라지지 않는 아이템이며(consumable=False), 한 칸에 하나만 들어간다(stackable=False).

    추가 속성
        atk_bonus       : 올려주는 공격력
        allowed_classes : 장착 가능한 직업 클래스 이름들의 튜플. None 이면 모든 직업 가능
                          예) ("Warrior",)  → 두더지 전사만 장착 가능

    장착 방식
        target.weapon 에 무기를 저장하고 target.atk 를 올린다.
        이미 다른 무기를 끼고 있으면 먼저 벗기고(공격력 원상복구) 새 무기를 낀다.
        벗겨진 옛 무기는 equip() 의 반환값으로 돌려주므로,
        Inventory.use() 가 그 무기를 다시 가방에 넣어준다.
    """

    stackable = False
    consumable = False
    category = "무기"

    def __init__(self, name, price, atk_bonus, allowed_classes=None, description=""):
        super().__init__(name, price, description)
        if atk_bonus <= 0:
            raise ValueError("무기의 공격력 보너스는 1 이상이어야 합니다.")
        self.atk_bonus = atk_bonus
        # 리스트로 받아도 튜플로 바꿔 저장 → 밖에서 실수로 수정하지 못하게
        self.allowed_classes = tuple(allowed_classes) if allowed_classes else None

    def can_equip(self, target):
        """
        target 이 이 무기를 장착할 수 있는 직업인지 True/False 로 알려준다.
        type(target).__mro__ 는 '자기 클래스 + 모든 부모 클래스' 목록이다.
        그래서 Warrior 를 상속한 자식 클래스(예: 각성한 전사)도 장착할 수 있다.
        """
        if self.allowed_classes is None:
            return True
        return any(cls.__name__ in self.allowed_classes for cls in type(target).__mro__)

    def allowed_text(self):
        """'두더지 전사, 여우 궁수' 처럼 장착 가능 직업을 한글로 돌려준다."""
        if self.allowed_classes is None:
            return "모든 직업"
        return ", ".join(CLASS_DISPLAY_NAMES.get(c, c) for c in self.allowed_classes)

    def equip(self, target):
        """
        target 에게 이 무기를 장착시킨다.
        반환값: 원래 끼고 있던 무기 (없었으면 None)
        장착할 수 없으면 ItemUseError 발생 → 아무것도 바뀌지 않는다.
        """
        if not target.is_alive():
            raise ItemUseError(f"{target.name}은(는) 쓰러져 있어서 무기를 장착할 수 없다!")
        if not self.can_equip(target):
            raise ItemUseError(f"{self.name}은(는) {self.allowed_text()}만 장착할 수 있다!")

        old_weapon = getattr(target, "weapon", None)
        if old_weapon is self:
            raise ItemUseError(f"{target.name}은(는) 이미 {self.name}을(를) 장착하고 있다!")

        if old_weapon is not None:
            old_weapon.unequip(target)    # 옛 무기의 공격력 보너스를 먼저 빼준다

        target.atk += self.atk_bonus      # Unit.atk 는 public 속성이라 직접 변경 가능
        target.weapon = self
        return old_weapon

    def unequip(self, target):
        """target 이 끼고 있는 이 무기를 벗긴다. (공격력 원상복구)"""
        if getattr(target, "weapon", None) is not self:
            raise ItemUseError(f"{target.name}은(는) {self.name}을(를) 장착하고 있지 않다!")
        target.atk -= self.atk_bonus
        target.weapon = None

    def equip_message(self, target, old_weapon):
        """장착 결과 메시지를 만든다. (use() 와 Inventory.use() 가 같이 사용)"""
        msg = f"{target.name}은(는) {self.name}을(를) 장착했다! 공격력 +{self.atk_bonus} (ATK {target.atk})"
        if old_weapon is not None:
            msg += f"\n  └ 사용하던 {old_weapon.name}은(는) 가방에 넣었다."
        return msg

    def use(self, target):
        """
        Item.use() 오버라이딩: 무기를 '사용' = 장착.
        ⚠ 이 메서드를 직접 부르면 벗겨진 옛 무기가 가방으로 돌아가지 않는다.
          게임에서는 꼭 Inventory.use(번호, 캐릭터) 로 사용할 것!
        """
        old_weapon = self.equip(target)
        return self.equip_message(target, old_weapon)

    def __str__(self):
        return (f"{self.name} ({self.price}G) - 공격력 +{self.atk_bonus} "
                f"[{self.allowed_text()}] | {self.description}")


# ===========================================================================
# 4. 아이템 도감 (카탈로그) : 상점 판매 목록, 몬스터 드롭, 시작 아이템 지급용
# ===========================================================================
# 값이 '아이템 객체'가 아니라 '아이템을 만드는 함수(lambda)'인 이유:
#   같은 객체를 여러 곳에서 공유하면, 무기를 한 캐릭터가 장착했을 때
#   다른 곳의 '같은 무기'도 장착된 것처럼 꼬일 수 있다.
#   그래서 create_item() 을 부를 때마다 '새 객체'를 만들어 준다.
_ITEM_FACTORIES = {
    # ---- 회복 아이템 ----
    "small_berry": lambda: Potion(
        "작은 회복 열매", 30, 30, "숲 다람쥐들이 모아둔 새콤한 빨간 열매"),
    "big_potion": lambda: Potion(
        "큰 회복 물약", 80, 80, "토끼 약사가 달인 진한 약초 물약"),
    "mana_dew": lambda: ManaPotion(
        "마나 이슬", 40, 30, "달빛 아래 맺힌 이슬. 마력이 차오른다"),
    "phoenix_feather": lambda: Revive(
        "불사조 깃털", 200, 0.5, "쓰러진 동료를 따뜻한 불꽃으로 감싸 되살린다"),

    # ---- 공용 무기 ----
    "rusty_dagger": lambda: Weapon(
        "녹슨 단검", 20, 3, None, "던전 입구에 굴러다니던 낡은 단검"),

    # ---- 두더지 전사 (근거리) ----
    "steel_claw": lambda: Weapon(
        "강철 발톱 장갑", 100, 8, ["Warrior"], "땅굴을 파던 발톱에 강철을 덧씌웠다"),
    "mithril_claw": lambda: Weapon(
        "미스릴 굴착 발톱", 250, 15, ["Warrior"], "오우거의 갑옷도 파고드는 전설의 발톱"),

    # ---- 부엉이 마법사 (마법) ----
    "feather_staff": lambda: Weapon(
        "부엉이 깃털 지팡이", 120, 10, ["Mage"], "현자 부엉이의 깃털이 달린 지팡이"),
    "starlight_staff": lambda: Weapon(
        "별빛 수정 지팡이", 280, 18, ["Mage"], "밤하늘의 별빛을 담은 수정 지팡이"),

    # ---- 여우 궁수 (원거리) ----
    "fox_bow": lambda: Weapon(
        "여우 꼬리 단궁", 110, 9, ["Archer"], "가볍고 빠른 여우족 전통 활"),
    "wind_bow": lambda: Weapon(
        "바람 정령 장궁", 260, 16, ["Archer"], "화살이 바람을 타고 고블린을 꿰뚫는다"),
}


def create_item(item_id):
    """
    아이템 ID(문자열)로 새 아이템 객체를 만들어 돌려준다.
        예) potion = create_item("small_berry")
    없는 ID 면 ItemNotFoundError 발생.
    """
    factory = _ITEM_FACTORIES.get(item_id)
    if factory is None:
        raise ItemNotFoundError(f"'{item_id}'(이)라는 아이템은 도감에 없습니다.")
    return factory()   # lambda 를 호출 → 새 아이템 객체 생성


def get_item_ids(category=None):
    """
    도감에 있는 아이템 ID 목록을 돌려준다.
    category 를 주면 그 분류만 ("회복" 또는 "무기")
        예) 상점 진열: [create_item(i) for i in get_item_ids()]
            몬스터 드롭: random.choice(get_item_ids("회복"))
    """
    if category is None:
        return list(_ITEM_FACTORIES.keys())
    return [item_id for item_id, factory in _ITEM_FACTORIES.items()
            if factory().category == category]
