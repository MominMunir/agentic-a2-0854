import { defineConfig } from "@playwright/test";
import path from "node:path";
const root = path.resolve("../..");
process.env.PLAYWRIGHT_BROWSERS_PATH ||= path.join(root, ".cache/playwright");
const python =
  process.platform === "win32"
    ? path.join(root, ".venv/Scripts/python.exe")
    : path.join(root, ".venv/bin/python");
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "../../evaluation/playwright.json" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000`,
      cwd: root,
      url: "http://127.0.0.1:8000/api/health",
      timeout: 60000,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: "sqlite:///tmp/e2e.db",
        CHECKPOINT_URL: "sqlite:///tmp/e2e-checkpoints.db",
        MCP_TRANSPORT: "memory",
        INFERENCE_MODE: "smoke",
        EMBEDDING_BACKEND: "hash_smoke",
        EXECUTOR: "local",
        APP_URL: "http://127.0.0.1:5173",
      },
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      timeout: 60000,
      reuseExistingServer: false,
    },
  ],
});
