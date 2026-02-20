#!/usr/bin/env python3
"""
명언 큐레이션 멀티 에이전트 시스템 — 웹 UI

브라우저에서 요청을 입력하고, 실시간 진행 상황을 확인하며,
결과를 바로 확인할 수 있는 간단한 웹 인터페이스.

사용법:
    python web_app.py
    # 브라우저에서 http://localhost:5000 접속
"""

import asyncio
import json
import logging
import os
import sys
import threading
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agents.orchestrator import Orchestrator

app = Flask(__name__)

# 작업 상태 저장소
jobs = {}


class JobLogHandler(logging.Handler):
    """특정 작업의 로그를 캡처하는 핸들러."""

    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    def emit(self, record):
        if self.job_id in jobs:
            msg = self.format(record)
            jobs[self.job_id]["logs"].append(msg)


def setup_logging():
    """로깅을 설정한다."""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("quote-agents")
    root_logger.setLevel(log_level)
    if not root_logger.handlers:
        root_logger.addHandler(handler)


def run_pipeline_in_thread(job_id, user_request):
    """별도 스레드에서 파이프라인을 실행한다."""
    # 이 작업 전용 로그 핸들러 추가
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    log_handler = JobLogHandler(job_id)
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger("quote-agents")
    root_logger.addHandler(log_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["logs"].append(f"요청 접수: {user_request}")

        orchestrator = Orchestrator()
        start_time = datetime.now()
        result = loop.run_until_complete(orchestrator.run_pipeline(user_request))
        elapsed = datetime.now() - start_time

        # output 디렉토리에 자동 저장
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(config.OUTPUT_DIR, f"result_{timestamp}.tsv")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(result)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result
        jobs[job_id]["save_path"] = save_path
        jobs[job_id]["elapsed"] = str(elapsed)
        jobs[job_id]["logs"].append(f"완료! (소요 시간: {elapsed})")

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["logs"].append(f"오류 발생: {e}")

    finally:
        root_logger.removeHandler(log_handler)
        loop.close()


@app.route("/")
def index():
    """메인 페이지."""
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    """파이프라인 실행 요청."""
    if not config.ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY가 설정되지 않았습니다."}), 400

    data = request.get_json()
    user_request = data.get("request", "").strip()

    if not user_request:
        return jsonify({"error": "요청을 입력해주세요."}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "pending",
        "request": user_request,
        "logs": [],
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }

    thread = threading.Thread(
        target=run_pipeline_in_thread,
        args=(job_id, user_request),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    """작업 상태 조회."""
    if job_id not in jobs:
        return jsonify({"error": "작업을 찾을 수 없습니다."}), 404

    job = jobs[job_id]
    return jsonify({
        "status": job["status"],
        "logs": job["logs"],
        "result": job["result"],
        "error": job["error"],
        "elapsed": job.get("elapsed"),
        "save_path": job.get("save_path"),
    })


@app.route("/api/history")
def api_history():
    """이전 실행 기록 목록."""
    history = []
    for job_id, job in sorted(jobs.items(), key=lambda x: x[1]["created_at"], reverse=True):
        history.append({
            "job_id": job_id,
            "request": job["request"],
            "status": job["status"],
            "created_at": job["created_at"],
        })
    return jsonify(history)


if __name__ == "__main__":
    setup_logging()

    if not config.ANTHROPIC_API_KEY:
        print("경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.", file=sys.stderr)
        print("export ANTHROPIC_API_KEY='your-api-key'", file=sys.stderr)

    print("\n" + "=" * 50)
    print("  명언 큐레이션 웹 UI")
    print("  http://localhost:8080")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=8080, debug=False)
