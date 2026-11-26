"""
core/ui.py - 화면 출력 / 입력 도우미 (공통)

모든 모듈이 print 대신 say() 를 쓰면 메시지가 한 줄씩 천천히 나와서
전투 상황을 읽기 쉬워진다.

환경 변수
    DUNGEON_TEXT_DELAY : 메시지 사이 대기 시간(초). 기본 0.35, 0 이면 대기 없음
    DUNGEON_NO_CLEAR   : 값이 있으면 화면 지우기를 하지 않음 (테스트/디버깅용)
"""
import os
import time

try:
    TEXT_DELAY = float(os.environ.get("DUNGEON_TEXT_DELAY", "0.35"))
except ValueError:
    TEXT_DELAY = 0.35

LINE = "=" * 56
THIN = "-" * 56


def clear():
    """화면 지우기"""
    if os.environ.get("DUNGEON_NO_CLEAR"):
        print()
        return
    os.system("cls" if os.name == "nt" else "clear")


def say(text="", delay=None):
    """메시지 한 줄 출력 후 잠깐 대기"""
    print(text)
    wait = TEXT_DELAY if delay is None else delay
    if wait > 0:
        time.sleep(wait)


def pause(message="Enter를 눌러 계속"):
    input(f"\n  ({message})")


def ask_number(prompt, lo, hi):
    """lo ~ hi 사이 숫자를 입력받을 때까지 반복"""
    while True:
        s = input(prompt).strip()
        if s.isdigit() and lo <= int(s) <= hi:
            return int(s)
        print(f"  {lo}~{hi} 사이 숫자를 입력하세요.")


def ask_yes_no(prompt):
    return input(prompt).strip().lower() in ("y", "yes", "ㅛ", "예", "네")


# 영문자/숫자를 한국어로 읽을 때 받침이 있는 것 (L=엘, M=엠, N=엔, R=알, 0=영, 1=일 ...)
_BATCHIM_CHARS = set("LMNRlmnr013678")


def josa(word, pair):
    """josa('고블린', '이/가') -> '고블린이', josa('오크 A', '은/는') -> '오크 A는'"""
    with_b, without_b = pair.split("/")
    last = word.rstrip()[-1:] if word else ""
    if "가" <= last <= "힣":
        has_batchim = (ord(last) - 0xAC00) % 28 > 0
    elif last.isascii() and last.isalnum():
        has_batchim = last in _BATCHIM_CHARS
    else:
        return f"{word}{with_b}({without_b})"
    return word + (with_b if has_batchim else without_b)


def hp_bar(cur, mx, length=20):
    """███░░░ 모양의 막대"""
    mx = max(mx, 1)
    filled = min(length, round(length * cur / mx))
    if cur > 0:
        filled = max(filled, 1)          # 살아 있으면 최소 1칸
    return "█" * filled + "░" * (length - filled)
