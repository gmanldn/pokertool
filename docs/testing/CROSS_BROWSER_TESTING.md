# Cross-Browser Testing Guide

**Author:** PokerTool Team
**Created:** 2025-10-22
**Version:** 1.0.0

## Overview

PokerTool uses Playwright for automated cross-browser compatibility testing. Tests verify that the application works correctly across Chrome, Firefox, Safari (WebKit), and Edge in both light and dark modes.

## Supported Browsers

| Browser | Engine | Light Mode | Dark Mode | Notes |
|---------|--------|------------|-----------|-------|
| **Chrome** | Chromium | ✅ | ✅ | Primary development browser |
| **Firefox** | Gecko | ✅ | ✅ | Second most popular |
| **Safari** | WebKit | ✅ | ✅ | macOS/iOS default browser |
| **Edge** | Chromium | ✅ | ✅ | Windows default browser |

## Test Coverage

The cross-browser test suite (`tests/cross-browser/browser-compatibility.spec.ts`) validates:

### Core Functionality
- ✅ Homepage loading and rendering
- ✅ Navigation bar display
- ✅ Dark mode toggle functionality
- ✅ System status indicators
- ✅ Responsive design (desktop + mobile)

### Browser Features
- ✅ CSS Grid support
- ✅ CSS Flexbox support
- ✅ Modern JavaScript (ES6+: arrow functions, async/await, fetch, Promise, Map, Set)
- ✅ localStorage and sessionStorage
- ✅ WebSocket support
- ✅ requestAnimationFrame

### Rendering
- ✅ Material-UI components
- ✅ Console error detection
- ✅ Basic accessibility (alt text, lang attribute)

## Running Tests

### Prerequisites

1. Install Playwright browsers (one-time setup):
```bash
cd pokertool-frontend
npx playwright install
```

This installs Chromium, Firefox, WebKit, and Edge browser binaries (~500MB total).

### Test Commands

**Run all browsers (all 8 configurations):**
```bash
npm run test:cross-browser
```

**Run specific browser:**
```bash
npm run test:cross-browser:chromium  # Chrome light + dark
npm run test:cross-browser:firefox   # Firefox light + dark
npm run test:cross-browser:webkit    # Safari light + dark
npm run test:cross-browser:edge      # Edge light + dark
```

**Run with UI mode (interactive debugging):**
```bash
npx playwright test tests/cross-browser --ui
```

**Run specific test:**
```bash
npx playwright test tests/cross-browser -g "should load homepage"
```

### CI/CD Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Install Playwright Browsers
  run: npx playwright install --with-deps
  working-directory: pokertool-frontend

- name: Run Cross-Browser Tests
  run: npm run test:cross-browser
  working-directory: pokertool-frontend

- name: Upload Test Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: pokertool-frontend/playwright-report/
```

## Test Results

Test reports are generated in HTML format:

```bash
pokertool-frontend/
  playwright-report/
    index.html          # Main report
    data/               # Test data
    trace-*.zip         # Traces for failed tests
```

Open report:
```bash
npx playwright show-report
```

## Browser-Specific Issues

### Known Compatibility Issues

| Issue | Browsers | Workaround | Status |
|-------|----------|------------|--------|
| WebSocket reconnection delay | Firefox | Increase timeout to 5s | ✅ Fixed |
| localStorage quota | Safari | Handle QuotaExceededError | ✅ Fixed |
| Flexbox gap property | Old Edge | Use margin fallback | ✅ Fixed |

### Browser Feature Detection

The application uses feature detection instead of user-agent sniffing:

```javascript
// Good: Feature detection
if (typeof WebSocket === 'function') {
  // Use WebSocket
}

// Bad: User-agent sniffing
if (navigator.userAgent.includes('Firefox')) {
  // Don't do this
}
```

## Debugging Failed Tests

### 1. View Test Report
```bash
npx playwright show-report
```

### 2. Run in Debug Mode
```bash
npx playwright test tests/cross-browser --debug
```

### 3. View Trace
```bash
npx playwright show-trace playwright-report/data/trace-xyz.zip
```

### 4. Take Screenshots
Tests automatically take screenshots on failure. Find them in:
```
playwright-report/screenshots/
```

## Adding New Tests

### Template

```typescript
test('should [do something]', async ({ page, browserName }) => {
  // Arrange
  await page.goto('/some-page');

  // Act
  const element = page.locator('[data-testid="my-element"]');
  await element.click();

  // Assert
  await expect(element).toHaveText('Expected Text');

  console.log(`✓ Test passed on ${browserName}`);
});
```

### Best Practices

1. **Use data-testid attributes** for reliable selectors
2. **Wait for networkidle** before asserting
3. **Log success messages** with browser name
4. **Handle browser differences** gracefully (use test.skip() if needed)
5. **Test both light and dark modes** when relevant

## Performance Benchmarks

Target performance across all browsers:

| Metric | Target | Notes |
|--------|--------|-------|
| Page Load Time | < 3s | First contentful paint |
| Time to Interactive | < 5s | Fully interactive |
| Layout Shift (CLS) | < 0.1 | Cumulative Layout Shift |
| First Input Delay | < 100ms | User interaction responsiveness |

Monitor with:
```bash
npx playwright test tests/cross-browser --project=chromium-light --trace on
```

Then view metrics in trace viewer.

## Troubleshooting

### Playwright Installation Issues

**Problem:** Browsers fail to install

**Solution:**
```bash
# Force reinstall
npx playwright install --force

# Install system dependencies (Linux)
npx playwright install-deps
```

### Tests Timeout

**Problem:** Tests hang or timeout

**Solution:**
1. Increase timeout in `playwright.config.ts`:
```typescript
use: {
  actionTimeout: 15000,  // 15 seconds
  navigationTimeout: 30000,  // 30 seconds
}
```

2. Or per-test:
```typescript
test.setTimeout(60000);  // 60 seconds
```

### WebKit Issues on Linux

**Problem:** WebKit doesn't launch on Linux

**Solution:**
```bash
# Install webkit dependencies
sudo npx playwright install-deps webkit
```

### Flaky Tests

**Problem:** Tests pass sometimes, fail sometimes

**Solution:**
1. Add explicit waits:
```typescript
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);
```

2. Use retry logic:
```typescript
await expect(async () => {
  const element = page.locator('[data-testid="my-element"]');
  await expect(element).toBeVisible();
}).toPass({ timeout: 10000 });
```

## Browser Version Matrix

### Current Test Versions

| Browser | Version | Last Updated |
|---------|---------|--------------|
| Chromium | 131.0.6778.33 | 2025-10-22 |
| Firefox | 132.0 | 2025-10-22 |
| WebKit | 18.2 | 2025-10-22 |
| Edge | 131.0.2903.27 | 2025-10-22 |

Update browsers:
```bash
npx playwright install
```

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Cross-Browser Testing Best Practices](https://playwright.dev/docs/best-practices)
- [Browser Compatibility Data](https://caniuse.com/)
- [WebKit Feature Status](https://webkit.org/status/)
- [Firefox Release Notes](https://www.mozilla.org/en-US/firefox/releases/)

## Next Steps

1. ✅ Expand test coverage to all pages
2. ✅ Add performance benchmarks
3. ✅ Integrate into CI/CD pipeline
4. ✅ Add visual regression tests
5. 🔄 Monitor browser update releases
6. 🔄 Test on real devices (BrowserStack/Sauce Labs)

---

**Last Updated:** 2025-10-22
**Maintained By:** PokerTool Team
