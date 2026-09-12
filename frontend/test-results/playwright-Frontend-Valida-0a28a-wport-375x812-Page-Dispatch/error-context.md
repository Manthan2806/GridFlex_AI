# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: playwright.spec.ts >> Frontend Validation >> Viewport: 375x812 >> Page: Dispatch
- Location: playwright.spec.ts:52:13

# Error details

```
Error: Too many arguments. If you need to pass more than 1 argument to the function wrap them in an object.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const baseURL = 'http://localhost:5173';
  4  | const viewports = [
  5  |   { width: 1920, height: 1080, label: '1920x1080' },
  6  |   { width: 1366, height: 768, label: '1366x768' },
  7  |   { width: 1024, height: 768, label: '1024x768' },
  8  |   { width: 768, height: 1024, label: '768x1024' },
  9  |   { width: 375, height: 812, label: '375x812' }
  10 | ];
  11 | 
  12 | const pages = [
  13 |   { path: '/overview', name: 'Overview' },
  14 |   { path: '/flexibility', name: 'Flexibility' },
  15 |   { path: '/dispatch', name: 'Dispatch' },
  16 |   { path: '/experiments', name: 'Experiments' }
  17 | ];
  18 | 
  19 | test.describe('Frontend Validation', () => {
  20 |   test.beforeEach(async ({ page }) => {
  21 |     const consoleErrors: string[] = [];
  22 |     const pageErrors: Error[] = [];
  23 |     
  24 |     page.on('console', msg => {
  25 |       if (msg.type() === 'error') {
  26 |         consoleErrors.push(msg.text());
  27 |       }
  28 |     });
  29 |     
  30 |     page.on('pageerror', error => {
  31 |       pageErrors.push(error);
  32 |     });
  33 |     
  34 |     await page.addInitScript(() => {
  35 |       window.__VALIDATION_CONSOLE_ERRORS__ = [];
  36 |       window.__VALIDATION_PAGE_ERRORS__ = [];
  37 |     });
  38 |     
> 39 |     await page.addInitScript((consoleErrorsArray, pageErrorsArray) => {
     |                ^ Error: Too many arguments. If you need to pass more than 1 argument to the function wrap them in an object.
  40 |       window.__VALIDATION_CONSOLE_ERRORS__ = consoleErrorsArray;
  41 |       window.__VALIDATION_PAGE_ERRORS__ = pageErrorsArray;
  42 |     }, consoleErrors, pageErrors);
  43 |   });
  44 | 
  45 |   for (const viewport of viewports) {
  46 |     test.describe(`Viewport: ${viewport.label}`, () => {
  47 |       test.beforeEach(async ({ page }) => {
  48 |         await page.setViewportSize({ width: viewport.width, height: viewport.height });
  49 |       });
  50 | 
  51 |       for (const pageInfo of pages) {
  52 |         test(`Page: ${pageInfo.name}`, async ({ page }) => {
  53 |           const consoleErrorsBefore: string[] = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
  54 |           const pageErrorsBefore: Error[] = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);
  55 |           
  56 |           await page.goto(`${baseURL}${pageInfo.path}`);
  57 |           await page.waitForSelector('#root', { state: 'attached' });
  58 |           await page.waitForTimeout(500);
  59 |           
  60 |           const consoleErrorsAfter: string[] = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
  61 |           const pageErrorsAfter: Error[] = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);
  62 |           
  63 |           const newConsoleErrors = consoleErrorsAfter.filter((_, i) => i >= consoleErrorsBefore.length);
  64 |           const newPageErrors = pageErrorsAfter.filter((_, i) => i >= pageErrorsBefore.length);
  65 |           
  66 |           const allConsoleErrors = newConsoleErrors.flat();
  67 |           const allPageErrors = newPageErrors.map(err => err.message);
  68 |           
  69 |           const allErrors = [...allConsoleErrors, ...allPageErrors];
  70 |           
  71 |           expect(allErrors).toEqual([]);
  72 |         });
  73 |       }
  74 |     });
  75 |   }
  76 | });
  77 | 
  78 | async function waitForAppToLoad(page: any) {
  79 |   await page.waitForSelector('#root', { state: 'attached' });
  80 |   await page.waitForTimeout(500);
  81 | }
```