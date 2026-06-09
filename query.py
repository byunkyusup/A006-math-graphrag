"""GraphRAG 질의 CLI — 개념을 그래프에서 찾아 선수학습 경로 + LLM 설명 출력.

사용:
  python query.py "분수의 곱셈을 배우려면 무엇을 먼저 알아야 해?"
  python query.py --no-gen "이차방정식"
"""

import argparse
import sys

from src.generator import generate_answer
from src.graph import ConceptGraph
from src.retriever import GraphRetriever


def main():
    parser = argparse.ArgumentParser(description="수학 개념 GraphRAG")
    parser.add_argument("query", help="자연어 질의 또는 개념명")
    parser.add_argument("--no-gen", action="store_true", help="LLM 생성 생략")
    args = parser.parse_args()

    graph = ConceptGraph.load()
    retriever = GraphRetriever(graph)
    ctx = retriever.retrieve(args.query)

    if ctx is None:
        print("그래프에서 관련 개념을 찾지 못했습니다.")
        return

    node = ctx["node"]
    print(f"\n=== 목표 개념 ===\n{node['grade']} {node['label']} "
          f"(영역: {node['area']}, 정답률 {node['correctRate']:.0f}%)")

    print("\n=== 선수학습 경로 (그래프 역탐색) ===")
    if ctx["prereq_levels"]:
        for i, level in enumerate(ctx["prereq_levels"], 1):
            names = " · ".join(f"{n['grade']} {n['label']}" for n in level)
            print(f"  -{i}단계 선수: {names}")
    else:
        print("  (선수 개념 없음 — 출발 개념)")

    print("\n=== 후속 개념 ===")
    print("  " + (" · ".join(f"{n['grade']} {n['label']}" for n in ctx["successors"]) or "(없음)"))

    if args.no_gen:
        return

    print("\n=== LLM 학습 경로 안내 (Ollama) ===")
    print(generate_answer(args.query, ctx))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"[오류] {exc}. 먼저 gen_graph.py 실행 필요.", file=sys.stderr)
        sys.exit(1)
