import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { sessions, filterProjects, validateInquiry } from '../../shared.mjs';
import '../../style.css';

const repo = 'https://github.com/jaewonlee021111/physical-ai-learning/tree/main';

function Header() {
  const [open, setOpen] = useState(false);
  const menu = useRef(null);
  return <header className="site-header" onKeyDown={event => { if (event.key === 'Escape') { setOpen(false); menu.current.focus(); } }}><div className="shell nav-row">
    <a className="brand" href="#"><span className="brand-mark">j.</span> JAEWON LEE</a>
    <button ref={menu} className="menu-toggle" aria-expanded={open} aria-controls="main-nav" onClick={() => setOpen(!open)}>메뉴</button>
    <nav id="main-nav" aria-label="주 메뉴" data-open={open}>
      {[['#projects', '프로젝트'], ['#journey', '학습 기록'], ['#contact', '문의 실습']].map(([href, label]) => <a key={href} href={href} onClick={() => setOpen(false)}>{label}</a>)}
      <a className="version-link" href="../../index.html">HTML 버전 ↗</a>
    </nav>
  </div></header>;
}

function Hero() {
  return <section className="hero shell" aria-labelledby="hero-title"><div className="hero-copy">
    <p className="eyebrow"><span className="status-dot" /> PHYSICAL AI · LEARNING PORTFOLIO</p>
    <span className="react-label">REACT VERSION · COMPONENTS + STATE</span>
    <h1 id="hero-title">데이터에서 시작해,<br /><span>작동하는 것</span>으로.</h1>
    <p className="intro">의생명공학을 배우는 이재원입니다.<br />Python으로 규칙을 만들고, AI와 함께 검토하고,<br />웹에서 직접 확인할 수 있는 결과를 쌓아 갑니다.</p>
    <div className="hero-actions"><a className="button primary" href="#projects">프로젝트 살펴보기 <span>↗</span></a><a className="text-link" href={repo}>GitHub 기록 ↗</a></div>
    <p className="hero-footnote">동국대학교 의생명공학과 <span>·</span> 의료·바이오 AI에 관심</p>
  </div><div className="hero-board" aria-label="데이터·구현·검증 학습 과정"><div className="board-top"><span className="mini-mark">WORK IN PROGRESS</span><span>2026 / 10</span></div><div className="board-note"><span>01 / INPUT</span><strong>Curiosity<br />into practice.</strong><p>질문을 코드로,<br />코드를 확인 가능한 결과로.</p></div><div className="board-flow"><div><small>DATA</small><strong>{'{ 001 }'}</strong></div><span>→</span><div><small>BUILD</small><strong>def make()</strong></div><span>→</span><div><small>VERIFY</small><strong>✓</strong></div></div><div className="board-bottom"><span>PYTHON / WEB / AI</span><span className="orbit">✳</span></div></div></section>;
}

function ProjectCard({ project }) {
  return <article className="project-card"><div className={`project-preview ${project.accent}`} aria-hidden="true">{project.preview.map(line => <span key={line}>{line}</span>)}</div><div className="project-body"><p className="project-tag">{project.tag}</p><h3>{project.title}</h3><p>{project.description}</p><a className="project-link" href={project.href} aria-label={`${project.title} 프로젝트 열기`}>프로젝트 열기 ↗</a></div></article>;
}

function Projects() {
  const [category, setCategory] = useState('all');
  const filtered = filterProjects(category);
  return <section id="projects" className="section shell"><div className="section-heading"><div><p className="eyebrow">01 / SELECTED PRACTICE</p><h2>직접 만들어 본 것들</h2></div><p>기능을 나누고, 실행하고,<br />결과를 확인하는 연습.</p></div><div className="filter-row" role="group" aria-label="프로젝트 분야 필터">{[['all', '전체'], ['python', 'Python & AI'], ['web', 'Web']].map(([value, label]) => <button key={value} aria-pressed={category === value} onClick={() => setCategory(value)}>{label}</button>)}<span className="project-count" aria-live="polite">{filtered.length} PROJECTS</span></div><div className="project-grid">{filtered.map(project => <ProjectCard key={project.id} project={project} />)}</div></section>;
}

function Journey() {
  return <section id="journey" className="journey section"><div className="shell journey-layout"><div><p className="eyebrow">02 / LEARNING JOURNEY</p><h2>한 번의 실행보다,<br />이어지는 과정.</h2><p className="muted">2026년 10월 21일까지 공개된<br />교육 진도에 맞춘 실습 기록입니다.</p><a className="text-link" href={repo}>날짜별 코드와 실행 결과 ↗</a></div><ol className="session-list">{sessions.map(([date, title, detail]) => <li key={date}><time dateTime={`2026-${date.replace('.', '-')}`}>{date}</time><div><h3>{title}</h3><p>{detail}</p></div></li>)}</ol></div></section>;
}

function InquiryForm() {
  const [values, setValues] = useState({ name: '', email: '', message: '' });
  const [errors, setErrors] = useState({});
  const [result, setResult] = useState('');
  const refs = useRef({});
  function submit(event) {
    event.preventDefault(); const next = validateInquiry(values); setErrors(next);
    const first = Object.keys(next)[0];
    setResult(first ? '입력 내용을 다시 확인해 주세요.' : '입력 검사를 통과했습니다. 이 실습 폼은 메시지를 전송하지 않습니다.');
    if (first) refs.current[first].focus();
  }
  return <form noValidate onSubmit={submit}>{[['name', '이름'], ['email', '이메일'], ['message', '문의 내용']].map(([name, label]) => {
    const props = { id: name, name, value: values[name], 'aria-invalid': Boolean(errors[name]), 'aria-describedby': `${name}-error`, ref: element => { refs.current[name] = element; }, onChange: event => { setValues({ ...values, [name]: event.target.value }); setResult(''); } };
    return <div className="field" key={name}><label htmlFor={name}>{label}{name === 'message' && <span>10~1,000자</span>}</label>{name === 'message' ? <textarea {...props} rows="4" maxLength={1000} placeholder="어떤 프로젝트가 궁금하신가요?" /> : <input {...props} type={name === 'email' ? 'email' : 'text'} autoComplete={name === 'email' ? 'email' : 'name'} placeholder={name === 'email' ? 'hello@example.com' : '이름을 입력해 주세요'} />}<small id={`${name}-error`} className="error">{errors[name] || ''}</small></div>;
  })}<button className="button primary" type="submit">입력 내용 확인 <span>↗</span></button><p className="form-result" role="status" aria-live="polite">{result}</p></form>;
}

function App() {
  return <><a className="skip" href="#main">본문으로 이동</a><Header /><main id="main"><Hero /><Projects /><Journey /><section id="contact" className="section shell contact-layout"><div><p className="eyebrow">03 / FORM PRACTICE</p><h2>입력도, 한 번 더<br />확인합니다.</h2><p className="muted">이름·이메일·문의 내용을 검사하는 폼 실습입니다.<br />입력한 내용은 서버로 전송하거나 저장하지 않습니다.</p><div className="contact-note"><span>↗</span><p>필터·메뉴·입력값·검사 결과를<br />React state로 관리합니다.</p></div></div><InquiryForm /></section></main><footer className="shell footer"><a className="brand" href="#"><span className="brand-mark">j.</span> JAEWON LEE</a><p>배우고, 만들고, 다시 확인합니다.</p><a href="https://github.com/jaewonlee021111">GITHUB ↗</a><small>REACT · JSX · PROPS · STATE · 2026</small></footer></>;
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);
