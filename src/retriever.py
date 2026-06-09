"""GraphRAG 검색 — 질의를 개념 노드에 매칭하고, 그래프를 탐색해 컨텍스트 서브그래프를 모은다.

Hybrid RAG가 '독립 문서'를 검색한다면, 여기서는 매칭된 개념을 기점으로
선수학습 경로(조상) + 후속 개념(자식) + 동일 영역 형제를 그래프에서 끌어온다.
"""

import re

_TOK = re.compile(r"[0-9]+|[a-zA-Z]+|[가-힣]+")


def _tokens(text):
    out = set()
    for t in _TOK.findall(text.lower()):
        out.add(t)
        if "가" <= t[0] <= "힣" and len(t) > 2:
            out.update(t[i:i + 2] for i in range(len(t) - 1))
    return out


class GraphRetriever:
    def __init__(self, graph):
        self.g = graph

    def match_node(self, query):
        """질의와 토큰 겹침이 가장 큰 개념 노드 id를 반환 (없으면 None)."""
        qt = _tokens(query)
        best, best_score = None, 0
        for nid, n in self.g.nodes.items():
            text = f"{n['label']} {n['area']} {n['grade']} {' '.join(n.get('keywords', []))}"
            score = len(qt & _tokens(text))
            # 학년 표기가 질의에 있으면 가산
            if n["grade"] in query:
                score += 2
            if score > best_score:
                best, best_score = nid, score
        return best if best_score > 0 else None

    def retrieve(self, query):
        """매칭 노드 기준으로 GraphRAG 컨텍스트(dict) 구성."""
        nid = self.match_node(query)
        if nid is None:
            return None
        node = self.g.nodes[nid]
        levels = self.g.ancestors_by_level(nid)
        return {
            "node": node,
            "prereq_levels": [[self.g.nodes[i] for i in lv] for lv in levels],
            "successors": [self.g.nodes[i] for i in self.g.successors(nid)],
            "area_siblings": [
                n for n in self.g.area_members(node["area"]) if n["id"] != nid
            ][:6],
        }
