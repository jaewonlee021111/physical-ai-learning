import test from 'node:test';
import assert from 'node:assert/strict';
import { validateInquiry, filterProjects } from '../../shared.mjs';

test('빈 입력·공백은 세 필드 모두 실패한다', () => { assert.deepEqual(Object.keys(validateInquiry({name:' ', email:'', message:''})), ['name','email','message']); });
test('이메일 형식과 최소·최대 길이를 검사한다', () => {
  for (const email of ['a', 'a@b', 'a b@c.com']) assert.ok(validateInquiry({name:'이재원',email,message:'내용입니다. 충분한 길이.'}).email);
  assert.ok(validateInquiry({name:'이재원',email:'a@b.com',message:'짧음'}).message);
  assert.ok(validateInquiry({name:'이재원',email:'a@b.com',message:'가'.repeat(1001)}).message);
});
test('정상 입력과 경계 길이를 허용한다', () => { for (const length of [10,1000]) assert.deepEqual(validateInquiry({name:'이재원',email:'test@example.com',message:'가'.repeat(length)}),{}); });
test('분야 필터는 원본과 분리된 결과를 제공한다', () => { assert.equal(filterProjects('all').length,6); assert.equal(filterProjects('web').length,2); assert.equal(filterProjects('python').length,4); assert.equal(filterProjects('unknown').length,0); });
