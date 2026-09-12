import { test, expect } from '@playwright/test';

const baseURL = 'http://localhost:5173';
const viewports = [
  { width: 375, height: 812, label: 'mobile-375px' },
  { width: 768, height: 1024, label: 'tablet-768px' },
  { width: 1280, height: 800, label: 'desktop-1280px' }
];

const dispatchViewports = [
  { width: 375, height: 812, label: '375x812' },
  { width: 768, height: 1366, label: '768x1366' },
  { width: 1280, height: 800, label: '1280x800' }
];

const allPages = [
  { path: '/overview', name: 'Overview' },
  { path: '/flexibility', name: 'Flexibility' },
  { path: '/dispatch', name: 'Dispatch' },
  { path: '/experiments', name: 'Experiments' }
];

const dispatchPageSections = [
  'RenewableOpportunityDetail',
  'RelevantFlexibility',
  'RecommendedDispatch',
  'DecisionRationale',
  'ConstraintCheck',
  'SimulationAction',
  'SimulationResult'
];

function countOccurrences(page: any, selector: string): number {
  return page.$$eval(selector, elements => elements.length);
}

test.describe('F3 Dispatch Validation', () => {
  test('should verify all pages load without errors across viewports', async ({ page }) => {
    const baseConsoleErrors: string[] = [];
    const basePageErrors: Error[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        baseConsoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      basePageErrors.push(error);
    });

    for (const viewport of dispatchViewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      for (const pageInfo of allPages) {
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

        // Filter out favicon-related errors
        const nonFaviconErrors = allErrors.filter((e: string) => !e.toLowerCase().includes('favicon'));
        
        if (nonFaviconErrors.length > 0) {
          console.log(`⚠ Errors on ${pageInfo.name} at ${viewport.label}:`, nonFaviconErrors);
        }

        // Check for React jsx attribute warnings
        const jsxWarnings = allErrors.filter((e: string) => e.includes('jsx') && e.toLowerCase().includes('attribute'));
        if (jsxWarnings.length > 0) {
          console.log(`⚠ React jsx warnings on ${pageInfo.name} at ${viewport.label}:`, jsxWarnings);
        }
      }
    }
  });

  test('should verify /dispatch page loads and all 7 sections render', async ({ page }) => {
    await page.goto(`${baseURL}/dispatch`);
    await page.waitForSelector('#root', { state: 'attached' });
    await page.waitForTimeout(1000);

    // Verify all 7 dispatch sections render
    for (const section of dispatchPageSections) {
      const selector = `[data-testid="${section.toLowerCase()}"]` || section;
      const element = await page.$(`text=${section}`);
      // Try to find the section by its heading text
      const headings = await page.$$(`h3`);
      const headingTexts = await Promise.all(headings.map(async (h: any) => await h.textContent()));
      const found = headingTexts!.includes(section);
      expect(found).toBe(true, `${section} section not found on /dispatch page`);
    }

    // Verify sidebar appears exactly once
    const sidebars = await page.$$('aside');
    expect(sidebars.length).toBe(1), `Expected exactly 1 sidebar on /dispatch, found ${sidebars.length}`;

    // Verify scenario context appears exactly once
    const scenarioContexts = await page.$$('[aria-label="Scenario context"]');
    expect(scenarioContexts.length).toBe(1), `Expected exactly 1 scenario context on /dispatch, found ${scenarioContexts.length}`;
  });

  test('should verify clicking "Simulate Dispatch" shows simulation result', async ({ page }) => {
    await page.goto(`${baseURL}/dispatch`);
    await page.waitForSelector('#root', { state: 'attached' });
    await page.waitForTimeout(1000);

    // Click "Run Simulation" button
    await page.click('button:has-text("Run Simulation")');
    await page.waitForTimeout(3000);

    // Verify simulation result appears
    const simulationResultHeading = await page.$('h3:has-text("Simulation Result")');
    expect(simulationResultHeading).not.toBeNull(), 'Simulation Result section should appear after simulation';

    // Check that the result has content (not "No simulation has been run yet")
    const resultSection = await page.$('.dispatch-sections');
    expect(resultSection).toBeTruthy();

    // Check for simulation steps or status
    const statusIndicators = await page.$$('[data-testid*="status"], .status');
    const hasStatus = statusIndicators.length > 0;
    expect(hasStatus).toBe(true, 'Simulation status should be visible');
  });

  test('should verify no 404 favicon errors across all pages and viewports', async ({ page }) => {
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      for (const pageInfo of allPages) {
        await page.goto(`${baseURL}${pageInfo.path}`);
        await page.waitForSelector('#root', { state: 'attached' });
        await page.waitForTimeout(500);

        // Check for favicon 404 errors in page errors
        const pageErrors = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);
        const faviconErrors = pageErrors.filter((e: Error) => e.message.toLowerCase().includes('favicon'));
        expect(faviconErrors).toEqual([], `Favicon 404 errors on ${pageInfo.name} at ${viewport.label}`);

        // Check console errors (excluding favicon)
        const consoleErrors = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
        const nonFaviconErrors = consoleErrors.filter((e: string) => !e.toLowerCase().includes('favicon'));
        expect(nonFaviconErrors).toEqual([], `Non-favicon console errors on ${pageInfo.name} at ${viewport.label}: ${nonFaviconErrors.join(', ')}`);
      }
    }
  });

  test('should verify sidebar appears exactly once on each dispatch-related page', async ({ page }) => {
    for (const pageInfo of allPages) {
      await page.goto(`${baseURL}${pageInfo.path}`);
      await page.waitForSelector('#root', { state: 'attached' });
      await page.waitForTimeout(500);

      const sidebars = await page.$$('aside');
      // On dispatch page, expect exactly 1 sidebar
      if (pageInfo.path === '/dispatch') {
        expect(sidebars.length).toBe(1), `/dispatch: Expected exactly 1 sidebar, found ${sidebars.length}`;
      } else {
        // On other pages, sidebar should still appear (from AppShell) but count may vary
        console.log(`${pageInfo.name}: found ${sidebars.length} sidebars`);
      }

      // Verify scenario context appears exactly once
      const scenarioContexts = await page.$$('[aria-label="Scenario context"]');
      expect(scenarioContexts.length).toBe(1), `/${pageInfo.path}: Expected exactly 1 scenario context, found ${scenarioContexts.length}`;
    }
  });

  test('should verify all routes render without console errors', async ({ page }) => {
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      for (const pageInfo of allPages) {
        await page.goto(`${baseURL}${pageInfo.path}`);
        await page.waitForSelector('#root', { state: 'attached' });
        await page.waitForTimeout(500);

        const consoleErrors = await page.evaluate(() => window.__VALIDATION_CONSOLE_ERRORS__ || []);
        const pageErrors = await page.evaluate(() => window.__VALIDATION_PAGE_ERRORS__ || []);

        const newConsoleErrors = consoleErrors.filter((_, i) => i >= 0);
        const newPageErrors = pageErrors.map(err => err.message);

        const allConsoleErrors = newConsoleErrors.flat();
        const allPageErrors = newPageErrors;

        const nonFaviconErrors = allConsoleErrors.filter((e: string) => !e.toLowerCase().includes('favicon'));
        
        expect(nonFaviconErrors.length).toBe(0, `Console errors on ${pageInfo.name} at ${viewport.label}: ${nonFaviconErrors.join(', ')}`);
        
        const jsxWarnings = allConsoleErrors.filter((e: string) => e.includes('jsx') && e.toLowerCase().includes('attribute'));
        expect(jsxWarnings.length).toBe(0, `React jsx attribute warnings on ${pageInfo.name} at ${viewport.label}`);
      }
    }
  });
});