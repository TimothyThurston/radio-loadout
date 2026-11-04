import { test, expect } from "@playwright/test";

test("production pages keep API docs disabled and load no external documentation assets", async ({ page, context, request, baseURL }) => {
    const externalRequests = [];
    const origin = new URL(baseURL).origin;
    await context.route("**/*", async (route) => {
        const url = new URL(route.request().url());
        if (url.origin !== origin) {
            externalRequests.push(url.href);
            await route.abort();
        } else {
            await route.continue();
        }
    });
    for (const path of ["/", "/builder"]) {
        const response = await page.goto(path);
        expect(response.status()).toBe(200);
        await expect(page.getByRole("link", { name: "View API", exact: true })).toHaveCount(0);
        await expect(page.locator('a[href="/docs"], a[href="/redoc"]')).toHaveCount(0);
        expect(await page.content()).not.toMatch(/cdn\.jsdelivr\.net|fonts\.googleapis\.com|fonts\.gstatic\.com|fastapi\.tiangolo\.com/);
    }
    await expect(page.getByRole("article")).toHaveCount(1);
    for (const path of ["/docs", "/redoc", "/docs/oauth2-redirect"]) {
        const response = await request.get(path);
        expect(response.status()).toBe(404);
        expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    }
    const schema = await request.get("/openapi.json");
    expect(schema.status()).toBe(200);
    expect((await schema.json()).paths["/downloads/chirp.csv"]).toBeDefined();
    expect(externalRequests).toEqual([]);
});
