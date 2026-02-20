#!/usr/bin/env python3
"""
명언 큐레이션 멀티 에이전트 시스템 — 진입점 (CLI)

5개의 AI 에이전트가 역할별로 협업하여 세계적 대가들의 명언을
수집 → 정리 → 검수 → 최종 확인하고, 사용자에게 고품질 결과물을 전달한다.

사용법:
    python main.py
    python main.py --topic "리더십" --leaders "일론 머스크,스티브 잡스" --count 10
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agents.orchestrator import Orchestrator


def setup_logging():
    """로깅을 설정한다."""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("wisdom-agents")
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def parse_args():
    """커맨드라인 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="명언 큐레이션 멀티 에이전트 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py
  python main.py --topic "리더십" --count 10
  python main.py --topic "투자 철학" --leaders "워런 버핏,레이 달리오" --count 5
  python main.py --topic "리더십" --leaders "일론 머스크,스티브 잡스" --count 10
        """,
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="명언 주제 (예: '리더십', '투자 철학')",
    )
    parser.add_argument(
        "--leaders",
        type=str,
        default=None,
        help="인물 목록 (쉼표 구분, 예: '일론 머스크,스티브 잡스')",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="요청 명언 개수 (기본: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="결과물 저장 파일 경로 (지정하지 않으면 stdout 출력)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="사용할 Gemini 모델 (기본: gemini-2.0-flash)",
    )
    return parser.parse_args()


def build_request_from_args(args) -> str:
    """커맨드라인 인자로부터 사용자 요청 문자열을 구성한다."""
    if args.topic is None:
        return ""

    parts = []
    if args.leaders:
        leaders = args.leaders.split(",")
        leaders_str = "와 ".join(l.strip() for l in leaders)
        parts.append(f"{leaders_str}의")
    parts.append(f"{args.topic} 명언")
    if args.count:
        parts.append(f"{args.count}개")
    else:
        parts.append("10개")

    return " ".join(parts)


async def run():
    """메인 실행 함수."""
    setup_logging()
    args = parse_args()

    # API 키 확인
    if not config.GEMINI_API_KEY:
        print("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.", file=sys.stderr)
        print("export GEMINI_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)

    # 모델 설정 오버라이드
    if args.model:
        config.DEFAULT_MODEL = args.model

    # 사용자 요청 구성
    user_request = build_request_from_args(args)

    if not user_request:
        # 대화형 모드
        print("=" * 60)
        print("  명언 큐레이션 멀티 에이전트 시스템")
        print("=" * 60)
        print()
        print("명언 요청을 입력하세요.")
        print("예: 일론 머스크와 스티브 잡스의 리더십 명언 10개")
        print("예: 투자 철학 명언 5개")
        print("예: 워런 버핏의 비즈니스 명언 20개")
        print()
        user_request = input("요청> ").strip()

        if not user_request:
            print("요청이 입력되지 않았습니다.")
            sys.exit(0)

    print(f"\n요청 접수: {user_request}\n")
    print("-" * 60)

    # 오케스트레이터 실행
    orchestrator = Orchestrator()

    start_time = datetime.now()
    result = await orchestrator.run_pipeline(user_request)
    elapsed = datetime.now() - start_time

    print("-" * 60)
    print(f"\n실행 시간: {elapsed}\n")

    # 결과 출력
    if args.output:
        # 파일로 저장
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"결과가 {args.output}에 저장되었습니다.")
    else:
        # stdout 출력
        print("```")
        print(result)
        print("```")

    # output 디렉토리에도 자동 저장
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_save_path = os.path.join(config.OUTPUT_DIR, f"result_{timestamp}.tsv")
    with open(auto_save_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\n자동 저장: {auto_save_path}")


def main():
    """동기 진입점."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
