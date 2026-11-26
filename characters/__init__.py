# characters/__init__.py
# 이 파일이 있어야 characters 폴더를 "패키지"로 인식해서 import할 수 있어요.
# 다른 팀원은 이렇게 짧게 불러 쓰면 돼요.
#   from characters import Warrior, Mage, Archer, create_player

from characters.player import Player, Warrior, Mage, Archer, create_player, JOBS

__all__ = ["Player", "Warrior", "Mage", "Archer", "create_player", "JOBS"]