import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  testDir: './tests',
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', {outputFile: 'results.json'}]],
  use: {baseURL: 'http://127.0.0.1:5050', browserName: 'chromium'},
  webServer: {
    command: 'python3 app.py --source synthetic --port 5050',
    cwd: fileURLToPath(new URL('..', import.meta.url)),
    url: 'http://127.0.0.1:5050/api/status',
    reuseExistingServer: false,
    timeout: 30000,
  },
});
