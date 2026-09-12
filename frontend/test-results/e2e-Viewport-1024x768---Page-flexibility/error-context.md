# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e.spec.ts >> Viewport 1024x768 - Page flexibility
- Location: e2e.spec.ts:20:9

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: false
Received: true
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to main content" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - complementary "Primary navigation" [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]: G
      - generic [ref=e8]: GridFlex
    - tablist "Primary navigation" [ref=e9]:
      - tab "Overview" [ref=e10] [cursor=pointer]:
        - generic [aria-hidden] [ref=e11]: ▦
      - tab "Flexibility" [selected] [ref=e13] [cursor=pointer]:
        - generic [aria-hidden] [ref=e14]: ◈
      - tab "Dispatch" [ref=e16] [cursor=pointer]:
        - generic [aria-hidden] [ref=e17]: ▶
      - tab "Experiments" [ref=e19] [cursor=pointer]:
        - generic [aria-hidden] [ref=e20]: ◎
  - main [ref=e22]:
    - generic [ref=e23]:
      - heading "flexibility" [level=2] [ref=e26]
      - generic [ref=e28]:
        - region "Scenario context" [ref=e29]:
          - generic [ref=e30]:
            - generic [ref=e31]:
              - generic [ref=e32]: Scenario ID
              - text: DR-2026-Q3-001
            - generic [ref=e33]:
              - generic [ref=e34]: Time Horizon
              - text: 8 minutes
            - generic [ref=e35]:
              - generic [ref=e36]: Mode
              - text: simulation
        - status "Simulation mode active" [ref=e37]:
          - generic [ref=e39]: Simulation Mode
    - main [ref=e40]:
      - generic [ref=e42]:
        - heading "Flexibility" [level=2] [ref=e43]
        - paragraph [ref=e44]: Portfolio of flexible resources and their trust/reliability
      - generic [ref=e46]:
        - generic [ref=e47]:
          - generic [ref=e48]:
            - generic [ref=e49]: Resources
            - generic [ref=e50]: "12"
          - generic [ref=e51]:
            - generic [ref=e52]: Potential
            - generic [ref=e53]: 1450 kW
          - generic [ref=e54]:
            - generic [ref=e55]: Expected
            - generic [ref=e56]: 1243 kW
          - generic [ref=e57]:
            - generic [ref=e58]: Trusted
            - generic [ref=e59]: 1161 kW
        - generic [ref=e60]:
          - generic [ref=e61]:
            - generic [ref=e62]: Search by ID
            - textbox "e.g. ev-fleet-01" [ref=e63]
          - generic [ref=e64]:
            - generic [ref=e65]: Type
            - combobox [ref=e66]:
              - option "All types" [selected]
              - option "EV"
              - option "Water Heater"
              - option "Industrial Batch"
          - generic [ref=e67]:
            - generic [ref=e68]: Status
            - combobox [ref=e69]:
              - option "All statuses" [selected]
              - option "Available"
              - option "Dispatched"
              - option "Completed"
              - option "Unavailable"
          - generic [ref=e70]:
            - generic [ref=e71]: Location
            - combobox [ref=e72]:
              - option "All locations" [selected]
              - option "Site A"
              - option "Site B"
              - option "Site C"
        - table [ref=e74]:
          - rowgroup [ref=e75]:
            - row [ref=e76]:
              - columnheader "ID" [ref=e77]
              - columnheader "Type" [ref=e78]
              - columnheader "Location" [ref=e79]
              - columnheader "Potential" [ref=e80]
              - columnheader "Expected" [ref=e81]
              - columnheader "Trusted" [ref=e82]
              - columnheader "Confidence" [ref=e83]
              - columnheader "Status" [ref=e84]
              - columnheader "Constraint" [ref=e85]
          - rowgroup [ref=e86]:
            - button [ref=e87] [cursor=pointer]:
              - cell "ev-fleet-01" [ref=e88]
              - cell "ev" [ref=e89]
              - cell "site-a" [ref=e90]
              - cell "120" [ref=e91]
              - cell "95" [ref=e92]
              - cell "85" [ref=e93]
              - cell "91%" [ref=e94]
              - cell [ref=e95]:
                - status "Active status" [ref=e96]: Active
              - cell [ref=e98]:
                - status "Normal status" [ref=e99]: Normal
            - button [ref=e101] [cursor=pointer]:
              - cell "wh-building-a" [ref=e102]
              - cell "water heater" [ref=e103]
              - cell "site-a" [ref=e104]
              - cell "75" [ref=e105]
              - cell "60" [ref=e106]
              - cell "58" [ref=e107]
              - cell "86%" [ref=e108]
              - cell [ref=e109]:
                - status "Active status" [ref=e110]: Active
              - cell [ref=e112]:
                - status "Normal status" [ref=e113]: Normal
            - button [ref=e115] [cursor=pointer]:
              - cell "industrial-batch-02" [ref=e116]
              - cell "industrial batch" [ref=e117]
              - cell "site-b" [ref=e118]
              - cell "200" [ref=e119]
              - cell "180" [ref=e120]
              - cell "170" [ref=e121]
              - cell "89%" [ref=e122]
              - cell [ref=e123]:
                - status "Complete status" [ref=e124]: Complete
              - cell [ref=e126]:
                - status "Normal status" [ref=e127]: Normal
            - button [ref=e129] [cursor=pointer]:
              - cell "ev-fleet-02" [ref=e130]
              - cell "ev" [ref=e131]
              - cell "site-b" [ref=e132]
              - cell "90" [ref=e133]
              - cell "75" [ref=e134]
              - cell "70" [ref=e135]
              - cell "88%" [ref=e136]
              - cell [ref=e137]:
                - status "Inactive status" [ref=e138]: Inactive
              - cell [ref=e140]:
                - status "Normal status" [ref=e141]: Normal
            - button [ref=e143] [cursor=pointer]:
              - cell "wh-building-b" [ref=e144]
              - cell "water heater" [ref=e145]
              - cell "site-c" [ref=e146]
              - cell "60" [ref=e147]
              - cell "50" [ref=e148]
              - cell "48" [ref=e149]
              - cell "85%" [ref=e150]
              - cell [ref=e151]:
                - status "Active status" [ref=e152]: Active
              - cell [ref=e154]:
                - status "Normal status" [ref=e155]: Normal
            - button [ref=e157] [cursor=pointer]:
              - cell "industrial-batch-01" [ref=e158]
              - cell "industrial batch" [ref=e159]
              - cell "site-a" [ref=e160]
              - cell "150" [ref=e161]
              - cell "135" [ref=e162]
              - cell "130" [ref=e163]
              - cell "87%" [ref=e164]
              - cell [ref=e165]:
                - status "Active status" [ref=e166]: Active
              - cell [ref=e168]:
                - status "Normal status" [ref=e169]: Normal
            - button [ref=e171] [cursor=pointer]:
              - cell "ev-fleet-03" [ref=e172]
              - cell "ev" [ref=e173]
              - cell "site-b" [ref=e174]
              - cell "100" [ref=e175]
              - cell "80" [ref=e176]
              - cell "70" [ref=e177]
              - cell "83%" [ref=e178]
              - cell [ref=e179]:
                - status "Active status" [ref=e180]: Active
              - cell [ref=e182]:
                - status "Normal status" [ref=e183]: Normal
            - button [ref=e185] [cursor=pointer]:
              - cell "wh-building-c" [ref=e186]
              - cell "water heater" [ref=e187]
              - cell "site-c" [ref=e188]
              - cell "55" [ref=e189]
              - cell "45" [ref=e190]
              - cell "42" [ref=e191]
              - cell "78%" [ref=e192]
              - cell [ref=e193]:
                - status "Active status" [ref=e194]: Active
              - cell [ref=e196]:
                - status "Normal status" [ref=e197]: Normal
            - button [ref=e199] [cursor=pointer]:
              - cell "industrial-batch-03" [ref=e200]
              - cell "industrial batch" [ref=e201]
              - cell "site-a" [ref=e202]
              - cell "180" [ref=e203]
              - cell "160" [ref=e204]
              - cell "155" [ref=e205]
              - cell "86%" [ref=e206]
              - cell [ref=e207]:
                - status "Complete status" [ref=e208]: Complete
              - cell [ref=e210]:
                - status "Warning status" [ref=e211]: Warning
            - button [ref=e213] [cursor=pointer]:
              - cell "ev-fleet-04" [ref=e214]
              - cell "ev" [ref=e215]
              - cell "site-c" [ref=e216]
              - cell "80" [ref=e217]
              - cell "65" [ref=e218]
              - cell "60" [ref=e219]
              - cell "89%" [ref=e220]
              - cell [ref=e221]:
                - status "Inactive status" [ref=e222]: Inactive
              - cell [ref=e224]:
                - status "Normal status" [ref=e225]: Normal
            - button [ref=e227] [cursor=pointer]:
              - cell "wh-building-d" [ref=e228]
              - cell "water heater" [ref=e229]
              - cell "site-b" [ref=e230]
              - cell "90" [ref=e231]
              - cell "78" [ref=e232]
              - cell "73" [ref=e233]
              - cell "84%" [ref=e234]
              - cell [ref=e235]:
                - status "Active status" [ref=e236]: Active
              - cell [ref=e238]:
                - status "Normal status" [ref=e239]: Normal
            - button [ref=e241] [cursor=pointer]:
              - cell "industrial-batch-04" [ref=e242]
              - cell "industrial batch" [ref=e243]
              - cell "site-c" [ref=e244]
              - cell "250" [ref=e245]
              - cell "220" [ref=e246]
              - cell "200" [ref=e247]
              - cell "75%" [ref=e248]
              - cell [ref=e249]:
                - status "Active status" [ref=e250]: Active
              - cell [ref=e252]:
                - status "Warning status" [ref=e253]: Warning
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const BASE_URL = 'http://localhost:5173';
  4  | const VIEWPORTS = [
  5  |   { width: 1920, height: 1080 },
  6  |   { width: 1366, height: 768 },
  7  |   { width: 1024, height: 768 },
  8  |   { width: 768, height: 1024 },
  9  |   { width: 375, height: 812 }
  10 | ];
  11 | const PAGES = [
  12 |   '/overview',
  13 |   '/flexibility',
  14 |   '/dispatch',
  15 |   '/experiments'
  16 | ];
  17 | 
  18 | for (const v of VIEWPORTS) {
  19 |   for (const p of PAGES) {
  20 |     test(`Viewport ${v.width}x${v.height} - Page ${p.replace('/', '')}`, async ({ page }) => {
  21 |       await page.setViewportSize({ width: v.width, height: v.height });
  22 |       
  23 |       const errors: string[] = [];
  24 |       page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  25 |       page.on('pageerror', e => { errors.push(e.message); });
  26 |       
  27 |       await page.goto(`${BASE_URL}${p}`);
  28 |       await page.waitForSelector('#root');
  29 |       
  30 |       const hasOverflow = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
> 31 |       expect(hasOverflow).toBe(false);
     |                           ^ Error: expect(received).toBe(expected) // Object.is equality
  32 |       
  33 |       const faviconOk = await page.evaluate(() => {
  34 |         const link = document.querySelector('link[rel="icon"]');
  35 |         return link !== null;
  36 |       });
  37 |       expect(faviconOk).toBe(true);
  38 |       
  39 |       const jsxErrors = errors.filter(e => e.toLowerCase().includes('jsx') && e.toLowerCase().includes('attribute'));
  40 |       expect(jsxErrors).toEqual([]);
  41 |       
  42 |       const faviconErrors = errors.filter(e => e.toLowerCase().includes('favicon'));
  43 |       expect(faviconErrors).toEqual([]);
  44 |     });
  45 |   }
  46 | }
```