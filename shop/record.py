"""
shop/record.py - 플레이 기록 / 랭킹 (⑤ 상점·기록 담당)

data/records.txt 에 한 줄씩 저장한다.
    날짜|이름|직업|레벨|도달층|클리어(1/0)
"""
import os
from datetime import datetime

RECORD_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "records.txt")
SEP = "|"


def save_record(name, job, floor, cleared, level=1):
    """플레이 결과 한 줄 저장. 파일 오류가 나도 게임은 멈추지 않는다."""
    name = str(name).replace(SEP, "/")
    line = SEP.join([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        name, str(job), str(level), str(floor), "1" if cleared else "0",
    ])
    try:
        os.makedirs(os.path.dirname(RECORD_FILE), exist_ok=True)
        with open(RECORD_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        print(f"  (기록 저장 실패: {e})")


def load_records():
    """저장된 기록을 딕셔너리 리스트로. 깨진 줄은 건너뛴다."""
    records = []
    try:
        with open(RECORD_FILE, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(SEP)
                if len(parts) != 6:
                    continue
                try:
                    records.append({
                        "date": parts[0], "name": parts[1], "job": parts[2],
                        "level": int(parts[3]), "floor": int(parts[4]),
                        "cleared": parts[5] == "1",
                    })
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return records


def get_ranking(limit=10):
    """클리어 > 도달층 > 레벨 순으로 정렬"""
    records = load_records()
    records.sort(key=lambda r: (r["cleared"], r["floor"], r["level"]), reverse=True)
    return records[:limit]


def show_ranking(limit=10):
    print("\n  🏆 명예의 전당 (TOP {})\n".format(limit))
    ranking = get_ranking(limit)
    if not ranking:
        print("  아직 기록이 없어요. 첫 번째 탈출자가 되어 보세요!")
        return
    print(f"  {'순위':<4}{'이름':<10}{'직업':<10}{'Lv':>4}{'층':>5}   결과     날짜")
    print("  " + "-" * 60)
    for i, r in enumerate(ranking, 1):
        result = "탈출 성공" if r["cleared"] else "실패"
        print(f"  {i:<5}{r['name']:<10}{r['job']:<10}{r['level']:>4}{r['floor']:>5}   "
              f"{result:<7}  {r['date']}")
