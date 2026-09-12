# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: experiments-smoke.spec.ts >> Experiments Page Smoke Test >> should render Experiments page and run simulation
- Location: experiments-smoke.spec.ts:6:7

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 3

- Array []
+ Array [
+   "Failed to load resource: the server responded with a status of 500 (Internal Server Error)",
+ ]
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]: "[plugin:vite:import-analysis] Failed to resolve import \"../../../app/providers/DataAdapterProvider\" from \"src\\features\\experiments\\useExperiments.ts\". Does the file exist?"
  - generic [ref=e5]: C:/Users/viraj/Code_files/Github/GridFlex AI/frontend/src/features/experiments/useExperiments.ts:2:31
  - generic [ref=e6]: "1 | import { useCallback, useEffect, useMemo, useReducer, useState } from \"react\"; 2 | import { useDataAdapter } from \"../../../app/providers/DataAdapterProvider\"; | ^ 3 | import { ExperimentAPI } from \"./experimentAPI\"; 4 | import { experimentReducer, initialExperimentUIState } from \"./experimentSlice\";"
  - generic [ref=e7]: at formatError (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:44066:46) at TransformContext.error (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:44062:19) at normalizeUrl (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:41845:33) at process.processTicksAndRejections (node:internal/process/task_queues:104:5) at async file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:41999:47 at async Promise.all (index 1) at async TransformContext.transform (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:41915:13) at async Object.transform (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:44356:30) at async loadAndTransform (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:55088:29) at async viteTransformMiddleware (file:///C:/Users/viraj/Code_files/Github/GridFlex%20AI/frontend/node_modules/vite/dist/node/chunks/dep-827b23df.js:64699:32
  - generic [ref=e8]:
    - text: Click outside, press Esc key, or fix the code to dismiss. You can also disable this overlay by setting
    - code [ref=e9]: server.hmr.overlay
    - text: to
    - code [ref=e10]: "false"
    - text: in
    - code [ref=e11]: vite.config.js.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const baseURL = 'http://localhost:5173';
  4  | 
  5  | test.describe('Experiments Page Smoke Test', () => {
  6  |   test('should render Experiments page and run simulation', async ({ page }) => {
  7  |     // Track console errors
  8  |     const consoleErrors: string[] = [];
  9  |     page.on('console', msg => {
  10 |       if (msg.type() === 'error') {
  11 |         consoleErrors.push(msg.text());
  12 |       }
  13 |     });
  14 | 
  15 |     // Navigate to Experiments page
  16 |     await page.goto(`${baseURL}/experiments`);
  17 |     await page.waitForSelector('#root', { state: 'attached' });
  18 |     await page.waitForTimeout(1000);
  19 | 
  20 |     // Verify page renders without errors
> 21 |     expect(consoleErrors).toEqual([]);
     |                           ^ Error: expect(received).toEqual(expected) // deep equality
  22 | 
  23 |     // Verify page title/header is visible
  24 |     await expect(page.locator('text=Experiments')).toBeVisible();
  25 | 
  26 |     // Verify Run Horizon Simulation button exists and is clickable
  27 |     const runButton = page.locator('button:has-text("Run Horizon Simulation")');
  28 |     await expect(runButton).toBeVisible();
  29 |     await expect(runButton).toBeEnabled();
  30 | 
  31 |     // Click the Run Horizon Simulation button
  32 |     await runButton.click();
  33 | 
  34 |     // Wait for simulation to complete (button text changes to "Running Simulation...")
  35 |     await expect(page.locator('button:has-text("Running Simulation...")')).toBeVisible();
  36 | 
  37 |     // Wait for simulation to complete and results to appear
  38 |     // The mock adapter takes ~800ms, so wait a bit longer
  39 |     await page.waitForTimeout(2000);
  40 | 
  41 |     // Verify button is re-enabled and shows original text
  42 |     await expect(runButton).toBeEnabled();
  43 |     await expect(runButton).toContainText('Run Horizon Simulation');
  44 | 
  45 |     // Verify Feasibility badge appears (FEASIBLE)
  46 |     await expect(page.locator('text=FEASIBLE')).toBeVisible();
  47 | 
  48 |     // Verify Feasibility Reason appears
  49 |     await expect(page.locator('text=All horizon steps respect feeder capacity constraints and resource availability schedules.')).toBeVisible();
  50 | 
  51 |     // Verify tabs are visible
  52 |     await expect(page.locator('text=Feasibility')).toBeVisible();
  53 |     await expect(page.locator('text=Horizon')).toBeVisible();
  54 |     await expect(page.locator('text=Comparison')).toBeVisible();
  55 |     await expect(page.locator('text=Trust Updates')).toBeVisible();
  56 | 
  57 |     // Click through tabs to verify content renders
  58 |     await page.click('button:has-text("Horizon")');
  59 |     await expect(page.locator('text=Step 1: 14:00 - 15:00')).toBeVisible();
  60 | 
  61 |     await page.click('button:has-text("Comparison")');
  62 |     await expect(page.locator('text=Delivery Error (kW)')).toBeVisible();
  63 | 
  64 |     await page.click('button:has-text("Trust Updates")');
  65 |     await expect(page.locator('text=ev-fleet-01')).toBeVisible();
  66 | 
  67 |     // Verify Instruction Matrix is visible
  68 |     await expect(page.locator('text=Instruction Matrix')).toBeVisible();
  69 |     await expect(page.locator('text=ev-fleet-01')).toBeVisible();
  70 | 
  71 |     // Final check: no console errors
  72 |     expect(consoleErrors).toEqual([]);
  73 |   });
  74 | });
```