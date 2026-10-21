export const projects = [
  { id: 'data', category: 'python', tag: 'DATA · PYTHON', title: '데이터를 다룬다는 것', description: 'CSV와 JSON 사이에서 식별자, 미측정, 실제 0의 의미를 지키는 데이터 실습.', href: 'https://github.com/jaewonlee021111/physical-ai-learning/tree/main/labs/2026-10-08', accent: 'blue', preview: ['001 → "001"', 'empty → null', '0 ≠ missing'] },
  { id: 'python', category: 'python', tag: 'PYTHON · FILE I/O', title: '작게 만들고, 끝까지 검사하기', description: '트리·좌석 예약·측정값 분석부터 JSON 저장과 구역별 센서 보고서까지.', href: 'https://github.com/jaewonlee021111/physical-ai-learning/tree/main/assignments', accent: 'orange', preview: ['  *', ' ***', '*****'] },
  { id: 'equipment', category: 'python', tag: 'AGENT · MCP', title: '실습실 장비 대여 관리', description: '재고 경계를 지키는 대여·반납 CLI. 실제 파일 복원과 MCP 문서 읽기를 검증합니다.', href: 'https://github.com/jaewonlee021111/physical-ai-learning/tree/main/projects/equipment-loan', accent: 'green', preview: ['CAM01   1 / 2', 'MIC01   3 / 3', 'KIT01   0 / 4'] },
  { id: 'market', category: 'web', tag: 'HTML · CSS · JS', title: 'MAKER MARKET', description: '아두이노 부품을 검색하고, 필터링하고, 장바구니에 담는 쇼핑몰 실습.', href: 'https://arduino-mall.vercel.app/', accent: 'purple', preview: ['BOARD + SENSOR', '12 sample products', 'search → cart'] },
  { id: 'pc', category: 'web', tag: 'WEB · INTERACTION', title: 'PC BUILD LAB', description: '컴퓨터 부품을 비교하고 조합하며 견적을 구성하는 인터랙션 프로젝트.', href: 'https://pc-build-lab-jaewon.vercel.app/', accent: 'blue', preview: ['CPU → GPU → RAM', 'parts · compare', 'build your setup'] },
];

export const sessions = [
  ['10.08', '데이터에 맥락 붙이기', '구조·자료형·CSV·JSON'],
  ['10.14', 'Python으로 규칙 만들기', '입력·조건·반복·함수'],
  ['10.15', '파일을 프로그램으로 연결하기', '예외·저장·검사·집계'],
  ['10.16', '변경을 남기고 공유하기', 'Git·GitHub·브랜치·PR'],
  ['10.20', 'AI와 함께 구현하고 검토하기', '설계·에이전트·Skills·MCP'],
  ['10.21', '웹으로 보여 주기', 'HTML·CSS·React·팀 검수'],
];

export function validateInquiry(values) {
  const errors = {};
  if (!String(values.name ?? '').trim()) errors.name = '이름을 입력해 주세요.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(values.email ?? '').trim())) errors.email = '이메일 형식을 확인해 주세요.';
  const message = String(values.message ?? '').trim();
  if (message.length < 10) errors.message = '내용을 10자 이상 입력해 주세요.';
  if (message.length > 1000) errors.message = '내용은 1,000자 이내로 작성해 주세요.';
  return errors;
}

export function filterProjects(category) {
  return projects.filter(project => category === 'all' || project.category === category);
}
