import { test, expect } from '@playwright/test';

test.describe('Debug Dispatch Page', () => {
  test('inspect dispatch page content', async ({ page }) => {
    const response = await page.goto('http://localhost:5173/dispatch');
    await page.waitForSelector('#root', { state: 'attached' });
    await page.waitForTimeout(2000);

    console.log('RESPONSE STATUS:', response?.status());
    
    const rootInnerHTML = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.innerHTML.substring(0, 2000) : 'NO ROOT';
    });
    console.log('ROOT INNER HTML:', rootInnerHTML);

    // Check what's actually visible on the page
    const visibleText = await page.textContent('body');
    console.log('BODY TEXT LENGTH:', visibleText?.length);
    console.log('BODY TEXT SAMPLE:', visibleText?.substring(0, 500));

    // Check all rendered elements
    const allDivs = await page.$$eval('div', els => els.map(el => el.textContent?.substring(0, 100)));
    console.log('ALL DIVS TEXT:', allDivs.filter(t => t && t.trim().length > 0));

    // Take screenshot
    await page.screenshot({ path: 'test-results/dispatch-debug.png', fullPage: true });
  });
});