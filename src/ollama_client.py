"""로컬 Ollama HTTP API 클라이언트 (stdlib urllib)."""

import json
import urllib.request
import urllib.error

from src import config


def _post(path, payload, timeout=300):
    url = config.OLLAMA_HOST + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama 호출 실패 ({url}). `ollama serve` 실행 여부를 확인하세요. 원인: {exc}"
        ) from exc


def generate(prompt, temperature=0.3):
    result = _post("/api/generate", {
        "model": config.GEN_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    })
    return result.get("response", "").strip()
