import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

export const test = base.extend({
    testBrowser: async ({ browser, browserName, playwright, launchOptions, headless, channel }, use) => {
        if (browserName === "chromium") {
            await use(browser);
            return;
        }

        // Firefox and WebKit retain idle sockets after context closure.
        const disposable = await playwright[browserName].launch({ ...launchOptions, headless, channel });
        try {
            await use(disposable);
        } finally {
            await disposable.close();
        }
    },
    context: async ({ browserName, context, testBrowser }, use) => {
        if (browserName === "chromium") {
            await use(context);
            return;
        }

        // Use the runner's playwright instance so project context options and
        // the trace/screenshot hooks also apply to this context.
        const isolatedContext = await testBrowser.newContext();
        try {
            await use(isolatedContext);
        } finally {
            await isolatedContext.close();
        }
    },
});
