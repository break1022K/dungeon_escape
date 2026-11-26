"""
main.py - 던전 탈출 실행 파일

    python main.py
"""
import sys

from game import Game


def main():
    # 윈도우 콘솔에서 이모지가 출력되지 않아도 게임이 멈추지 않도록
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    try:
        Game().run()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  게임을 종료합니다. 🐾")


if __name__ == "__main__":
    main()
