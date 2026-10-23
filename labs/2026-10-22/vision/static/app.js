const $ = id => document.getElementById(id);
let paused = false;
let pipeline = [];
async function call(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || response.status);
  return data;
}
async function gallery() {
  const items = await call('/api/captures');
  $('gallery').replaceChildren(...items.map(url => {
    const a = document.createElement('a');
    a.href = url; a.target = '_blank'; a.rel = 'noopener';
    const img = document.createElement('img');
    img.src = url; img.alt = '저장한 실습 화면';
    a.append(img);
    return a;
  }));
}
$('settings').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await call('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(Object.fromEntries(new FormData(event.target)))});
    $('error').textContent = '설정을 적용했습니다.';
  } catch(error) { $('error').textContent = error.message; }
});
$('capture').addEventListener('click', async () => {
  try {
    await call('/api/capture', {method:'POST'});
    await gallery();
    $('error').textContent = '사진과 처리 정보를 저장했습니다.';
  } catch(error) { $('error').textContent = error.message; }
});
$('theme').addEventListener('click', () => document.body.classList.toggle('light'));
$('pause').addEventListener('click', () => {
  paused = !paused;
  $('pause').textContent = paused ? '로그 계속 보기' : '로그 일시정지';
});
function draw(data) {
  $('source').textContent = data.source === 'camera' ? '실제 카메라' : '합성 입력 · 카메라 아님';
  if (data.error) $('error').textContent = data.error;
  $('summary').textContent = `#${data.frame ?? 0} · 약 ${data.stream_fps_estimate ?? 0} FPS · ${data.device ?? 'cpu'} / ${data.imgsz ?? '-'} · conf ${data.conf ?? '-'} · skip ${data.skip ?? '-'} · 병목 ${data.bottleneck ?? '-'}`;
  $('objects').textContent = !data.model_enabled ? 'YOLO 꺼짐 · 탐지를 실행하지 않습니다.' : (data.sampled_out ? '이번 프레임 추론 생략 · 이전 박스 재사용 / ' : '') + (data.detections?.map(o => `${o.label} ${(o.confidence*100).toFixed(1)}%`).join(', ') || '탐지 없음');
  for (const node of pipeline) {
    const button = document.getElementById(`stage-${node.id}`);
    if (!button) continue;
    button.textContent = `${node.id} · 평균 ${(data.mean_ms?.[node.id] ?? 0).toFixed(2)} ms`;
    button.classList.toggle('active', data.active === node.id);
    button.classList.toggle('skipped', node.id === 'inference' && data.sampled_out);
  }
  if (!paused) {
    $('logs').textContent = (data.logs || []).filter(row => $('level').value === 'ALL' || (row.level || 'INFO') === $('level').value).map(row => JSON.stringify(row)).join('\n');
    $('logs').scrollTop = $('logs').scrollHeight;
  }
}
async function init() {
  pipeline = await call('/api/pipeline');
  const order = ['capture','preprocess','inference','postprocess','visualize','output'];
  pipeline.sort((a,b) => order.indexOf(a.id)-order.indexOf(b.id));
  // 로컬 SVG 연결선: 외부 CDN 없이 오프라인에서도 같은 흐름을 보여준다.
  for (const node of pipeline) {
    const button = document.createElement('button');
    button.type = 'button'; button.id = `stage-${node.id}`; button.className = 'stage';
    button.addEventListener('click', () => {$('detail').textContent = `${node.summary || node.label} / 입력: ${node.input || '-'} / 출력: ${node.output || '-'} / 이유: ${node.reason || '-'}`;});
    $('stages').append(button);
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 20 12'); svg.setAttribute('class','connector'); svg.setAttribute('aria-hidden','true');
    const path = document.createElementNS(svg.namespaceURI,'path');
    path.setAttribute('d','M10 0V10M6 6L10 10L14 6'); path.setAttribute('fill','none'); path.setAttribute('stroke','currentColor');
    svg.append(path); $('stages').append(svg);
  }
  await gallery();
  const events = new EventSource('/events');
  events.onmessage = event => draw(JSON.parse(event.data));
  events.onerror = () => {$('error').textContent = '상태 연결을 재시도합니다. 서버 실행 여부를 확인하세요.';};
  addEventListener('pagehide', () => events.close(), {once:true});
}
init().catch(error => {$('error').textContent = error.message;});
