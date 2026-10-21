# HTML·React 포트폴리오 실습

방문자: 이재원의 실습 결과를 확인하려는 동료·강사. 목적: 첫 화면에서 학습 방향을 파악하고 프로젝트 소스와 실행 기록으로 이동한다.

## 실행

저장소 루트에서 `python -m http.server 8000`을 실행한 뒤 `http://localhost:8000/web/`에 접속한다. ES module을 사용하므로 파일 더블클릭 대신 HTTP 서버로 연다. React 완성본은 [react/dist/index.html](react/dist/index.html)에 포함했다.

React 수정·재빌드:

```sh
cd web/react
npm ci
npm test
npm run build
```

개발 중에는 `npm run dev`, HTML과 빌드본 비교는 루트의 Python HTTP 서버를 사용한다. `package-lock.json`으로 의존성을 고정했다.

## 같은 기능의 두 구현

| 기능 | HTML·JavaScript | React |
| --- | --- | --- |
| 의미 있는 구조 | header·nav·main·section·footer | 같은 요소를 컴포넌트로 구성 |
| 프로젝트 표시 | createElement·textContent | ProjectCard와 props |
| 분야 필터 | DOM 재구성·aria-pressed 변경 | category state와 목록 렌더링 |
| 모바일 메뉴 | dataset·aria-expanded | open state |
| 문의 입력 | FormData·DOM 오류 안내 | values·errors·result state |
| 입력 규칙 | shared.mjs의 순수 함수 | 같은 함수를 재사용 |
| 배포 경로 | 상대 경로 | Vite base './' |

이름·이메일·문의 길이를 검사하고 첫 오류로 포커스를 옮긴다. 개인정보를 저장하거나 전송하지 않는다. 메뉴·필터 버튼에는 접근성 상태를 제공하며 모션 감소 설정을 따른다.

## 검사 기록

- [실행 결과](../evidence/validation.json)
- [브라우저 확인](../evidence/browser-check.json)
- [자동 검수와 수정 내용](docs/review.md)
- [공개 배포 기록](docs/release.md)

수업의 사람 팀 검수·Notion 실제 호출 기록과 자동 점검은 구분한다. Notion 연결은 [MCP 안내](../mcp/README.md)를 참고한다.
