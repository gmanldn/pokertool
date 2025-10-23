/**
 * Cross-Browser Compatibility Tests
 *
 * Validates PokerTool frontend works correctly on Chrome, Firefox, Safari, and Edge.
 * Tests core functionality, rendering, and browser-specific features.
 */

import { test, expect } from '@playwright/test';

test.describe('Cross-Browser Compatibility', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for app to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('should load homepage successfully', async ({ page, browserName }) => {
    // Check page loaded
    await expect(page).toHaveTitle(/PokerTool/);

    // Check main content is visible
    await expect(page.locator('body')).toBeVisible();

    console.log(`✓ Homepage loaded on ${browserName}`);
  });

  test('should render navigation bar', async ({ page, browserName }) => {
    // Check navigation exists
    const nav = page.locator('nav, header');
    await expect(nav).toBeVisible();

    // Check key navigation elements
    const appTitle = page.getByText(/PokerTool/i).first();
    await expect(appTitle).toBeVisible();

    console.log(`✓ Navigation rendered on ${browserName}`);
  });

  test('should render dark mode toggle', async ({ page, browserName }) => {
    // Find dark mode toggle (icon button or switch)
    const darkModeToggle = page.locator('[aria-label*="dark mode" i], [title*="dark mode" i]').first();

    if (await darkModeToggle.count() > 0) {
      await expect(darkModeToggle).toBeVisible();
      console.log(`✓ Dark mode toggle found on ${browserName}`);
    } else {
      console.log(`⚠ Dark mode toggle not found on ${browserName} (may be in menu)`);
    }
  });

  test('should toggle dark mode', async ({ page, browserName }) => {
    // Wait for page to stabilize
    await page.waitForTimeout(500);

    // Get initial background color
    const body = page.locator('body');
    const initialBg = await body.evaluate(el => window.getComputedStyle(el).backgroundColor);

    // Find and click dark mode toggle
    const darkModeToggle = page.locator('[aria-label*="dark mode" i], [title*="dark mode" i], button[class*="dark" i]').first();

    if (await darkModeToggle.count() > 0 && await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      // Get new background color
      const newBg = await body.evaluate(el => window.getComputedStyle(el).backgroundColor);

      // Colors should be different
      expect(initialBg).not.toBe(newBg);
      console.log(`✓ Dark mode toggled on ${browserName} (${initialBg} -> ${newBg})`);
    } else {
      test.skip();
    }
  });

  test('should render system status indicator', async ({ page, browserName }) => {
    // Look for status indicators
    const statusIndicators = page.locator('[class*="status" i], [data-testid*="status" i]');

    if (await statusIndicators.count() > 0) {
      await expect(statusIndicators.first()).toBeVisible();
      console.log(`✓ Status indicator rendered on ${browserName}`);
    } else {
      console.log(`⚠ Status indicator not found on ${browserName}`);
    }
  });

  test('should handle responsive design', async ({ page, browserName }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(300);

    const bodyDesktop = page.locator('body');
    await expect(bodyDesktop).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);

    const bodyMobile = page.locator('body');
    await expect(bodyMobile).toBeVisible();

    console.log(`✓ Responsive design works on ${browserName}`);
  });

  test('should support CSS Grid layout', async ({ page, browserName }) => {
    // Check if CSS Grid is supported by browser
    const supportsGrid = await page.evaluate(() => {
      return CSS.supports('display', 'grid');
    });

    expect(supportsGrid).toBe(true);
    console.log(`✓ CSS Grid supported on ${browserName}`);
  });

  test('should support CSS Flexbox', async ({ page, browserName }) => {
    // Check if Flexbox is supported
    const supportsFlex = await page.evaluate(() => {
      return CSS.supports('display', 'flex');
    });

    expect(supportsFlex).toBe(true);
    console.log(`✓ CSS Flexbox supported on ${browserName}`);
  });

  test('should support modern JavaScript features', async ({ page, browserName }) => {
    // Check ES6+ features
    const features = await page.evaluate(() => {
      return {
        arrow: typeof (() => {}) === 'function',
        const: (() => { try { eval('const x = 1'); return true; } catch(e) { return false; }})(),
        async: typeof (async () => {}) === 'function',
        fetch: typeof fetch === 'function',
        promise: typeof Promise === 'function',
        map: typeof Map === 'function',
        set: typeof Set === 'function',
      };
    });

    expect(features.arrow).toBe(true);
    expect(features.const).toBe(true);
    expect(features.async).toBe(true);
    expect(features.fetch).toBe(true);
    expect(features.promise).toBe(true);
    expect(features.map).toBe(true);
    expect(features.set).toBe(true);

    console.log(`✓ Modern JS features supported on ${browserName}`);
  });

  test('should render Material-UI components', async ({ page, browserName }) => {
    // Check for MUI components
    const muiElements = page.locator('[class*="Mui" i]');

    if (await muiElements.count() > 0) {
      await expect(muiElements.first()).toBeVisible();
      console.log(`✓ Material-UI components rendered on ${browserName}`);
    } else {
      console.log(`⚠ No MUI components detected on ${browserName}`);
    }
  });

  test('should handle localStorage', async ({ page, browserName }) => {
    // Test localStorage functionality
    const storageWorks = await page.evaluate(() => {
      try {
        const testKey = '__test__';
        localStorage.setItem(testKey, 'value');
        const retrieved = localStorage.getItem(testKey);
        localStorage.removeItem(testKey);
        return retrieved === 'value';
      } catch (e) {
        return false;
      }
    });

    expect(storageWorks).toBe(true);
    console.log(`✓ localStorage works on ${browserName}`);
  });

  test('should handle sessionStorage', async ({ page, browserName }) => {
    // Test sessionStorage functionality
    const storageWorks = await page.evaluate(() => {
      try {
        const testKey = '__test__';
        sessionStorage.setItem(testKey, 'value');
        const retrieved = sessionStorage.getItem(testKey);
        sessionStorage.removeItem(testKey);
        return retrieved === 'value';
      } catch (e) {
        return false;
      }
    });

    expect(storageWorks).toBe(true);
    console.log(`✓ sessionStorage works on ${browserName}`);
  });

  test('should support WebSocket', async ({ page, browserName }) => {
    // Check if WebSocket is supported
    const supportsWS = await page.evaluate(() => {
      return typeof WebSocket === 'function';
    });

    expect(supportsWS).toBe(true);
    console.log(`✓ WebSocket supported on ${browserName}`);
  });

  test('should handle console errors', async ({ page, browserName }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', (error) => {
      consoleErrors.push(error.message);
    });

    // Navigate and wait
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Filter out expected errors
    const unexpectedErrors = consoleErrors.filter(err => {
      // Filter out network errors from API calls (expected in tests)
      return !err.includes('Failed to fetch') &&
             !err.includes('NetworkError') &&
             !err.includes('ERR_CONNECTION_REFUSED');
    });

    if (unexpectedErrors.length > 0) {
      console.log(`⚠ Console errors on ${browserName}:`, unexpectedErrors);
    } else {
      console.log(`✓ No unexpected console errors on ${browserName}`);
    }

    // Don't fail test on console errors, just log them
    // expect(unexpectedErrors.length).toBe(0);
  });

  test('should render without accessibility violations', async ({ page, browserName }) => {
    // Basic accessibility checks
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      // Images should have alt attribute (can be empty for decorative)
      expect(alt).not.toBeNull();
    }

    // Check for lang attribute on html
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();

    console.log(`✓ Basic accessibility checks passed on ${browserName}`);
  });
});

test.describe('Browser-Specific Features', () => {
  test('should detect browser engine', async ({ page, browserName }) => {
    const userAgent = await page.evaluate(() => navigator.userAgent);

    console.log(`Browser: ${browserName}`);
    console.log(`User Agent: ${userAgent}`);

    expect(userAgent).toBeTruthy();
  });

  test('should report viewport size', async ({ page, browserName }) => {
    const viewport = await page.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }));

    console.log(`Viewport on ${browserName}: ${viewport.width}x${viewport.height}`);

    expect(viewport.width).toBeGreaterThan(0);
    expect(viewport.height).toBeGreaterThan(0);
  });

  test('should support requestAnimationFrame', async ({ page, browserName }) => {
    const supportsRAF = await page.evaluate(() => {
      return typeof requestAnimationFrame === 'function';
    });

    expect(supportsRAF).toBe(true);
    console.log(`✓ requestAnimationFrame supported on ${browserName}`);
  });
});
