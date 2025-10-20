# Code Review Checklist

Comprehensive checklist for reviewing pull requests in PokerTool.

## Pre-Review Setup

- [ ] Pull the branch locally and test it
- [ ] Review linked issue/task for context
- [ ] Check CI/CD pipeline status (all checks passing)
- [ ] Review the PR description and scope

## Code Quality

### General Code Standards

- [ ] Code follows project style guide (Black, isort, pylint)
- [ ] No unnecessary code duplication
- [ ] Functions are small and focused (< 50 lines ideal)
- [ ] Variable/function names are clear and descriptive
- [ ] No commented-out code (remove or explain why kept)
- [ ] No debug print statements or console.logs
- [ ] Code is readable without excessive complexity

### Python-Specific

- [ ] Type hints present on all function signatures
- [ ] Docstrings follow Google/NumPy style
- [ ] Uses f-strings for string formatting (not %)
- [ ] Proper exception handling (no bare `except:`)
- [ ] Context managers used for resources (with statements)
- [ ] List/dict comprehensions used appropriately
- [ ] No mutable default arguments

### TypeScript/React-Specific

- [ ] Components are functional (not class-based unless necessary)
- [ ] Hooks used correctly (dependencies, cleanup)
- [ ] Props have TypeScript interfaces defined
- [ ] No `any` types (use proper typing)
- [ ] useCallback/useMemo used to prevent re-renders
- [ ] Accessibility attributes (aria-labels, roles)

## Architecture & Design

- [ ] Changes align with project architecture
- [ ] No God objects or classes (Single Responsibility)
- [ ] Proper separation of concerns
- [ ] Dependencies injected, not hard-coded
- [ ] Configuration in config files, not code
- [ ] No magic numbers/strings (use constants)
- [ ] Appropriate use of design patterns

## Testing

### Test Coverage

- [ ] New code has unit tests (>90% coverage)
- [ ] Edge cases are tested
- [ ] Error paths are tested
- [ ] Integration tests for new features
- [ ] All tests pass locally
- [ ] No flaky or skipped tests without justification

### Test Quality

- [ ] Tests are isolated and independent
- [ ] Test names clearly describe what is tested
- [ ] Mocks/fixtures are used appropriately
- [ ] Test data is realistic
- [ ] Assertions are specific and meaningful
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)

## Security

- [ ] No hardcoded credentials or secrets
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized outputs)
- [ ] CSRF protection on state-changing endpoints
- [ ] Authentication/authorization checks where needed
- [ ] Sensitive data encrypted at rest/transit
- [ ] No exposure of stack traces to users

## Performance

- [ ] No N+1 query problems
- [ ] Database queries have appropriate indexes
- [ ] Expensive operations are cached
- [ ] Large datasets paginated
- [ ] Image/asset optimization
- [ ] No memory leaks (resources cleaned up)
- [ ] Async operations used where appropriate
- [ ] Bundle size impact assessed (frontend)

## Error Handling & Logging

- [ ] Errors are handled gracefully
- [ ] User-friendly error messages
- [ ] Appropriate logging (INFO, DEBUG, ERROR levels)
- [ ] Sensitive data not logged
- [ ] Error context included in logs
- [ ] Correlation IDs used for request tracing
- [ ] Monitoring/alerts configured for critical errors

## Documentation

- [ ] README updated if needed
- [ ] API documentation updated (if API changes)
- [ ] CHANGELOG.md updated
- [ ] Complex logic has inline comments
- [ ] Breaking changes documented
- [ ] Migration guide provided (if needed)
- [ ] Environment variables documented

## Database Changes

- [ ] Migration scripts provided
- [ ] Migration is reversible (down migration)
- [ ] Migration tested on copy of production data
- [ ] Indexes added where needed
- [ ] No data loss in migration
- [ ] Backward compatible if possible

## API Changes

- [ ] API versioning respected
- [ ] Breaking changes avoided or versioned
- [ ] Request/response models documented
- [ ] Error codes documented
- [ ] Rate limiting considered
- [ ] OpenAPI/Swagger spec updated

## Frontend-Specific

- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading states implemented
- [ ] Error states handled gracefully
- [ ] Accessibility (WCAG 2.1 AA compliant)
- [ ] SEO considerations (if applicable)
- [ ] Browser compatibility tested
- [ ] No console errors or warnings

## Dependencies

- [ ] New dependencies justified
- [ ] Dependencies are up-to-date
- [ ] License compatibility checked
- [ ] Security vulnerabilities checked (npm audit, safety)
- [ ] Dependency version pinned appropriately
- [ ] Bundle size impact assessed

## Git & Version Control

- [ ] Commit messages are clear and descriptive
- [ ] Commits are logically organized
- [ ] No merge commits (rebased if needed)
- [ ] Branch is up-to-date with main/develop
- [ ] No conflicts
- [ ] Commit history is clean

## Deployment

- [ ] Environment variables documented
- [ ] Configuration changes documented
- [ ] Deployment plan provided (if complex)
- [ ] Rollback plan considered
- [ ] Feature flags used for risky changes
- [ ] Monitoring configured for new features

## Specific to PokerTool

### Poker Logic

- [ ] Poker rules correctly implemented
- [ ] Hand evaluations are accurate
- [ ] GTO calculations validated
- [ ] Betting logic handles edge cases
- [ ] Position tracking is correct

### Screen Scraping

- [ ] OCR accuracy validated on test images
- [ ] ROI extraction handles different resolutions
- [ ] Table detection works across poker sites
- [ ] Error recovery for failed scrapes
- [ ] Performance impact minimized

### Machine Learning

- [ ] Model inputs/outputs validated
- [ ] Training data quality assessed
- [ ] Model performance metrics documented
- [ ] Bias and fairness considered
- [ ] Model versioning implemented

## Review Process

### As Reviewer

1. **Understand**: Read PR description and linked issues
2. **Test**: Pull branch and test locally
3. **Review**: Go through checklist systematically
4. **Comment**: Leave clear, actionable feedback
5. **Approve**: Only when all critical issues resolved

### Comment Guidelines

- Be respectful and constructive
- Explain the "why" not just the "what"
- Suggest specific improvements
- Use prefixes:
  - `[CRITICAL]` - Must fix before merge
  - `[SUGGESTION]` - Nice to have
  - `[QUESTION]` - Need clarification
  - `[PRAISE]` - Good work!

### Example Comments

**Good**:
```
[SUGGESTION] Consider using a list comprehension here for better readability:
users = [user for user in all_users if user.is_active]
```

**Bad**:
```
This code is bad
```

## Approval Criteria

**Approve if**:
- All critical issues resolved
- Tests passing
- Documentation complete
- Security concerns addressed
- Performance acceptable

**Request Changes if**:
- Critical bugs present
- Tests failing or missing
- Security vulnerabilities
- Performance regression
- Breaking changes without migration

**Comment Only if**:
- Minor style issues
- Suggestions for future improvements
- Questions for clarification

## After Approval

- [ ] Squash commits if needed
- [ ] Update PR title/description
- [ ] Notify team in Slack/Discord
- [ ] Monitor deployment

## Quick Reference

### For Small PRs (< 100 lines)
Focus on:
- Code quality
- Tests
- Security
- Documentation

### For Large PRs (> 500 lines)
- Review in chunks
- Request breakdown if too large
- Extra attention to architecture
- Thorough testing

### For Urgent Hotfixes
- Focus on correctness
- Security implications
- Rollback plan
- Can defer style/docs improvements

## Tools

Use these tools to assist review:

```bash
# Run linters
black --check .
pylint src/
mypy src/

# Run tests
pytest tests/ -v

# Check test coverage
pytest --cov=src tests/

# Security scan
bandit -r src/
npm audit

# Type check frontend
cd pokertool-frontend && npm run type-check
```

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [React Best Practices](https://react.dev/learn)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PokerTool Architecture](ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)