"""그래프 컨텍스트를 자연어 학습 경로/진단으로 변환 (GraphRAG의 G 단계)."""

from src.ollama_client import generate


def _fmt(node):
    rate = node.get("correctRate")
    rate_str = f"{rate:.0f}%" if rate is not None else "-"
    return f"{node['grade']} {node['label']}(정답률 {rate_str})"


def build_prompt(query, ctx):
    node = ctx["node"]
    # 선수학습 경로: 먼 레벨 → 가까운 레벨 순으로 나열 (학습 순서)
    chain = []
    for level in reversed(ctx["prereq_levels"]):
        chain.append(" · ".join(_fmt(n) for n in level))
    prereq_text = "\n".join(f"  {i+1}단계: {c}" for i, c in enumerate(chain)) or "  (선수 개념 없음 — 출발 개념)"
    succ_text = " · ".join(_fmt(n) for n in ctx["successors"]) or "(후속 개념 없음)"

    return (
        "당신은 초·중등 수학 학습 경로 안내 도우미입니다. "
        "아래는 지식 그래프에서 탐색한 '목표 개념'과 그 선수학습 경로입니다.\n\n"
        f"[학습자 요청]\n{query}\n\n"
        f"[목표 개념]\n{_fmt(node)} — 영역: {node['area']}\n\n"
        f"[선수학습 경로 (먼저 익혀야 하는 순서)]\n{prereq_text}\n\n"
        f"[이 개념 다음에 이어지는 개념]\n{succ_text}\n\n"
        "[지침]\n"
        "- 목표 개념을 배우기 위해 어떤 선수 개념을 어떤 순서로 익혀야 하는지 설명하세요.\n"
        "- 정답률이 낮은 선수 개념이 있으면 보강이 필요하다고 짚어 주세요.\n"
        "- 그래프에 없는 개념을 지어내지 말고, 위 정보 안에서만 답하세요.\n"
        "- 한국어로 교사가 바로 활용할 수 있게 간결히 답하세요.\n"
    )


def generate_answer(query, ctx):
    if ctx is None:
        return "그래프에서 관련 개념을 찾지 못했습니다."
    return generate(build_prompt(query, ctx))
