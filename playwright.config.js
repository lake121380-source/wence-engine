// @ts-check
const { defineConfig } = require('@playwright/test')

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    headless: false,          // 有头模式，可以看到浏览器操作
    slowMo: 500,              // 每步操作间隔 500ms，方便观察
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    locale: 'zh-CN',
  },
  projects: [
    {
      name: 'frontend',
      use: { baseURL: 'http://localhost:5173' },
      testMatch: /frontend\/.*/,
    },
    {
      name: 'admin',
      use: { baseURL: 'http://localhost:5174' },
      testMatch: /admin\/.*/,
    },
  ],
})
