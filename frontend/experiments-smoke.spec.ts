import { test, expect } from '@playwright/test';

const baseURL = 'http://localhost:5173';

test.describe('Experiments Page Smoke Test', () => {
  test('should render Experiments page and run simulation', async ({ page }) => {
    // Track console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to Experiments page
    await page.goto(`${baseURL}/experiments`);
    await page.waitForSelector('#root', { state: 'attached' });
    await page.waitForTimeout(1000);

    // Verify page renders without errors
    expect(consoleErrors).toEqual([]);

    // Verify page title/header is visible
    await expect(page.locator('text=Experiments')).toBeVisible();

    // Verify Run Horizon Simulation button exists and is clickable
    const runButton = page.locator('button:has-text("Run Horizon Simulation")');
    await expect(runButton).toBeVisible();
    await expect(runButton).toBeEnabled();

    // Click the Run Horizon Simulation button
    await runButton.click();

    // Wait for simulation to complete (button text changes to "Running Simulation...")
    await expect(page.locator('button:has-text("Running Simulation...")')).toBeVisible();

    // Wait for simulation to complete and results to appear
    // The mock adapter takes ~800ms, so wait a bit longer
    await page.waitForTimeout(2000);

    // Verify button is re-enabled and shows original text
    await expect(runButton).toBeEnabled();
    await expect(runButton).toContainText('Run Horizon Simulation');

    // Verify Feasibility badge appears (FEASIBLE)
    await expect(page.locator('text=FEASIBLE')).toBeVisible();

    // Verify Feasibility Reason appears
    await expect(page.locator('text=All horizon steps respect feeder capacity constraints and resource availability schedules.')).toBeVisible();

    // Verify tabs are visible
    await expect(page.locator('text=Feasibility')).toBeVisible();
    await expect(page.locator('text=Horizon')).toBeVisible();
    await expect(page.locator('text=Comparison')).toBeVisible();
    await expect(page.locator('text=Trust Updates')).toBeVisible();

    // Click through tabs to verify content renders
    await page.click('button:has-text("Horizon")');
    await expect(page.locator('text=Step 1: 14:00 - 15:00')).toBeVisible();

    await page.click('button:has-text("Comparison")');
    await expect(page.locator('text=Delivery Error (kW)')).toBeVisible();

    await page.click('button:has-text("Trust Updates")');
    await expect(page.locator('text=ev-fleet-01')).toBeVisible();

    // Verify Instruction Matrix is visible
    await expect(page.locator('text=Instruction Matrix')).toBeVisible();
    await expect(page.locator('text=ev-fleet-01')).toBeVisible();

    // Final check: no console errors
    expect(consoleErrors).toEqual([]);
  });
});