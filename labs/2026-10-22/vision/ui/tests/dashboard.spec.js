import {test, expect} from '@playwright/test';

for (const width of [1280, 390]) {
  test(`stream, preprocessing, capture and metadata at ${width}px`, async ({page, request}) => {
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setViewportSize({width, height: 844});
    await page.goto('/', {waitUntil: 'domcontentloaded'});
    await expect(page.locator('#source')).toContainText('합성 입력');
    await expect(page.locator('#stage-output')).toBeVisible();
    await expect(page.locator('.feed')).toHaveJSProperty('naturalWidth', 640);
    await page.getByLabel('전처리').selectOption('gray');
    await page.getByRole('button', {name: '설정 적용'}).click();
    await expect.poll(async () => (await (await request.get('/api/status')).json()).mode).toBe('gray');
    const before = await page.locator('#gallery img').count();
    await page.getByRole('button', {name: '현재 화면 촬영'}).click();
    await expect(page.locator('#gallery img')).toHaveCount(before + 1);
    await expect(page.locator('#gallery img').first()).toHaveJSProperty('naturalWidth', 640);
    await page.locator('#stage-capture').click();
    await expect(page.locator('#detail')).toContainText('입력:');
    await page.getByRole('button', {name: '화면 테마 전환'}).click();
    await expect(page.locator('body')).toHaveClass('light');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    expect(errors).toEqual([]);
    await page.screenshot({path: `screenshots/dashboard-${width}.png`, fullPage: true});
  });
}

test('SSE updates continue while log display is paused', async ({page}) => {
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#logs')).not.toBeEmpty();
  await page.getByRole('button', {name: '로그 일시정지'}).click();
  const paused = await page.locator('#logs').textContent();
  const summary = await page.locator('#summary').textContent();
  await expect.poll(() => page.locator('#summary').textContent()).not.toBe(summary);
  await expect(page.locator('#logs')).toHaveText(paused);
  await page.getByRole('button', {name:'로그 계속 보기'}).click();
  await expect.poll(() => page.locator('#logs').textContent()).not.toBe(paused);
});
