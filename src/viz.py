"""graph.json → 자가완결 Obsidian풍 인터랙티브 그래프 HTML 생성.

force-graph(CDN, 2D canvas)로 다크 테마 force-directed 그래프를 그린다.
- 영역(area)별 노드 색상, 차수 기반 노드 크기
- hover: 노드+이웃 강조, 나머지 디밍
- click / 검색: 해당 개념의 선수학습 조상 경로를 금색으로 강조 + 상세 패널
"""

import json

from src import config

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>수학 개념 지식 그래프 · GraphRAG</title>
<script src="https://unpkg.com/force-graph@1.43.5/dist/force-graph.min.js"></script>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: #0c0d12;
    font-family: -apple-system, "Apple SD Gothic Neo", "Pretendard", sans-serif; color: #e6e8ef; }
  #graph { position: fixed; inset: 0; }
  .ui { position: fixed; z-index: 10; }
  #title { top: 18px; left: 20px; max-width: 360px; pointer-events: none; }
  #title h1 { margin: 0; font-size: 17px; letter-spacing: .3px; }
  #title p { margin: 4px 0 0; font-size: 12px; color: #8b90a3; line-height: 1.5; }
  #search { top: 18px; right: 20px; }
  #search input { width: 230px; padding: 9px 12px; border-radius: 9px; border: 1px solid #2a2d3a;
    background: #15161e; color: #e6e8ef; font-size: 13px; outline: none; }
  #search input:focus { border-color: #ffcf5c; }
  #legend { bottom: 16px; left: 20px; display: flex; flex-wrap: wrap; gap: 6px 14px; max-width: 60vw; }
  #legend span { font-size: 11.5px; color: #aeb3c4; display: flex; align-items: center; gap: 6px; }
  #legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  #panel { bottom: 16px; right: 20px; width: 290px; padding: 16px 18px; border-radius: 12px;
    background: rgba(20,22,30,.92); border: 1px solid #262a38; backdrop-filter: blur(6px);
    display: none; }
  #panel h2 { margin: 0 0 2px; font-size: 16px; }
  #panel .meta { font-size: 12px; color: #8b90a3; margin-bottom: 10px; }
  #panel .row { font-size: 12.5px; margin: 5px 0; }
  #panel .row b { color: #ffcf5c; font-weight: 600; }
  #panel .chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 4px; }
  #panel .chip { font-size: 11px; padding: 2px 8px; border-radius: 20px; background: #20232f; color: #c7cbda; }
  #hint { bottom: 16px; right: 20px; font-size: 11.5px; color: #6a6f82; }
</style>
</head>
<body>
<div id="graph"></div>
<div class="ui" id="title">
  <h1>수학 개념 지식 그래프</h1>
  <p>AIHub #27752 · 선수학습 GraphRAG · 화살표는 <b>선수 → 후속</b> 방향.
     개념을 검색하거나 노드를 클릭하면 <b>선수학습 경로</b>가 강조됩니다.</p>
</div>
<div class="ui" id="search"><input id="q" placeholder="개념 검색 (예: 분수의 곱셈)" autocomplete="off" /></div>
<div class="ui" id="legend"></div>
<div class="ui" id="hint">노드 클릭 → 선수 경로 강조 · 휠로 확대/축소</div>
<div class="ui" id="panel"></div>

<script>
const DATA = __DATA__;

// 인접 맵
const succ = {}, pred = {};
DATA.links.forEach(l => {
  const s = typeof l.source === 'object' ? l.source.id : l.source;
  const t = typeof l.target === 'object' ? l.target.id : l.target;
  (succ[s] = succ[s] || []).push(t);
  (pred[t] = pred[t] || []).push(s);
});
const byId = {}; DATA.nodes.forEach(n => byId[n.id] = n);

// 영역 색상 팔레트 (다크 배경용)
const AREAS = [...new Set(DATA.nodes.map(n => n.area))];
const PALETTE = ['#7aa2f7','#bb9af7','#7dcfff','#9ece6a','#e0af68','#f7768e','#ff9e64','#73daca','#c0caf5'];
const colorOf = a => PALETTE[AREAS.indexOf(a) % PALETTE.length];

// 선수학습 조상(이 개념 전에 배워야 하는 모든 개념) 역탐색
function ancestors(id) {
  const seen = new Set(); const dq = [id];
  while (dq.length) { const x = dq.pop(); (pred[x] || []).forEach(p => { if (!seen.has(p)) { seen.add(p); dq.push(p); } }); }
  return seen;
}

let hi = new Set();        // 강조 노드
let hiLinks = new Set();   // 강조 엣지
let focus = null;

function setFocus(id) {
  focus = id;
  if (!id) { hi = new Set(); hiLinks = new Set(); renderPanel(null); Graph.nodeColor(Graph.nodeColor()); return; }
  const anc = ancestors(id); anc.add(id);
  hi = anc;
  hiLinks = new Set();
  DATA.links.forEach(l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    if (anc.has(s) && anc.has(t)) hiLinks.add(l);
  });
  renderPanel(byId[id]);
}

function renderPanel(n) {
  const p = document.getElementById('panel');
  if (!n) { p.style.display = 'none'; return; }
  const prereqs = (pred[n.id] || []).map(i => byId[i]);
  const nexts = (succ[n.id] || []).map(i => byId[i]);
  p.innerHTML =
    `<h2>${n.label}</h2><div class="meta">${n.grade} · ${n.area}</div>` +
    `<div class="row"><b>문항 수</b> ${n.items}개 · <b>평균 정답률</b> ${n.correctRate.toFixed(0)}%</div>` +
    `<div class="row"><b>직속 선수 개념</b>${prereqs.length ? '' : ' 없음 (출발 개념)'}<div class="chips">` +
      prereqs.map(x => `<span class="chip">${x.grade} ${x.label}</span>`).join('') + `</div></div>` +
    `<div class="row"><b>후속 개념</b>${nexts.length ? '' : ' 없음'}<div class="chips">` +
      nexts.map(x => `<span class="chip">${x.grade} ${x.label}</span>`).join('') + `</div></div>`;
  p.style.display = 'block';
}

const Graph = ForceGraph()(document.getElementById('graph'))
  .graphData(DATA)
  .backgroundColor('#0c0d12')
  .nodeRelSize(4)
  .nodeVal('val')
  .nodeColor(n => {
    if (hi.size && !hi.has(n.id)) return 'rgba(90,96,120,0.22)';
    return colorOf(n.area);
  })
  .linkColor(l => hiLinks.has(l) ? '#ffcf5c' : 'rgba(120,130,160,0.16)')
  .linkWidth(l => hiLinks.has(l) ? 2.2 : 0.6)
  .linkDirectionalArrowLength(3.5)
  .linkDirectionalArrowRelPos(1)
  .linkDirectionalParticles(l => hiLinks.has(l) ? 3 : 0)
  .linkDirectionalParticleWidth(2)
  .nodeCanvasObjectMode(() => 'after')
  .nodeCanvasObject((n, ctx, scale) => {
    const dim = hi.size && !hi.has(n.id);
    if (scale < 2.2 && !(hi.has(n.id) && hi.size)) return; // 확대 시 또는 강조 시에만 라벨
    const label = n.label;
    ctx.font = `${11 / scale}px -apple-system, sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillStyle = dim ? 'rgba(150,155,175,0.35)' : '#e6e8ef';
    ctx.fillText(label, n.x, n.y + Math.sqrt(n.val) * 1.6 + 1.5 / scale);
  })
  .onNodeClick(n => { setFocus(n.id); Graph.centerAt(n.x, n.y, 600); })
  .onNodeHover(n => {
    if (focus) return; // 포커스 고정 시 hover 무시
    if (!n) { hi = new Set(); hiLinks = new Set(); return; }
    hi = new Set([n.id, ...(succ[n.id] || []), ...(pred[n.id] || [])]);
    hiLinks = new Set(DATA.links.filter(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return s === n.id || t === n.id;
    }));
  })
  .onBackgroundClick(() => setFocus(null));

Graph.d3Force('charge').strength(-120);

// 검색: 라벨 부분일치 → 포커스 + 선수경로 강조
document.getElementById('q').addEventListener('input', e => {
  const v = e.target.value.trim();
  if (!v) { setFocus(null); return; }
  const hit = DATA.nodes.find(n => n.label.includes(v)) || DATA.nodes.find(n => (n.label + n.grade).includes(v));
  if (hit) { setFocus(hit.id); Graph.centerAt(hit.x, hit.y, 600); Graph.zoom(3, 600); }
});

// 범례
document.getElementById('legend').innerHTML =
  AREAS.map(a => `<span><i style="background:${colorOf(a)}"></i>${a}</span>`).join('');
</script>
</body>
</html>
"""


def build(graph_path=None, html_path=None):
    graph_path = graph_path or config.GRAPH_PATH
    html_path = html_path or config.HTML_PATH
    with open(graph_path, encoding="utf-8") as f:
        data = json.load(f)
    html = _TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path, len(data["nodes"]), len(data["links"])


if __name__ == "__main__":
    path, n, e = build()
    print(f"시각화 생성: {path} (노드 {n} · 엣지 {e})")
    print("브라우저에서 graph.html 을 열면 됩니다.")
