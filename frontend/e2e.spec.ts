import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';
const VIEWPORTS = [
  { width: 1920, height: 1080 },
  { width: 1366, height: 768 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 375, height: 812 }
];
const PAGES = [
  '/overview',
  '/flexibility',
  '/dispatch',
  '/experiments'
];

for (const v of VIEWPORTS) {
  for (const p of PAGES) {
    test(`Viewport ${v.width}x${v.height} - Page ${p.replace('/', '')}`, async ({ page }) => {
      await page.setViewportSize({ width: v.width, height: v.height });
      
      const errors: string[] = [];
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      page.on('pageerror', e => { errors.push(e.message); });
      
      await page.goto(`${BASE_URL}${p}`);
      await page.waitForSelector('#root');
      
      const hasOverflow = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
      expect(hasOverflow).toBe(false);
      
      const faviconOk = await page.evaluate(() => {
        const link = document.querySelector('link[rel="icon"]');
        return link !== null;
      });
      expect(faviconOk).toBe(true);
      
      const jsxErrors = errors.filter(e => e.toLowerCase().includes('jsx') && e.toLowerCase().includes('attribute'));
      expect(jsxErrors).toEqual([]);
      
      const faviconErrors = errors.filter(e => e.toLowerCase().includes('favicon'));
      expect(faviconErrors).toEqual([]);
    });
  }
}