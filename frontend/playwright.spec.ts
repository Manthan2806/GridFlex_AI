import { test, expect } from '@playwright/test';

const baseURL = 'http://localhost:5173';
const viewports = [
  { width: 1920, height: 1080, label: '1920x1080' },
  { width: 1366, height: 768, label: '1366x768' },
  { width: 1024, height: 768, label: '1024x768' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 375, height: 812, label: '375x812' }
];

const pages = [
  { path: '/overview', name: 'Overview' },
  { path: '/flexibility', name: 'Flexibility' },
  { path: '/dispatch', name: 'Dispatch' },
  { path: '/experiments', name: 'Experiments' }
];

test.describe('Frontend Validation', () => {
  test.beforeEach(async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: Error[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    page.on('pageerror', error => {
      pageErrors.push(error);
    });
    
    await page.addInitScript(() => {
      window.__VALIDATION_CONSOLE_ERRORS__ = [];
      window.__VALIDATION_PAGE_ERRORS__ = [];
    });
  });

  for (const viewport of viewports) {
    test.describe(`Viewport: ${viewport.label}`, () => {
      test.beforeEach(async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
      });

      for (const pageInfo of pages) {
        test(`Page: ${pageInfo.name}`, async ({ page }) => {
          const consoleErrorsBefore: string[] = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
          const pageErrorsBefore: Error[] = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);
          
          await page.goto(`${baseURL}${pageInfo.path}`);
          await page.waitForSelector('#root', { state: 'attached' });
          await page.waitForTimeout(500);
          
          const consoleErrorsAfter: string[] = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
          const pageErrorsAfter: Error[] = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);
          
          const newConsoleErrors = consoleErrorsAfter.filter((_, i) => i >= consoleErrorsBefore.length);
          const newPageErrors = pageErrorsAfter.filter((_, i) => i >= pageErrorsBefore.length);
          
          const allConsoleErrors = newConsoleErrors.flat();
          const allPageErrors = newPageErrors.map(err => err.message);
          
          const allErrors = [...allConsoleErrors, ...allPageErrors];
          
          expect(allErrors).toEqual([]);
        });
      }
    });
  }
});

async function waitForAppToLoad(page: any) {
  await page.waitForSelector('#root', { state: 'attached' });
  await page.waitForTimeout(500);
}