"""
items/inventory.py
==================
던전 탈출(Dungeon Escape) - 인벤토리(가방) 모듈  (③ 아이템·인벤토리 담당)

[개념]
    포켓몬스터의 '가방'처럼 칸(slot) 단위로 아이템을 보관한다.
        1. 작은 회복 열매   x3      ← 물약은 한 칸에 겹쳐 쌓인다 (최대 99개)
        2. 강철 발톱 장갑           ← 무기는 한 칸에 하나씩
    칸 수에는 제한이 있다 (기본 10칸). 꽉 차면 InventoryFullError.

[다른 팀이 주로 쓰는 메서드]
    ④ 게임·전투 담당
        inventory.show()               : 가방 내용 출력 (1번부터 번호 표시)
        inventory.use(index, target)   : index 번 칸의 아이템을 target 에게 사용
                                         → 결과 메시지(str) 반환
        inventory.unequip(target)      : 장착한 무기를 벗겨 가방에 넣기
        ※ index 는 0부터 시작! 메뉴에서 받은 번호는 int(input()) - 1 로 넘겨줄 것.

    ⑤ 상점 담당
        inventory.add(item, count)     : 아이템 넣기 (구매)
        inventory.remove(index, count) : 아이템 빼기 (판매) → 뺀 아이템 반환
        inventory.can_add(item, count) : 살 수 있는지 미리 확인

[예외 처리 예시 - 전투 담당 참고용]
    try:
        print(inventory.use(choice - 1, player))
    except (ItemUseError, ItemNotFoundError) as e:
        print(e)          # 턴을 소모하지 않고 다시 고르게 하면 된다
"""

from items.item import (
    Item,
    Weapon,
    ItemUseError,
    InventoryFullError,
    ItemNotFoundError,
)


# ===========================================================================
# InventorySlot : 가방의 '한 칸'
# ===========================================================================
class InventorySlot:
    """
    가방 한 칸. 아이템 하나와 그 개수를 함께 들고 있다.
    (물약은 같은 종류끼리 상태가 똑같으므로 객체 하나 + 개수로 표현해도 충분하다)
    Inventory 안에서만 쓰는 보조 클래스.
    """

    MAX_STACK = 99   # 한 칸에 겹쳐 쌓을 수 있는 최대 개수

    def __init__(self, item, count=1):
        self.item = item
        self.count = count

    @property
    def space_left(self):
        """이 칸에 더 쌓을 수 있는 개수. 겹치지 않는 아이템(무기)은 항상 0."""
        if not self.item.stackable:
            return 0
        return self.MAX_STACK - self.count

    def __str__(self):
        # 물약처럼 쌓이는 아이템만 'x3' 표시
        if self.item.stackable:
            return f"{self.item.name} x{self.count}"
        return self.item.name


# ===========================================================================
# Inventory : 가방
# ===========================================================================
class Inventory:
    """
    아이템을 칸(slot) 단위로 보관하는 가방.

    속성
        max_slots : 최대 칸 수
        __slots   : InventorySlot 리스트 (private → 밖에서 직접 못 건드리게 캡슐화)
                    ※ 파이썬 특수 문법 __slots__ 와는 관계없는 그냥 변수 이름이다.
    """

    DEFAULT_MAX_SLOTS = 10

    def __init__(self, max_slots=DEFAULT_MAX_SLOTS):
        if max_slots <= 0:
            raise ValueError("인벤토리 칸 수는 1 이상이어야 합니다.")
        self.max_slots = max_slots
        self.__slots = []

    # -----------------------------------------------------------------------
    # 상태 확인용 메서드 / 프로퍼티
    # -----------------------------------------------------------------------
    def __len__(self):
        """len(inventory) → 사용 중인 칸 수"""
        return len(self.__slots)

    def __iter__(self):
        """
        for item, count in inventory:  처럼 반복문에 바로 쓸 수 있게 해준다.
        (아이템, 개수) 튜플을 하나씩 돌려준다.
        """
        for slot in self.__slots:
            yield slot.item, slot.count

    @property
    def free_slots(self):
        """남은 빈 칸 수"""
        return self.max_slots - len(self.__slots)

    def is_full(self):
        return self.free_slots == 0

    def is_empty(self):
        return len(self.__slots) == 0

    def _get_slot(self, index):
        """
        index 번 칸을 꺼낸다. (0부터 시작)
        범위를 벗어나면 IndexError 대신 이해하기 쉬운 ItemNotFoundError 를 발생시킨다.
        음수 index(-1 = 마지막) 는 메뉴 입력 실수일 가능성이 높아 막는다.
        """
        if not isinstance(index, int) or not 0 <= index < len(self.__slots):
            raise ItemNotFoundError(f"{index + 1 if isinstance(index, int) else index}번 칸에는 아이템이 없다!")
        return self.__slots[index]

    def get(self, index):
        """index 번 칸의 아이템 객체를 돌려준다. (가방에서 빼지는 않음)"""
        return self._get_slot(index).item

    def count(self, name):
        """이름이 name 인 아이템이 가방에 총 몇 개 있는지 (여러 칸에 나뉘어 있어도 합산)"""
        return sum(slot.count for slot in self.__slots if slot.item.name == name)

    def has_item(self, name):
        return self.count(name) > 0

    def find_index(self, name):
        """
        이름으로 아이템이 들어있는 첫 번째 칸 번호(0부터)를 찾는다.
        없으면 ItemNotFoundError.
            예) idx = inventory.find_index("작은 회복 열매")
        """
        for i, slot in enumerate(self.__slots):
            if slot.item.name == name:
                return i
        raise ItemNotFoundError(f"가방에 {name}이(가) 없다!")

    # -----------------------------------------------------------------------
    # 넣기 / 빼기
    # -----------------------------------------------------------------------
    def can_add(self, item, count=1):
        """
        item 을 count 개 넣을 공간이 있는지 True/False 로 알려준다.
        (상점에서 구매 전에 미리 확인할 때 유용)
        """
        if not item.stackable:
            return self.free_slots >= count

        # 쌓이는 아이템: '기존 같은 칸의 남은 공간' + '빈 칸 수 x 최대 스택'
        room = sum(slot.space_left for slot in self.__slots
                   if slot.item.is_same_kind(item))
        room += self.free_slots * InventorySlot.MAX_STACK
        return room >= count

    def add(self, item, count=1):
        """
        가방에 item 을 count 개 넣는다.
        - 물약: 같은 종류가 있는 칸에 먼저 쌓고, 넘치면 새 칸을 만든다.
        - 무기: 항상 새 칸에 하나씩 (count 는 1만 허용)
        - 공간이 부족하면 InventoryFullError 발생 → 하나도 넣지 않는다 (전부 or 전무)
        반환값: 결과 메시지(str)
        """
        # 1) 잘못된 입력 검사
        if not isinstance(item, Item):
            raise TypeError("Item 객체만 인벤토리에 넣을 수 있습니다.")
        if count < 1:
            raise ValueError("넣을 개수는 1 이상이어야 합니다.")
        if not item.stackable and count != 1:
            # 같은 무기 객체를 여러 칸에 넣으면 장착 상태가 꼬이므로 막는다.
            raise ValueError("겹치지 않는 아이템(무기)은 한 번에 하나씩 넣어주세요.")

        # 2) 공간 확인을 '먼저' 해서, 일부만 들어가는 상황을 막는다
        if not self.can_add(item, count):
            raise InventoryFullError(f"가방이 가득 차서 {item.name}을(를) 넣을 수 없다!")

        # 3) 실제로 넣기
        remaining = count
        if item.stackable:
            # 3-1) 이미 있는 같은 종류 칸에 채워 넣기
            for slot in self.__slots:
                if remaining == 0:
                    break
                if slot.item.is_same_kind(item) and slot.space_left > 0:
                    put = min(slot.space_left, remaining)
                    slot.count += put
                    remaining -= put
        # 3-2) 남은 것은 새 칸에 (무기는 여기서 바로 한 칸 생성)
        while remaining > 0:
            put = min(InventorySlot.MAX_STACK, remaining) if item.stackable else 1
            self.__slots.append(InventorySlot(item, put))
            remaining -= put

        suffix = f" x{count}" if item.stackable else ""
        return f"{item.name}{suffix}을(를) 가방에 넣었다."

    def remove(self, index, count=1):
        """
        index 번 칸에서 아이템을 count 개 뺀다. 칸이 비면 칸 자체를 없앤다.
        반환값: 뺀 아이템 객체 (상점 판매 시 가격 계산 등에 사용)
        """
        slot = self._get_slot(index)
        if count < 1:
            raise ValueError("뺄 개수는 1 이상이어야 합니다.")
        if count > slot.count:
            raise ItemNotFoundError(f"{slot.item.name}은(는) {slot.count}개밖에 없다!")

        slot.count -= count
        if slot.count == 0:
            self.__slots.pop(index)   # 빈 칸 정리 → 뒤 칸들의 번호가 하나씩 당겨진다
        return slot.item

    # -----------------------------------------------------------------------
    # 사용 / 장착 해제
    # -----------------------------------------------------------------------
    def use(self, index, target):
        """
        index 번 칸의 아이템을 target(캐릭터)에게 사용한다.  ★ 전투 담당 핵심 메서드
        반환값: 화면에 출력할 결과 메시지(str)

        - 사용에 실패하면(ItemUseError) 아이템은 줄어들지 않는다.
          → 아이템의 use()/equip() 가 먼저 성공해야만 가방에서 빼기 때문.
        - 무기는 '장착'되고, 원래 끼던 무기는 가방으로 돌아온다.
        """
        item = self.get(index)

        if isinstance(item, Weapon):
            # 무기: 장착 → 가방에서 빼기 → 옛 무기 넣기
            old_weapon = item.equip(target)   # 실패 시 여기서 예외, 가방은 그대로
            self.remove(index)                # 한 칸이 비었으므로
            if old_weapon is not None:
                self.add(old_weapon)          # 옛 무기는 항상 들어갈 자리가 있다
            return item.equip_message(target, old_weapon)

        # 물약 등 일반 아이템: 다형성(polymorphism) - 종류에 맞는 use() 가 호출된다
        message = item.use(target)
        if item.consumable:
            self.remove(index)
        return message

    def unequip(self, target):
        """
        target 이 장착 중인 무기를 벗겨서 가방에 넣는다.
        반환값: 결과 메시지(str)
        """
        weapon = getattr(target, "weapon", None)
        if weapon is None:
            raise ItemUseError(f"{target.name}은(는) 장착한 무기가 없다!")
        if self.is_full():
            # 벗기기 '전에' 확인해야 무기가 허공으로 사라지지 않는다
            raise InventoryFullError("가방이 가득 차서 무기를 벗을 수 없다!")

        weapon.unequip(target)
        self.add(weapon)
        return f"{target.name}은(는) {weapon.name}을(를) 벗어 가방에 넣었다. (ATK {target.atk})"

    # -----------------------------------------------------------------------
    # 정리 / 출력
    # -----------------------------------------------------------------------
    def sort(self):
        """분류(회복 → 무기 → 기타) 순, 같은 분류 안에서는 이름순으로 정렬한다."""
        order = {"회복": 0, "무기": 1}
        self.__slots.sort(key=lambda s: (order.get(s.item.category, 9), s.item.name))

    def get_usable_indexes(self, category=None):
        """
        조건에 맞는 칸 번호(0부터) 리스트를 돌려준다.
            예) 전투 중 물약만 보여주고 싶을 때: inventory.get_usable_indexes("회복")
        """
        return [i for i, slot in enumerate(self.__slots)
                if category is None or slot.item.category == category]

    def __str__(self):
        """
        print(inventory) 했을 때 보이는 가방 모습.
        화면에는 사람이 보기 편하게 1번부터 번호를 붙인다.
        """
        lines = [f"🎒 가방 ({len(self.__slots)}/{self.max_slots}칸)"]
        if self.is_empty():
            lines.append("  (텅 비어 있다)")
        for i, slot in enumerate(self.__slots, start=1):
            lines.append(f"  {i}. [{slot.item.category}] {slot}")
        return "\n".join(lines)

    def show(self):
        """가방 내용을 화면에 출력한다."""
        print(self)


# ===========================================================================
# 단독 테스트 :  프로젝트 최상위 폴더(dungeon_escape/)에서
#               python -m items.inventory   로 실행
# (게임 본편에서 import 할 때는 이 부분이 실행되지 않는다)
# ※ 실행 시 "RuntimeWarning: 'items.inventory' found in sys.modules ..." 경고가
#   한 줄 나올 수 있는데, items/__init__.py 가 이 파일을 먼저 import 해서 생기는
#   것일 뿐 동작에는 문제없다.
# ===========================================================================
if __name__ == "__main__":
    from core.unit import Unit
    from items.item import create_item

    # 캐릭터 담당 코드가 아직 없어도 테스트할 수 있도록 간단한 가짜 캐릭터를 만든다.
    class Warrior(Unit):
        def __init__(self, name):
            super().__init__(name, hp=100, atk=12)
            self.max_hp = 100
            self.weapon = None

        def attack(self, target):
            target.take_damage(self.atk)

    class Mage(Unit):
        def __init__(self, name):
            super().__init__(name, hp=70, atk=15)
            self.max_hp = 70
            self.mp, self.max_mp = 10, 50
            self.weapon = None

        def attack(self, target):
            target.take_damage(self.atk)

    mole = Warrior("두더지 전사 두두")
    owl = Mage("부엉이 마법사 부엉")
    bag = Inventory()

    print(bag.add(create_item("small_berry"), 3))
    print(bag.add(create_item("mana_dew"), 2))
    print(bag.add(create_item("phoenix_feather")))
    print(bag.add(create_item("steel_claw")))
    print(bag.add(create_item("mithril_claw")))
    print(bag.add(create_item("feather_staff")))
    bag.show()

    print("\n--- 오크에게 맞았다! ---")
    mole.take_damage(50)
    print(bag.use(bag.find_index("작은 회복 열매"), mole))

    print("\n--- 체력이 가득한데 물약 사용 (실패해야 함) ---")
    mole.take_damage(-100)   # 테스트용 풀피 만들기
    try:
        bag.use(bag.find_index("작은 회복 열매"), mole)
    except ItemUseError as e:
        print("⚠", e)

    print("\n--- 무기 장착 / 교체 ---")
    print(bag.use(bag.find_index("강철 발톱 장갑"), mole))
    print(bag.use(bag.find_index("미스릴 굴착 발톱"), mole))
    try:
        bag.use(bag.find_index("부엉이 깃털 지팡이"), mole)   # 직업 불일치
    except ItemUseError as e:
        print("⚠", e)

    print("\n--- 마나 회복 / 부활 ---")
    print(bag.use(bag.find_index("마나 이슬"), owl))
    owl.take_damage(999)     # 오우거의 일격!
    print(f"{owl.name} 쓰러짐? {not owl.is_alive()}")
    print(bag.use(bag.find_index("불사조 깃털"), owl))

    print("\n--- 무기 해제 ---")
    print(bag.unequip(mole))

    print()
    bag.sort()
    bag.show()
