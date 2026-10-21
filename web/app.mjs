import { filterProjects, sessions, validateInquiry } from './shared.mjs';

const nav = document.querySelector('#main-nav');
const toggle = document.querySelector('.menu-toggle');
function closeMenu() { nav.dataset.open = 'false'; toggle.setAttribute('aria-expanded', 'false'); }
toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; nav.dataset.open = String(open); toggle.setAttribute('aria-expanded', String(open)); });
nav.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { closeMenu(); toggle.focus(); } });

function showProjects(category) {
  const items = filterProjects(category);
  const grid = document.querySelector('#project-grid');
  grid.replaceChildren(...items.map(project => {
    const card = document.createElement('article'); card.className = 'project-card';
    const preview = document.createElement('div'); preview.className = `project-preview ${project.accent}`; preview.setAttribute('aria-hidden', 'true');
    for (const line of project.preview) { const row = document.createElement('span'); row.textContent = line; preview.append(row); }
    const body = document.createElement('div'); body.className = 'project-body';
    const tag = document.createElement('p'); tag.className = 'project-tag'; tag.textContent = project.tag;
    const title = document.createElement('h3'); title.textContent = project.title;
    const description = document.createElement('p'); description.textContent = project.description;
    const link = document.createElement('a'); link.href = project.href; link.className = 'project-link'; link.textContent = '프로젝트 열기 ↗'; link.setAttribute('aria-label', `${project.title} 프로젝트 열기`);
    body.append(tag, title, description, link); card.append(preview, body); return card;
  }));
  document.querySelector('#project-count').textContent = `${items.length} PROJECTS`;
}
for (const button of document.querySelectorAll('[data-filter]')) button.addEventListener('click', () => {
  for (const item of document.querySelectorAll('[data-filter]')) item.setAttribute('aria-pressed', String(item === button));
  showProjects(button.dataset.filter);
});
showProjects('all');
for (const [date, title, detail] of sessions) {
  const item = document.createElement('li'); const time = document.createElement('time'); time.textContent = date; time.dateTime = `2026-${date.replace('.', '-')}`;
  const body = document.createElement('div'); const heading = document.createElement('h3'); heading.textContent = title; const description = document.createElement('p'); description.textContent = detail; body.append(heading, description); item.append(time, body); document.querySelector('#session-list').append(item);
}
document.querySelector('#inquiry-form').addEventListener('submit', event => {
  event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); const errors = validateInquiry(values);
  for (const name of ['name', 'email', 'message']) { document.querySelector(`#${name}-error`).textContent = errors[name] || ''; document.querySelector(`#${name}`).setAttribute('aria-invalid', String(Boolean(errors[name]))); }
  document.querySelector('#form-result').textContent = Object.keys(errors).length ? '입력 내용을 다시 확인해 주세요.' : '입력 검사를 통과했습니다. 이 실습 폼은 메시지를 전송하지 않습니다.';
  if (Object.keys(errors).length) document.querySelector(`#${Object.keys(errors)[0]}`).focus();
});
