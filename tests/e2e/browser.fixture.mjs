import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

export const test = base.extend({
    testBrowser: async ({ browser, browserName, playwright, launchOptions, headless, channel }, use) => {
        if (browserName !== "firefox") {
            await use(browser);
            return;
        }

        // Context closure on its own leaves Firefox's idle sockets open between tests.
        const firefox = await playwright.firefox.launch({ ...launchOptions, headless, channel });
        try {
            await use(firefox);
        } finally {
            await firefox.close();
        }
    },
    context: async ({ browserName, context, testBrowser }, use) => {
        if (browserName !== "firefox") {
            await use(context);
            return;
        }

        // Use the runner's playwright instance so project context options and
        // the trace/screenshot hooks also apply to this context.
        const firefoxContext = await testBrowser.newContext();
        try {
            await use(firefoxContext);
        } finally {
            await firefoxContext.close();
        }
    },
});
