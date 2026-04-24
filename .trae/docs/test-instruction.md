# Testing Instructions

## 1. Test Types
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test interactions between components
- **E2E Tests**: Test complete user flows
- **Performance Tests**: Test application performance

## 2. Running Tests
- **Unit Tests**: `npm test`
- **Integration Tests**: `npm run test:integration`
- **E2E Tests**: `npm run test:e2e`
- **Performance Tests**: `npm run test:performance`

## 3. Test Framework
- Use Jest for unit and integration tests
- Use Cypress for E2E tests
- Use Lighthouse for performance tests

## 4. Test Writing Guidelines
- Write tests for all new features
- Write tests for bug fixes
- Use descriptive test names
- Keep tests small and focused
- Use beforeEach/afterEach for setup/teardown

## 5. Test Coverage
- Aim for 80%+ test coverage
- Run coverage report: `npm run test:coverage`
- Review coverage report and add tests for uncovered code

## 6. CI/CD Integration
- Tests run automatically on PR creation
- All tests must pass before merging
- Coverage report is generated on each PR

## 7. Debugging Tests
- Use `npm test -- --watch` for interactive testing
- Use `npm test -- <test-file>` to run specific tests
- Use `console.log` in tests for debugging (remove before commit)