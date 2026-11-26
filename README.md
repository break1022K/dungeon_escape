# 🐾 Dungeon Escape - 두더지 원정대

오크 대족장에게 붙잡힌 두더지가 5층 던전을 파고 내려가 탈출하는 턴제 RPG입니다.

## 실행 방법

```bash
cd dungeon_escape
python main.py
```

Python 3.8 이상, 외부 라이브러리 필요 없음.

| 환경 변수 | 설명 |
|---|---|
| `DUNGEON_TEXT_DELAY` | 메시지 사이 대기 시간(초). 기본 0.35, `0` 이면 즉시 출력 |
| `DUNGEON_NO_CLEAR` | 값이 있으면 화면을 지우지 않음 (디버깅용) |

## 게임 방법

- **직업**: 발톱 전사(튼튼함) / 흙마법사(MP·지진) / 앞니 투척수(앞니 4개)
- **전투 행동**: 발톱 할퀴기 · 앞니 던지기(1.5배) · 땅속 숨기(다음 공격 회피) · 특수 기술 · 가방 · 도망
- 층의 몬스터를 모두 쓰러뜨리면 다음 층으로. 내려갈 때 앞니 재생, HP 30%·MP 50% 회복
- 5층 보스 **오크 대족장**을 쓰러뜨리면 탈출 성공. 결과는 `data/records.txt` 랭킹에 저장
- 캠프의 상점에서 물약·직업 전용 무기 구매. **불사조 깃털**은 쓰러질 때 자동 부활

## 폴더 구조

```
dungeon_escape/
├── main.py                  # ④ 실행 시작점 (python main.py)
├── README.md                # 팀 전체: 팀원/역할, 실행 방법
│
├── core/                    # 공통 (강사 제공, 수정 시 팀 합의)
│   ├── __init__.py
│   ├── unit.py              # Unit 부모 클래스
│   ├── exceptions.py        # 사용자 정의 예외 모음 (GameError 상속)
│   └── ui.py                # 화면/입력 도우미 (say, ask_number, josa ...)
│
├── characters/              # ① 캐릭터 담당
│   ├── __init__.py
│   └── player.py            # 발톱 전사, 흙마법사, 앞니 투척수
│
├── monsters/                # ② 몬스터 담당
│   ├── __init__.py
│   └── monster.py           # Goblin, Orc, Ogre, Boss, create_monsters(floor)
│
├── items/                   # ③ 아이템·인벤토리 담당
│   ├── __init__.py
│   ├── item.py              # Item, Potion, ManaPotion, Revive, Weapon
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