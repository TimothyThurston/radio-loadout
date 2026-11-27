import { expect, test } from "./builder.fixture.mjs";

export async function observeSettingsDisclosure(summary) {
    return summary.evaluateHandle((element) => {
        const details = element.parentElement;
        const events = [];
        const types = ["pointerdown", "mousedown", "pointerup", "mouseup", "click", "toggle"];
        const identify = (node) => node instanceof Element
            ? node.localName + (node.id ? `#${node.id}` : "")
            : null;
        const state = () => {
            const { x, y, width, height } = element.getBoundingClientRect();
            return {
                open: details.open,
                bounds: { x, y, width, height },
                viewport: { width: innerWidth, height: innerHeight },
                scrollY,
            };
        };
        const before = state();
        function record(event) {
            if (event.type === "toggle" && event.target !== details) return;
            const { clientX, clientY } = event;
            const position = event instanceof MouseEvent && (event.type !== "click" || event.detail > 0)
                ? { x: clientX, y: clientY, hit: identify(document.elementFromPoint(clientX, clientY)) }
                : null;
            if (events.length === 24) events.shift();
            events.push({
                event,
                observation: {
                    type: event.type,
                    target: identify(event.target),
                    position,
                    trusted: event.isTrusted,
                    ...state(),
                },
            });
        }
        for (const type of types) document.addEventListener(type, record, true);
        return {
            read: () => ({
                before,
                after: state(),
                events: events.map(({ event, observation }) => ({
                    ...observation,
                    defaultPrevented: event.defaultPrevented,
                })),
            }),
            stop: () => {
                for (const type of types) document.removeEventListener(type, record, true);
            },
        };
    });
}

export async function openSettingsPlan(page) {
    const details = page.locator("#builder-settings-details");
    const summary = details.locator("summary");
    const observation = await observeSettingsDisclosure(summary);
    try {
        await summary.click();
        await expect(details, "Clicking the settings plan summary opens the panel").toHaveJSProperty("open", true);
    } catch (error) {
        const data = await observation.evaluate((observer) => observer.read());
        await test.info().attach("settings-disclosure", {
            body: JSON.stringify(data, null, 2),
            contentType: "application/json",
        });
        throw error;
    } finally {
        await observation.evaluate((observer) => observer.stop());
        await observation.dispose();
    }
}
