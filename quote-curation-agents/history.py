"""
이전 실행 결과를 로드하여 중복 명언을 방지한다.
output/ 디렉토리의 TSV 파일들을 읽어 기존 명언 목록을 반환한다.
"""

import csv
import glob
import logging
import os

import config

logger = logging.getLogger("quote-agents.history")


def load_previous_wisdoms() -> list[dict]:
    """
    output/ 디렉토리의 모든 TSV 파일에서 이전 명언을 로드한다.

    Returns:
        이전에 최종 출력된 명언 딕셔너리 리스트
    """
    output_dir = config.OUTPUT_DIR
    if not os.path.isdir(output_dir):
        return []

    tsv_files = sorted(glob.glob(os.path.join(output_dir, "*.tsv")))
    if not tsv_files:
        return []

    all_wisdoms = []
    seen_keys = set()

    for tsv_path in tsv_files:
        try:
            with open(tsv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    if not row.get("wisdom_original"):
                        continue
                    # 중복 방지 키: 원문 앞 100자
                    dedup_key = row["wisdom_original"].strip().lower()[:100]
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)
                    all_wisdoms.append(dict(row))
        except Exception as e:
            logger.warning(f"TSV 로드 실패 ({tsv_path}): {e}")
            continue

    logger.info(f"이전 명언 {len(all_wisdoms)}개 로드 (파일 {len(tsv_files)}개)")
    return all_wisdoms
