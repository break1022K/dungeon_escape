```
dungeon_escape/
├── main.py                  # ④ 실행 시작점 (python main.py)
├── README.md                # 팀 전체: 팀원/역할, 실행 방법
│
├── core/                    # 공통 (강사 제공, 수정 시 팀 합의)
│   ├── __init__.py
│   ├── unit.py              # Unit 부모 클래스
│   └── exceptions.py        # 사용자 정의 예외 모음
│
├── characters/              # ① 캐릭터 담당
│   ├── __init__.py
│   └── player.py            # Warrior, Mage, Archer
│
├── monsters/                # ② 몬스터 담당
│   ├── __init__.py
│   └── monster.py           # Slime, Goblin, Boss, create_monsters(floor)
│
├── items/                   # ③ 아이템·인벤토리 담당
│   ├── __init__.py
│   ├── item.py              # Item, Potion, Weapon
│   └── inventory.py         # Inventory
│
├── game/                    # ④ 게임 진행·전투 담당
│   ├── __init__.py
│   ├── game.py              # Game (메뉴, 층 이동, 통합)
│   └── battle.py            # Battle (턴제 전투 루프)
│
├── shop/                    # ⑤ 상점·기록 담당 (5인 팀만)
│   ├── __init__.py
│   ├── shop.py              # Shop
│   └── record.py            # 플레이 기록, 랭킹
│
└── data/                    # ⑤ (5인 팀만)
    └── records.txt          # 랭킹 저장 파일
```