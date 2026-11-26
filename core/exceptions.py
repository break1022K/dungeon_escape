"""
core/exceptions.py - 게임 전용 예외 모음 (공통)

모든 게임 예외는 GameError 를 상속한다.
→ 전투/상점 화면에서는 `except GameError` 하나로 전부 잡아서
  메시지만 보여 주고 게임은 계속 진행할 수 있다.
"""


class GameError(Exception):
    """게임 안에서 처리할 수 있는 모든 오류의 부모 클래스"""


# ───────── 캐릭터 / 전투 ─────────
class UnitDeadError(GameError):
    """쓰러진 유닛이 행동하거나, 쓰러진 대상을 공격하려 할 때"""


class InvalidActionError(GameError):
    """지금은 할 수 없는 행동일 때 (이미 숨어 있음, 대상 없음 등)"""


class NotEnoughMPError(GameError):
    """MP 가 부족할 때"""


class NoTeethError(GameError):
    """던질 앞니가 없을 때"""


# ───────── 아이템 / 인벤토리 ─────────
class ItemUseError(GameError):
    """아이템을 지금 사용할 수 없을 때 (체력 가득, 직업 불일치 등)"""


class InventoryFullError(GameError):
    """가방에 빈 칸이 없을 때"""


class ItemNotFoundError(GameError):
    """없는 칸 번호를 고르거나, 없는 아이템을 찾을 때"""


# ───────── 상점 ─────────
class NotEnoughGoldError(GameError):
    """골드가 부족할 때"""
