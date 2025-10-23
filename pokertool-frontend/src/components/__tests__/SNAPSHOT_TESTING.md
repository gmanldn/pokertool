# Snapshot Testing Guide

Snapshot tests capture the rendered output of React components and detect unintended changes.

## Running Snapshot Tests

```bash
# Run all tests including snapshots
npm test

# Run snapshot tests only
npm test -- --testNamePattern="Snapshot"

# Update snapshots (when changes are intentional)
npm test -- -u
```

## When to Use Snapshots

**✅ Good Use Cases:**
- Component structure and props
- Static content rendering
- Error states and empty states
- Different component variations

**❌ Avoid Snapshots For:**
- Dynamic timestamps or IDs
- Frequently changing UI
- Components with random data
- Animation states

## Writing Snapshot Tests

### Basic Example

```typescript
import { render } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

it('renders correctly', () => {
  const { container } = render(<MyComponent />);
  expect(container.firstChild).toMatchSnapshot();
});
```

### With Props

```typescript
it('renders with props', () => {
  const { container } = render(
    <MyComponent
      title="Test Title"
      count={42}
      isActive={true}
    />
  );
  expect(container.firstChild).toMatchSnapshot();
});
```

### Multiple States

```typescript
it('renders loading state', () => {
  const { container } = render(<MyComponent isLoading={true} />);
  expect(container.firstChild).toMatchSnapshot();
});

it('renders error state', () => {
  const { container } = render(<MyComponent error="Failed to load" />);
  expect(container.firstChild).toMatchSnapshot();
});
```

## Reviewing Snapshot Changes

When snapshots fail:

1. **Review the diff carefully**
   - Is the change intentional?
   - Does it match your code changes?

2. **If change is correct:**
   ```bash
   npm test -- -u
   ```

3. **If change is unexpected:**
   - Fix your code
   - Re-run tests

## Snapshot File Organization

- Snapshots stored in `__snapshots__/` directory
- One snapshot file per test file
- Named: `ComponentName.snapshot.test.tsx.snap`
- **Commit snapshot files to git**

## Best Practices

1. **Keep snapshots small** - Test specific component parts
2. **Use descriptive test names** - Makes diffs easier to understand
3. **Review snapshot diffs in PRs** - Don't blindly update
4. **Combine with unit tests** - Snapshots don't test behavior
5. **Mock dynamic data** - Use fixed dates, IDs, etc.

## Example: Mocking Dynamic Data

```typescript
import { render } from '@testing-library/react';
import { HandDisplay } from '../HandDisplay';

// Mock Date for consistent snapshots
const FIXED_DATE = new Date('2025-01-01T00:00:00Z');

beforeAll(() => {
  jest.spyOn(global, 'Date').mockImplementation(() => FIXED_DATE as any);
});

afterAll(() => {
  jest.restoreAllMocks();
});

it('renders hand with timestamp', () => {
  const { container } = render(<HandDisplay hand={mockHand} />);
  expect(container.firstChild).toMatchSnapshot();
});
```

## Snapshot vs Unit Tests

| Snapshot Tests | Unit Tests |
|---|---|
| Structure and rendering | Behavior and logic |
| Quick to write | More explicit |
| Detect any change | Test specific scenarios |
| Large diffs | Focused assertions |

**Use both!** Snapshots catch visual regressions, unit tests verify functionality.

## CI Integration

Snapshots run automatically in CI:
- Fail if snapshots don't match
- Prevent accidental UI changes
- Must update snapshots in same PR as changes

## Troubleshooting

**Problem:** Snapshots fail on CI but pass locally
- **Solution:** Ensure consistent Node version, check for platform-specific rendering

**Problem:** Large snapshot diffs are hard to review
- **Solution:** Break component into smaller testable pieces

**Problem:** Snapshots too brittle (fail often)
- **Solution:** Mock dynamic parts, test smaller components

## Further Reading

- [Jest Snapshot Testing](https://jestjs.io/docs/snapshot-testing)
- [RTL Best Practices](https://testing-library.com/docs/react-testing-library/intro)
