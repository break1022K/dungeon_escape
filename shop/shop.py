"""
shop/shop.py - 상점 (⑤ 상점·기록 담당)

층 사이 캠프에서 열 수 있는 두더지 상인의 가게.
    Shop().open(player)     : 상점 화면 (사기 / 팔기)
    Shop().buy(player, id)  : 아이템 구매 (골드 부족·가방 가득 → 예외)
    Shop().sell(player, i)  : 가방 i번(0부터) 칸 아이템 1개 판매 (구매가의 절반)
"""
from core.exceptions import GameError, InventoryFullError, ItemUseError
from core.ui import clear, say, pause, ask_number, josa, LINE, THIN
from items import create_item, Weapon

# 상점 진열 목록 (items/item.py 의 아이템 ID)
DEFAULT_STOCK = [
    "small_berry", "big_potion", "mana_dew", "phoenix_feather",
    "rusty_dagger",
    "steel_claw", "mithril_claw",
    "earth_staff", "crystal_staff",
    "leather_glove", "wind_sling",
]


class Shop:
    def __init__(self, stock=None):
        self.stock = list(stock or DEFAULT_STOCK)

    # ───────── 진열 ─────────
    def items_for(self, player):
        """player 가 쓸 수 있는 아이템만 (다른 직업 전용 무기는 숨김)"""
        result = []
        for item_id in self.stock:
            item = create_item(item_id)
            if isinstance(item, Weapon) and not item.can_equip(player):
                continue
            result.append((item_id, item))
        return result

    # ───────── 사기 / 팔기 ─────────
    def buy(self, player, item_id, count=1):
        item = create_item(item_id)
        total = item.price * count
        if not player.inventory.can_add(item, count):
            raise InventoryFullError("가방에 빈 칸이 없어요!")
        player.spend_gold(total)            # 골드 부족이면 NotEnoughGoldError
        player.inventory.add(item, count)
        return f"{josa(item.name, '을/를')} {count}개 샀다! (-{total}G, 남은 골드 {player.gold}G)"

    def sell(self, player, index, count=1):
        item = player.inventory.get(index)
        if item is getattr(player, "weapon", None):
            raise ItemUseError("장착 중인 무기는 팔 수 없어요.")
        if item.sell_price <= 0:
            raise ItemUseError(f"{josa(item.name, '은/는')} 값어치가 없어서 팔 수 없어요.")
        player.inventory.remove(index, count)
        earned = item.sell_price * count
        player.earn_gold(earned)
        return f"{josa(item.name, '을/를')} {count}개 팔았다! (+{earned}G, 보유 골드 {player.gold}G)"

    # ───────── 화면 ─────────
    def _header(self, player, title):
        clear()
        print(LINE)
        print(f"  🏪 두더지 상인의 가게 - {title}")
        print(LINE)
        weapon = player.weapon.name if player.weapon else "없음"
        print(f"  보유 골드: {player.gold}G   |   장착 무기: {weapon}"
              f"   |   가방 {len(player.inventory)}/{player.inventory.max_slots}칸")
        print(THIN)

    def open(self, player):
        msg = "어서 오세요~ 던전에서 살아남으려면 준비가 필요하죠!"
        while True:
            self._header(player, "메인")
            print(f"  ▶ {msg}\n")
            print("   1. 사기")
            print("   2. 팔기")
            print("   0. 나가기")
            pick = ask_number("\n  > ", 0, 2)
            if pick == 0:
                say("  \"살아서 또 만나요~\"")
                return
            msg = self._buy_menu(player) if pick == 1 else self._sell_menu(player)

    def _buy_menu(self, player):
        goods = self.items_for(player)
        self._header(player, "사기")
        for i, (_, item) in enumerate(goods, 1):
            mark = "" if item.price <= player.gold else "  (골드 부족)"
            print(f"  {i:>2}. {item}{mark}")
        print("   0. 돌아가기")
        pick = ask_number("\n  무엇을 살까요? > ", 0, len(goods))
        if pick == 0:
            return "천천히 둘러보세요."

        item_id, item = goods[pick - 1]
        count = 1
        if item.stackable:
            max_count = max(1, player.gold // max(item.price, 1))
            count = ask_number(f"  몇 개 살까요? (1~{min(max_count, 99)}) > ", 1, min(max_count, 99))
        try:
            return self.buy(player, item_id, count)
        except GameError as e:
            return f"❌ {e}"

    def _sell_menu(self, player):
        inv = player.inventory
        if inv.is_empty():
            return "팔 물건이 없어요."
        self._header(player, "팔기")
        slots = list(inv)
        for i, (item, count) in enumerate(slots, 1):
            qty = f" x{count}" if item.stackable else ""
            print(f"  {i:>2}. {item.name}{qty}  → {item.sell_price}G")
        print("   0. 돌아가기")
        pick = ask_number("\n  무엇을 팔까요? > ", 0, len(slots))
        if pick == 0:
            return "좋은 물건 있으면 또 가져와요."
        try:
            return self.sell(player, pick - 1)
        except GameError as e:
            return f"❌ {e}"
