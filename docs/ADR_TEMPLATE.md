# ADR [Number]: [Title]

**Date**: YYYY-MM-DD  
**Status**: [Proposed | Accepted | Deprecated | Superseded]  
**Deciders**: [List of people involved]  
**Technical Story**: [GitHub issue/ticket number]

## Context and Problem Statement

[Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question.]

**Example**:
> We need to choose a database for storing hand history. The system must handle high write throughput (100+ hands/sec) while providing fast query access for analysis. We must decide between PostgreSQL, MongoDB, and SQLite.

## Decision Drivers

- [driver 1, e.g., a force, facing concern, ...]
- [driver 2, e.g., a force, facing concern, ...]
- [...]

**Example**:
- Must handle 100+ writes/second during tournaments
- Query performance for analytics and reporting
- Ease of deployment and maintenance
- Cost considerations
- Team expertise

## Considered Options

- [option 1]
- [option 2]
- [option 3]
- [...]

## Decision Outcome

**Chosen option**: "[option 1]"

[Justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force | ... | comes out best (see below).]

### Positive Consequences

- [e.g., improvement of quality attribute satisfaction, follow-up decisions required, ...]
- [...]

### Negative Consequences

- [e.g., compromising quality attribute, follow-up decisions required, ...]
- [...]

## Pros and Cons of the Options

### [option 1]

[example | description | pointer to more information | ...]

**Pros**:
- [argument a]
- [argument b]

**Cons**:
- [argument c]
- [argument d]

### [option 2]

[example | description | pointer to more information | ...]

**Pros**:
- [argument a]
- [argument b]

**Cons**:
- [argument c]
- [argument d]

### [option 3]

[example | description | pointer to more information | ...]

**Pros**:
- [argument a]
- [argument b]

**Cons**:
- [argument c]
- [argument d]

## Links

- [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->
- [Related documentation]
- [Technical specifications]

---

## Example: Completed ADR

# ADR 001: Use FastAPI for Backend Framework

**Date**: 2025-01-15  
**Status**: Accepted  
**Deciders**: Backend Team, Architecture Team  
**Technical Story**: #45

## Context and Problem Statement

We need to choose a Python web framework for the PokerTool backend API. The framework must support:
- High performance (low latency for real-time poker decisions)
- WebSocket support for live updates
- Automatic API documentation
- Type safety with Python type hints
- Easy testing

## Decision Drivers

- Real-time performance requirements (<100ms response time)
- Developer productivity and ease of testing
- Type safety to prevent runtime errors
- Built-in API documentation (OpenAPI/Swagger)
- Active community and ecosystem
- WebSocket support for live table updates

## Considered Options

- FastAPI
- Flask + extensions
- Django REST Framework
- Sanic

## Decision Outcome

**Chosen option**: "FastAPI"

FastAPI provides the best combination of performance, developer experience, and type safety. Its automatic OpenAPI documentation generation and Pydantic validation significantly reduce boilerplate while improving code quality.

### Positive Consequences

- Automatic API documentation via Swagger UI
- Type safety with Pydantic models prevents errors
- Excellent performance (comparable to Node.js/Go)
- Built-in async/await support for concurrency
- Minimal boilerplate code
- Strong ecosystem and community

### Negative Consequences

- Newer framework (less mature than Flask/Django)
- Smaller ecosystem compared to Django
- Some team members need to learn async programming
- Fewer third-party integrations

## Pros and Cons of the Options

### FastAPI

**Pros**:
- Fastest Python framework (benchmarked)
- Automatic OpenAPI documentation
- Type hints used for validation
- Built-in async support
- Excellent developer experience

**Cons**:
- Newer (less battle-tested)
- Requires Python 3.10+
- Learning curve for async patterns

### Flask + extensions

**Pros**:
- Very mature and stable
- Large ecosystem of extensions
- Team familiar with Flask
- Simple to understand

**Cons**:
- Slower performance
- Manual API documentation
- No built-in type validation
- Async support requires extensions

### Django REST Framework

**Pros**:
- Extremely mature
- Comprehensive admin interface
- Built-in ORM
- Strong security defaults

**Cons**:
- Heavyweight for API-only service
- Slower than FastAPI
- More boilerplate
- Less suitable for real-time

### Sanic

**Pros**:
- Very fast (async-first)
- Flask-like syntax
- Good performance

**Cons**:
- Smaller community
- Less documentation
- No automatic API docs
- Fewer extensions

## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Performance Benchmarks](https://fastapi.tiangolo.com/benchmarks/)
- [Implementation PR](https://github.com/gmanldn/pokertool/pull/45)
- Supersedes: ADR-000 (Initial Flask implementation)