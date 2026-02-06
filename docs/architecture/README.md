# Architecture Documentation

Complete technical architecture for the Django To-Do Application with Network Graph Visualization.

## Quick Navigation

### Core Architecture
- **[Introduction](introduction.md)** - Purpose, scope, and key principles
- **[High-Level Architecture](high-level-architecture.md)** - System overview, component layers, and data flows
- **[Tech Stack](tech-stack.md)** - Technology choices with modern Python tooling (uv + ruff)

### Data & API Design
- **[Data Models](data-models.md)** - Database schema, relationships, and query patterns
- **[API Specification](api-specification.md)** - REST endpoints, request/response formats

### Project Structure
- **[Source Tree](source-tree.md)** - Complete project directory structure and file organization

### Development & Deployment
- **[Development Workflow](development-workflow.md)** - Setup, modern tooling (uv + ruff), IDE configuration
- **[Deployment Architecture](deployment-architecture.md)** - PythonAnywhere deployment, CI/CD with GitHub Actions
- **[Coding Standards](coding-standards.md)** - Code quality, style guide, best practices

### Quality Assurance
- **[Testing Strategy](testing-strategy.md)** - Unit, integration, and E2E testing with pytest and Playwright
- **[Security & Performance](security-performance.md)** - Authentication, authorization, input validation, query optimization

### Operations
- **[Error Handling Strategy](error-handling-strategy.md)** - Error responses, logging, user feedback
- **[Monitoring & Observability](monitoring-observability.md)** - Logging, metrics, health checks, Sentry integration

## Key Technologies

### Backend
- **Django 4.2 LTS** - Web framework
- **PostgreSQL 14+** - Database
- **Django REST Framework** - API layer

### Frontend
- **Alpine.js** - Reactive UI (15KB)
- **vis-network** - Graph visualization
- **Bootstrap 5.3** - CSS framework

### Modern Python Tooling
- **uv** - Package manager (10-100x faster than pip)
- **ruff** - Linting & formatting (replaces black, isort, flake8, pylint)

### Testing & Quality
- **pytest** - Test framework
- **Factory Boy** - Test data generation
- **Playwright** - E2E testing

### Deployment
- **PythonAnywhere** - Hosting platform
- **WhiteNoise** - Static file serving
- **GitHub Actions** - CI/CD
- **Sentry** - Error tracking & performance monitoring

## Getting Started

1. **Read the [Introduction](introduction.md)** for overview and principles
2. **Review [Tech Stack](tech-stack.md)** to understand technology choices
3. **Follow [Development Workflow](development-workflow.md)** to set up your environment
4. **Reference [Coding Standards](coding-standards.md)** while developing

## Architecture Highlights

✅ **Modern Python tooling** with uv and ruff for developer velocity
✅ **Monolithic Django architecture** optimized for PythonAnywhere
✅ **UUID primary keys** for security and scalability
✅ **Comprehensive testing** with 80%+ coverage target
✅ **Production-ready** security and performance optimizations
✅ **CI/CD pipeline** with automated testing and deployment

## Document Version

- **Architecture Version**: 1.0
- **Created**: 2026-01-24
- **Target**: Django To-Do App MVP (8-week timeline)

---

For questions or clarifications, refer to the specific section documents above.
