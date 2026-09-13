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

for (const viewport of viewports) {
  for (const pageInfo of pages) {
    test(`[${viewport.label}] ${pageInfo.name}`, async ({ page }) => {
      const consoleErrors: string[] = [];
      const pageErrors: Error[] = [];
      
      // Capture console errors
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });
      
      // Capture page errors
      page.on('pageerror', error => {
        pageErrors.push(error);
      });
      
      // Set viewport
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Navigate to page
      await page.goto(`${baseURL}${pageInfo.path}`);
      await page.waitForSelector('#root', { state: 'attached' });
      await page.waitForTimeout(500);
      
      // Check horizontal overflow
      const hasHorizontalOverflow = await page.evaluate(() => {
        return document.body.scrollWidth > window.innerWidth;
      });
      expect(hasHorizontalOverflow).toBe(false, `Horizontal overflow detected on ${pageInfo.name} at ${viewport.label}`);
      
      // Check console errors (filter favicon-related)
      const nonFaviconErrorMessages = consoleErrors.filter(e => !e.toLowerCase().includes('favicon'));
      expect(nonFaviconErrorMessages).toEqual([], 
        `Console errors on ${pageInfo.name} at ${viewport.label}: ${nonFaviconErrorMessages.join(', ')}`);
      
      // Check for React jsx attribute warnings
      const jsxWarnings = consoleErrors.filter(e => 
        e.includes('jsx') && e.toLowerCase().includes('attribute'));
      expect(jsxWarnings).toEqual([], 
        `React jsx attribute warnings on ${pageInfo.name} at ${viewport.label}`);
      
      // Check favicon loads
      const faviconLink = await page.$('link[rel="icon"]');
      expect(faviconLink).not.toBeNull();
      
      if (faviconLink) {
        const href = await faviconLink.getAttribute('href');
        expect(href).toContain('favicon.svg');
        
        const faviconUrl = href.startsWith('http') ? href : `${baseURL}${href}`;
        const res = await page.request.get(faviconUrl);
        expect(res.ok()).toBe(true);
      }
      
      // Check page-level favicon errors (404)
      const faviconPageErrors = pageErrors.filter(e => 
        e.message.toLowerCase().includes('favicon'));
      expect(faviconPageErrors).toEqual([], 
        `Favicon 404 errors on ${pageInfo.name} at ${viewport.label}`);
      
      // Page-specific: Check tables render
      const tables = await page.$$('table');
      for (const table of tables) {
        expect(await table.isVisible()).toBe(true);
      }
      
      // Page-specific: Check status badges don't show "unknown"
      const badges = await page.$$('span[role="status"]');
      for (const badge of badges) {
        const text = await badge.textContent();
        expect(text?.toLowerCase()).not.toBe('unknown');
        expect(text?.toLowerCase()).not.toContain('unknown');
      }
      
      // Page-specific: Check drawer on flexibility page
      if (pageInfo.path === '/flexibility') {
        const rows = await page.$$('table tbody tr');
        if (rows.length > 0) {
          await rows[0].click();
          const drawer = await page.waitForSelector('[role="dialog"]', { 
            state: 'visible', timeout: 5000 
          }).catch(() => null);
          expect(drawer).toBeTruthy();
          
          const closeBtn = await page.$('[aria-label="Close resource detail"]');
          if (closeBtn) {
            await closeBtn.click();
          }
        }
      }
    });
  }
}