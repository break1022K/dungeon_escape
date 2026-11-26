"""
core/unit.py - 모든 캐릭터/몬스터의 부모 클래스 (공통)

[팀 약속]
    name     : 이름
    hp       : 현재 HP (property, 0 ~ max_hp 로 자동 제한)
    max_hp   : 최대 HP
    atk      : 공격력
    defense  : 방어력 (받는 피해에서 빼 줌, 최소 1 피해)
    is_alive()            : 살아 있으면 True
    take_damage(amount)   : 방어력 적용 후 피해 → 실제 피해량 반환
    heal(amount)          : 회복 → 실제 회복량 반환 (쓰러진 유닛도 가능 = 부활)
    strike(target, power) : target 에게 power 로 공격하고 피해 메시지 출력
    attack(target)        : 기본 공격 (자식 클래스가 반드시 구현)
"""
from abc import ABC, abstractmethod

from core.ui import say


class Unit(ABC):
    def __init__(self, name, hp, atk, defense=0):
        if hp <= 0:
            raise ValueError("HP는 1 이상이어야 합니다.")
        self.name = name
        self.max_hp = int(hp)
        self.__hp = int(hp)              # [캡슐화] hp property 로만 접근
        self.atk = int(atk)
        self.defense = int(defense)

    # ───────── HP ─────────
    @property
    def hp(self):
        return self.__hp

    @hp.setter
    def hp(self, value):
        self.__hp = max(0, min(int(value), self.max_hp))

    def is_alive(self):
        return self.__hp > 0

    def take_damage(self, amount):
        """방어력을 뺀 만큼 HP 감소 (최소 1). 실제로 들어간 피해량을 반환."""
        damage = max(1, int(amount) - self.defense)
        self.hp -= damage
        return damage

    def heal(self, amount):
        """HP 회복 (최대 HP 초과 불가). 실제 회복량을 반환."""
        before = self.__hp
        self.hp = before + max(0, int(amount))
        return self.__hp - before

    # ───────── 공격 ─────────
    def strike(self, target, power):
        """target.take_damage 를 부르고 결과를 화면에 보여 준다."""
        damage = target.take_damage(power)
        if damage > 0:
            say(f"   → {target.name}에게 {damage}의 피해! "
                f"(HP {target.hp}/{target.max_hp})")
        return damage

    @abstractmethod
    def attack(self, target):
        """기본 공격. 준 피해량(int)을 반환한다."""

    def __str__(self):
        return f"{self.name} (HP {self.hp}/{self.max_hp}, 공격 {self.atk}, 방어 {self.defense})"
