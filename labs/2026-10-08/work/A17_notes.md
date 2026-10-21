# A17 · JSON 객체에 글자·숫자·상태 넣기

## 작성한 결과
False를 false로 고치고 마지막 속성 뒤 쉼표를 제거했다. JSON 타입은 order_id·item 문자열, quantity 숫자, paid bool, note null이다. 새 주문에서는 quantity=0, paid=true, note=""로 작성해 null과 빈 문자열을 구별한다.

공개 교안 활동에 대한 재현 풀이. 사람과의 짝 검토는 별도 진행 항목이다.
