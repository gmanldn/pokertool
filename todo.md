# PokerTool TODO List

## Smoke Test Suite - End-to-End Validation

### High Priority - Smoke Tests
- [x] Create comprehensive smoke test suite
- [x] Test backend API health and endpoints
- [x] Test frontend build and deployment
- [x] Test database connectivity and operations
- [x] Test screen scraper initialization
- [x] Test ML features (GTO, opponent modeling)
- [x] Test WebSocket real-time communication
- [x] Test authentication flow
- [x] Test end-to-end workflow (scrape → analyze → advise)
- [x] Create standalone smoke test runner script
- [x] Integrate with CI/CD pipeline

### Testing Infrastructure
- [ ] Add smoke test documentation
- [ ] Create smoke test CI/CD workflow
- [ ] Add smoke test badges to README
- [ ] Setup automated smoke test reports
- [ ] Create smoke test metrics dashboard

### Future Enhancements
- [ ] Add performance benchmarking to smoke tests
- [ ] Add load testing scenarios
- [ ] Add security smoke tests
- [ ] Add cross-browser smoke tests for frontend
- [ ] Add mobile responsiveness smoke tests

## Notes
- Smoke tests should complete in <2 minutes
- All smoke tests must be non-destructive
- Smoke tests suitable for pre-deployment validation
- Run smoke tests before every release
