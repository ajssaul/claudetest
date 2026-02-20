# 명언 큐레이션 멀티 에이전트 시스템

5개의 AI 에이전트가 역할별로 협업하여 세계적 대가들의 명언을 수집 → 정리 → 검수 → 최종 확인하고, 사용자에게 고품질 결과물을 전달하는 파이프라인 시스템.

## 아키텍처

```
사용자 요청
    │
    ▼
🎯 오케스트레이터 ─── 전체 파이프라인 조율 & 피드백 루프 관리
    │
    ▼
🔍 수집자 ◄──── 반려 (3→2, 4→2, 5→2)
    │
    ▼
📝 정리자 ◄──── 반려 (4→3)
    │
    ▼
🔎 검수자 ◄──── 반려 (5→4)
    │
    ▼
✅ 최종 확인자
    │
    ▼
📊 TSV 결과물
```

## 설치

```bash
pip install -r requirements.txt
export GROQ_API_KEY="your-api-key"
```

## 사용법

```bash
# 대화형 모드
python main.py

# 인자 지정
python main.py --topic "리더십" --leaders "일론 머스크,스티브 잡스" --count 10
python main.py --topic "투자 철학" --leaders "워런 버핏" --count 5 --output output/result.tsv
```

## 피드백 루프 제한

- 동일 경로 피드백: 최대 3회
- 전체 파이프라인 재시작: 최대 2회
- 전체 피드백 총 횟수: 최대 10회

한도 초과 시 현재까지 결과물과 함께 파이프라인 실행 리포트를 출력합니다.

## 프로젝트 구조

```
wisdom-curation-agents/
├── main.py                     # CLI 진입점
├── config.py                   # 설정
├── requirements.txt
├── agents/
│   ├── base_agent.py           # 공통 베이스 클래스
│   ├── orchestrator.py         # 오케스트레이터
│   ├── collector.py            # 수집자
│   ├── organizer.py            # 정리자
│   ├── reviewer.py             # 검수자
│   └── final_validator.py      # 최종 확인자
├── models/
│   ├── wisdom.py               # Wisdom 데이터 모델
│   └── task.py                 # 태스크/메시지 모델
├── tools/
│   ├── web_search.py           # 웹 검색
│   ├── youtube_search.py       # 유튜브 자막 추출
│   ├── x_search.py             # X(트위터) 검색
│   ├── book_search.py          # 도서 검색
│   └── source_validator.py     # 출처 검증
├── prompts/                    # 에이전트 시스템 프롬프트
├── guidelines/                 # 프로젝트 지침
└── output/                     # 결과물 저장
```
