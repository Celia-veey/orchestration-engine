# Development Instructions

## 1. Environment Setup
- Install Node.js 18.x
- Install npm 9.x
- Clone repository: `git clone https://github.com/Celia-veey/orchestration-engine.git`
- Install dependencies: `npm install`

## 2. Development Workflow
1. Create a new branch: `git checkout -b <type>/<context_id>`
2. Make changes to code
3. Run tests: `npm test`
4. Run lint: `npm run lint`
5. Commit changes: `git commit -m "<type>(<scope>): <description>"`
6. Push changes: `git push origin <branch>`
7. Create PR: Follow PR guidelines in agent-pr-guidelines.md

## 3. Code Standards
- Use TypeScript for all code
- Follow ESLint rules
- Write unit tests for all new features
- Use meaningful variable and function names
- Keep functions small and focused

## 4. Debugging
- Use Chrome DevTools for frontend debugging
- Use VS Code debugger for backend debugging
- Add console logs for debugging (remove before commit)

## 5. Deployment
- Run build: `npm run build`
- Deploy to staging: `npm run deploy:staging`
- Deploy to production: `npm run deploy`