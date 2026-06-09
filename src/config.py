"""중앙 설정값 — Ollama 모델, 경로."""

import os

OLLAMA_HOST = "http://localhost:11434"
GEN_MODEL = "qwen2.5:3b"   # 답변 생성 (다국어, 한국어 양호)

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(_SRC_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
GRAPH_PATH = os.path.join(DATA_DIR, "graph.json")
HTML_PATH = os.path.join(PROJECT_DIR, "graph.html")
