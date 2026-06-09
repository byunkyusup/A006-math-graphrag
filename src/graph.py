"""개념 선수학습 지식 그래프 자료구조 + 탐색.

방향: link.source(선수 개념) → link.target(후속 개념).
즉 source를 알아야 target을 배울 수 있다.
"""

import json
from collections import defaultdict, deque

from src import config


class ConceptGraph:
    def __init__(self, data):
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.links = data["links"]
        self.succ = defaultdict(list)  # 선수 → 후속 (다음에 배우는 것)
        self.pred = defaultdict(list)  # 후속 → 선수 (먼저 배워야 하는 것)
        for link in self.links:
            self.succ[link["source"]].append(link["target"])
            self.pred[link["target"]].append(link["source"])

    @classmethod
    def load(cls, path=None):
        with open(path or config.GRAPH_PATH, encoding="utf-8") as f:
            return cls(json.load(f))

    def degree(self, node_id):
        return len(self.succ[node_id]) + len(self.pred[node_id])

    def ancestors_by_level(self, node_id, max_depth=4):
        """선수학습 개념을 깊이(레벨)별로 반환. level 1 = 직전 선수, 2 = 그 이전 …"""
        levels = []
        seen = {node_id}
        frontier = [node_id]
        for _ in range(max_depth):
            nxt = []
            for nid in frontier:
                for p in self.pred[nid]:
                    if p not in seen:
                        seen.add(p)
                        nxt.append(p)
            if not nxt:
                break
            levels.append(nxt)
            frontier = nxt
        return levels  # [[level1...], [level2...], ...]

    def successors(self, node_id):
        """이 개념을 배운 뒤 이어지는 후속 개념(직속)."""
        return list(self.succ[node_id])

    def area_members(self, area):
        return [n for n in self.nodes.values() if n["area"] == area]
