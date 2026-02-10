# Technical Assumptions

## Repository Structure: Monorepo
Single repository containing the complete Django application with clear app separation (tasks, tags, visualization) as outlined in your Project Brief's technical considerations.

## Service Architecture
**Monolithic Django application** initially, designed with clear API patterns for future microservice extraction if needed. This aligns with your 8-week MVP timeline, single developer constraint, and PythonAnywhere hosting approach. The architecture should include:
- Clean separation between apps (tasks, tags, visualization)
- RESTful API design patterns for future mobile app support
- Standard Django project structure with proper model relationships for tag queries

## Testing Requirements
**Unit + Integration testing** using Django's built-in test framework with pytest integration. Given the complex tag relationships and network graph functionality, both unit tests for individual components and integration tests for tag filtering workflows are essential. Manual testing convenience methods should be included for UI interaction testing.

## Additional Technical Assumptions and Requests

**Frontend Technology Stack:**
- Django templates with vanilla JavaScript or lightweight framework (Alpine.js/Stimulus) for interactivity
- D3.js or vis.js for network graph visualization (requires research and prototyping phase)
- CSS with proper responsive design patterns for desktop-first, mobile-friendly experience

**Backend & Database:**
- Django 4.x with PostgreSQL for complex relationship queries and tag performance optimization
- Proper database indexing for tag relationship queries and full-text search capabilities
- User authentication using Django's built-in auth system

**Deployment & Infrastructure:**
- PythonAnywhere hosting for initial deployment with standard Django deployment practices
- JSON export functionality for user data portability and GDPR compliance
- Standard Django security practices with environment-based configuration

**Performance Constraints:**
- Network graph must handle up to 500 tasks per user without performance degradation
- Database queries optimized for tag relationship filtering under 100ms response times
- JavaScript bundle size minimized to support PythonAnywhere hosting limitations
