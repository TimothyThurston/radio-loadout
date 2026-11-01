import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.RADIO_LOADOUT_E2E_PORT || 8137);
if (!Number.isInteger(port) || port < 1024 || port > 65535) {
    throw new Error("RADIO_LOADOUT_E2E_PORT must be an integer from 1024 to 65535.");
}
const venvPython = path.join(root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.PLAYWRIGHT_PYTHON || (existsSync(venvPython) ? venvPython : "python");
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
    testDir: "./tests/e2e",
    testMatch: "**/*.spec.mjs",
    fullyParallel: true,
    forbidOnly: Boolean(process.env.CI),
    retries: 0,
    workers: 2,
    timeout: 45_000,
    globalTimeout: 10 * 60_000,
    expect: { timeout: 7_000 },
    outputDir: "test-results",
    reporter: [["list"], ["html", { open: "never" }]],
    use: {
        baseURL,
        actionTimeout: 10_000,
        acceptDownloads: true,
        serviceWorkers: "block",
        trace: "retain-on-failure",
        screenshot: "only-on-failure",
        video: "off",
    },
    projects: [
        { name: "chromium-desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
        // A narrow Chromium viewport, not a claim about real phones or mobile Safari.
        { name: "chromium-narrow", use: { ...devices["Desktop Chrome"], viewport: { width: 375, height: 812 } } },
    ],
    webServer: {
        command: `"${python}" -m radio_loadout.web.serve`,
        cwd: root,
        env: {
            PYTHONPATH: path.join(root, "src"), PYTHONNOUSERSITE: "1",
            HOST: "127.0.0.1", PORT: String(port),
            RADIO_LOADOUT_ALLOWED_HOSTS: "localhost,127.0.0.1", RADIO_LOADOUT_FORWARDED_ALLOW_IPS: "",
        },
        url: `${baseURL}/builder`,
        reuseExistingServer: false,
        timeout: 30_000,
        stdout: "pipe",
        stderr: "pipe",
    },
});
