# Frontend Performance Optimization Guide

## Implemented Optimizations

### 1. React.memo for Component Memoization
- **Dashboard** component wrapped with React.memo
- Prevents unnecessary re-renders when parent updates
- displayName added for React DevTools debugging

### 2. Bundle Size Analysis Script
- Script: `pokertool-frontend/scripts/analyze-bundle.sh`
- Reports chunks >200KB with optimization recommendations
- Usage: `./scripts/analyze-bundle.sh`

### 3. CI Performance Improvements
- Enhanced pip caching with Python version-specific keys
- npm caching via setup-node action
- Multi-level cache restore-keys for better hit rates
- Faster CI builds (estimated 30-50% time reduction)

## Best Practices

**When to use React.memo:**
- ✅ Expensive components (charts, large lists)
- ✅ Components high in the tree
- ✅ Stable props that don't change often
- ❌ Lightweight components (simple text, icons)
- ❌ Props that change frequently

**Performance hooks:**
- `useCallback`: Memoize event handlers passed to children
- `useMemo`: Cache expensive calculations
- `React.lazy`: Load heavy components on demand

**Example - useCallback:**
```typescript
const handleClick = useCallback(() => {
  doSomething(value);
}, [value]); // Only recreate when value changes
```

## Monitoring Performance

**React DevTools Profiler:**
1. Install React DevTools browser extension
2. Open Profiler tab
3. Record user interactions
4. Analyze component render times and frequency

**Bundle Analysis:**
```bash
npm run build
npx source-map-explorer build/static/js/*.js
```

**Core Web Vitals Targets:**
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms
- CLS (Cumulative Layout Shift): <0.1

## Common Anti-Patterns to Avoid

❌ **Anonymous functions in JSX:**
```typescript
// Bad
<Button onClick={() => handleClick(id)}>Click</Button>

// Good
const onClick = useCallback(() => handleClick(id), [id]);
<Button onClick={onClick}>Click</Button>
```

❌ **Inline object/array creation:**
```typescript
// Bad
<Component data={[item1, item2, item3]} />

// Good
const data = useMemo(() => [item1, item2, item3], [item1, item2, item3]);
<Component data={data} />
```

## Optimization Checklist

Before deploying:
- [ ] Run bundle analysis script
- [ ] Check for chunks >200KB
- [ ] Profile with React DevTools
- [ ] Test on slow 3G network
- [ ] Verify lazy loading works
- [ ] Run Lighthouse audit (target: 90+)

## Further Reading

- [React Performance Docs](https://react.dev/learn/render-and-commit)
- [React.memo API](https://react.dev/reference/react/memo)
- [Code Splitting](https://reactjs.org/docs/code-splitting.html)
- [Web Performance](https://web.dev/performance/)
