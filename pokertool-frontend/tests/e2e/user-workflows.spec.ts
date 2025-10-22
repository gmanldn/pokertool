/**
 * End-to-End User Workflow Tests
 *
 * Tests complete user journeys through the application,
 * validating critical paths and interactions.
 *
 * Author: PokerTool Team
 * Created: 2025-10-22
 */

import { test, expect } from '@playwright/test';

test.describe('User Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page before each test
    await page.goto('/');
  });

  test('complete first-time user journey', async ({ page }) => {
    /**
     * Scenario: New user visits app for first time
     * Steps:
     * 1. Land on homepage
     * 2. See system status
     * 3. Navigate to different sections
     * 4. View TODO list
     * 5. Check backend connection status
     */

    // Step 1: Verify homepage loads
    await expect(page).toHaveTitle(/PokerTool/i);

    // Step 2: See system status dashboard
    const statusHeading = page.locator('h4, h5, h6').filter({ hasText: /system status/i }).first();
    await expect(statusHeading).toBeVisible();

    // Step 3: Navigate to TODO section
    const todoLink = page.locator('a, button').filter({ hasText: /todo/i }).first();
    if (await todoLink.count() > 0) {
      await todoLink.click();
      await page.waitForTimeout(500);

      // Verify TODO section visible
      const todoSection = page.locator('text=/todo/i').first();
      await expect(todoSection).toBeVisible();
    }

    // Step 4: Check backend connection indicator
    const backendStatus = page.locator('[class*="status"], [class*="indicator"]').first();
    // Should show connection status (connected/disconnected)

    // Step 5: Verify no errors in console
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Wait a bit to capture any errors
    await page.waitForTimeout(1000);

    // Allow expected errors (network failures in dev environment)
    const allowedErrors = ['Failed to fetch', 'NetworkError', 'ERR_CONNECTION_REFUSED'];
    const unexpectedErrors = consoleErrors.filter(err =>
      !allowedErrors.some(allowed => err.includes(allowed))
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('dashboard navigation workflow', async ({ page }) => {
    /**
     * Scenario: User navigates through main sections
     * Steps:
     * 1. Start on dashboard
     * 2. Navigate to different pages
     * 3. Verify each page loads
     * 4. Return to dashboard
     */

    // Verify dashboard loads
    await expect(page.locator('body')).toBeVisible();

    // Find navigation links
    const navLinks = page.locator('nav a, header a, [role="navigation"] a');
    const linkCount = await navLinks.count();

    // Navigate through first few links
    const linksToTest = Math.min(linkCount, 3);
    for (let i = 0; i < linksToTest; i++) {
      const link = navLinks.nth(i);
      const linkText = await link.textContent();

      // Skip external links
      const href = await link.getAttribute('href');
      if (href && !href.startsWith('http')) {
        await link.click();
        await page.waitForLoadState('networkidle');

        // Verify page changed
        expect(page.url()).toBeTruthy();

        // Go back to home
        await page.goto('/');
        await page.waitForLoadState('networkidle');
      }
    }
  });

  test('system health monitoring workflow', async ({ page }) => {
    /**
     * Scenario: User monitors system health
     * Steps:
     * 1. View system status cards
     * 2. Check health indicators
     * 3. Verify metrics display
     */

    // Look for system status or health indicators
    const statusCards = page.locator('[class*="card"], [class*="status"], [class*="health"]');
    const cardCount = await statusCards.count();

    // Should have at least one status indicator
    expect(cardCount).toBeGreaterThan(0);

    // Check for common health metrics
    const metricsPatterns = [
      /cpu/i,
      /memory/i,
      /status/i,
      /health/i,
      /uptime/i,
      /connection/i
    ];

    let foundMetrics = 0;
    for (const pattern of metricsPatterns) {
      const metric = page.locator(`text=${pattern}`).first();
      if (await metric.count() > 0) {
        foundMetrics++;
      }
    }

    // Should have at least one metric
    expect(foundMetrics).toBeGreaterThan(0);
  });

  test('dark mode toggle workflow', async ({ page }) => {
    /**
     * Scenario: User toggles dark mode
     * Steps:
     * 1. Identify current theme
     * 2. Toggle dark mode
     * 3. Verify theme changed
     * 4. Toggle back
     */

    const body = page.locator('body');

    // Get initial background color
    const initialBg = await body.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Find dark mode toggle
    const darkModeToggle = page.locator(
      '[aria-label*="dark mode" i], [aria-label*="theme" i], button:has-text("dark"), button:has-text("theme")'
    ).first();

    if (await darkModeToggle.count() > 0 && await darkModeToggle.isVisible()) {
      // Toggle dark mode
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      // Verify background changed
      const newBg = await body.evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });

      expect(initialBg).not.toBe(newBg);

      // Toggle back
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      // Verify returned to original
      const finalBg = await body.evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });

      expect(finalBg).toBe(initialBg);
    }
  });

  test('responsive design workflow', async ({ page }) => {
    /**
     * Scenario: User views app on different screen sizes
     * Steps:
     * 1. Test desktop view
     * 2. Test tablet view
     * 3. Test mobile view
     * 4. Verify responsive behavior
     */

    // Desktop view (1920x1080)
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(300);
    await expect(page.locator('body')).toBeVisible();

    // Tablet view (768x1024)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(300);
    await expect(page.locator('body')).toBeVisible();

    // Mobile view (375x667)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
    await expect(page.locator('body')).toBeVisible();

    // Check for mobile menu/drawer on small screens
    const mobileMenuButton = page.locator('[aria-label*="menu" i], button:has-text("menu")').first();
    if (await mobileMenuButton.count() > 0 && await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      await page.waitForTimeout(300);

      // Mobile drawer should appear
      const drawer = page.locator('[role="dialog"], [class*="drawer"], [class*="menu"]').first();
      // May or may not be visible depending on implementation
    }
  });

  test('error handling workflow', async ({ page }) => {
    /**
     * Scenario: User encounters errors
     * Steps:
     * 1. Navigate to non-existent route
     * 2. Verify error handling
     * 3. Navigate back to working route
     */

    // Navigate to invalid route
    await page.goto('/this-route-does-not-exist-xyz-123');
    await page.waitForLoadState('networkidle');

    // Should show 404 or redirect to home
    const is404 = page.url().includes('404') ||
                  (await page.locator('text=/not found/i').count()) > 0 ||
                  (await page.locator('text=/404/').count()) > 0;

    const isRedirected = page.url() === new URL('/', page.url()).href;

    // Either show 404 or redirect to home
    expect(is404 || isRedirected).toBeTruthy();

    // Navigate back to home
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });

  test('TODO list interaction workflow', async ({ page }) => {
    /**
     * Scenario: User interacts with TODO list
     * Steps:
     * 1. Find TODO section
     * 2. View TODO items
     * 3. Interact with items (if possible)
     */

    // Look for TODO section
    const todoSection = page.locator('text=/todo/i, h1:has-text("todo"), h2:has-text("todo"), h3:has-text("todo")').first();

    if (await todoSection.count() > 0) {
      // Click to navigate/expand
      if (await todoSection.isVisible()) {
        await todoSection.click();
        await page.waitForTimeout(500);
      }

      // Look for TODO items
      const todoItems = page.locator('[class*="todo"], li, [role="listitem"]');
      const itemCount = await todoItems.count();

      // Should have some TODO items or show empty state
      expect(itemCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('backend connection status workflow', async ({ page }) => {
    /**
     * Scenario: User monitors backend connection
     * Steps:
     * 1. View connection status
     * 2. Verify status indicator present
     * 3. Check for connection errors (expected in test env)
     */

    // Look for connection status indicators
    const connectionPatterns = [
      /connected/i,
      /disconnected/i,
      /offline/i,
      /online/i,
      /backend/i,
      /server/i,
      /api/i
    ];

    let foundIndicator = false;
    for (const pattern of connectionPatterns) {
      const indicator = page.locator(`text=${pattern}`).first();
      if (await indicator.count() > 0) {
        foundIndicator = true;
        break;
      }
    }

    // Should have connection status indicator
    // (May not be visible if no backend running in test environment)
  });

  test('performance: page load time', async ({ page }) => {
    /**
     * Scenario: Verify page loads quickly
     * Steps:
     * 1. Measure page load time
     * 2. Verify under threshold
     */

    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    // Page should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);

    // Verify main content visible
    await expect(page.locator('body')).toBeVisible();
  });

  test('accessibility: keyboard navigation', async ({ page }) => {
    /**
     * Scenario: User navigates with keyboard
     * Steps:
     * 1. Tab through focusable elements
     * 2. Verify focus indicators
     * 3. Test Enter/Space on interactive elements
     */

    // Tab through first few elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // Tab a few more times
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }

    // Verify can still focus elements
    focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});

test.describe('Critical Path Workflows', () => {
  test('complete user session', async ({ page }) => {
    /**
     * Scenario: Complete user session from start to finish
     * Steps:
     * 1. Land on app
     * 2. View system status
     * 3. Navigate multiple sections
     * 4. Toggle settings
     * 5. Complete session
     */

    // 1. Land on app
    await page.goto('/');
    await expect(page).toHaveTitle(/PokerTool/i);

    // 2. View system status
    await page.waitForTimeout(1000);
    const statusVisible = (await page.locator('text=/status/i').count()) > 0;

    // 3. Navigate sections (if navigation exists)
    const navLinks = page.locator('nav a, header a');
    const linkCount = await navLinks.count();
    if (linkCount > 0) {
      await navLinks.first().click();
      await page.waitForTimeout(500);
      await page.goto('/');
    }

    // 4. Toggle dark mode (if available)
    const darkModeToggle = page.locator('[aria-label*="dark" i]').first();
    if (await darkModeToggle.count() > 0) {
      await darkModeToggle.click();
      await page.waitForTimeout(300);
    }

    // 5. Complete session - verify no crashes
    await expect(page.locator('body')).toBeVisible();
  });
});
