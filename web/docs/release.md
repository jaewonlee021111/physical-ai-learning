# 배포·실행 기록

## 제작 결과
HTML·CSS·JavaScript 원본과 React 원본·Vite 빌드 결과를 함께 저장했다. 소스와 빌드본을 GitHub에 업로드한다.

## 확인한 실행
- 내부 HTTP 미리보기에서 두 버전 렌더링
- HTML → React, React → HTML 상대 경로 전환
- 필터·빈 입력·정상 입력 검사
- 모바일 390px 프레임의 메뉴·Escape·가로 넘침 검증
- desktop/mobile 캡처: ../../evidence/portfolio-desktop.jpg, portfolio-mobile.jpg

## Vercel 상태
공개 배포 미완료. 대상은 기존 연결에서 확인한 팀 `team_7Vpaj3zM2kQll6iitbwxnRrJ`, 새 프로젝트 이름은 `physical-ai-jaewon`이었다. API는 해당 팀 범위 접근 권한 부족으로 403을 반환했다. 이어진 CLI 경로는 자동 승인 검토가 해당 팀 production 공개 배포에 대한 명시적 사용자 승인이 확인되지 않았다는 이유로 차단했다. 우회 배포하지 않았다. 공개 URL을 생성한 것으로 표시하지 않는다.

## 로컬에서 열기
저장소 루트에서 `python -m http.server 8000`, 이후 `http://localhost:8000/web/`에 접속한다. React 완성본도 HTML 화면의 버전 전환 버튼으로 열 수 있다. GitHub Pages를 별도로 활성화할 경우 이 경로와 상대 자산 경로를 그대로 사용할 수 있다. Pages가 현재 활성화되어 있다고 확인한 것은 아니다.
