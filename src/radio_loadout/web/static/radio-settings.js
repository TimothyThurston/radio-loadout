/* Guidance-only UI. This intentionally has no channel, backup or localStorage integration. */
(() => {
    "use strict";
    const error = document.querySelector("#settings-error");
    const status = document.querySelector("#settings-status");
    const panel = document.querySelector("#settings-preview");
    const diff = document.querySelector("#settings-diff");
    const applyButton = document.querySelector("#apply-settings");
    const previewButton = document.querySelector("#preview-settings");
    const clearButton = document.querySelector("#clear-settings");
    const controls = [...document.querySelectorAll("[data-current], [data-proposed], [data-include]")];
    function showError(cause) {
        error.textContent = cause instanceof Error ? cause.message : "Could not update the settings plan.";
        error.hidden = false;
    }
    try {
        const catalog = JSON.parse(document.querySelector("#settings-catalog").textContent);
        const planner = RadioSettingsPlan.createPlanner(catalog);
        let plan = planner.empty();
        let review = null;
        const cards = [...document.querySelectorAll("[data-setting]")];
        const ids = new Set(cards.map((card) => card.dataset.setting));
        if (cards.length !== catalog.settings.length || ids.size !== cards.length
            || catalog.settings.some((setting) => !ids.has(setting.setting_id))) {
            throw new Error("Settings page/catalog mismatch. Editing is disabled.");
        }
        function invalidate() {
            review = null;
            panel.hidden = true;
            applyButton.disabled = true;
            diff.replaceChildren();
            error.hidden = true;
        }
        function renderPlan() {
            for (const card of cards) {
                const entry = plan.entries[card.dataset.setting];
                card.querySelector("[data-current]").value = entry ? JSON.stringify(entry.value) : "";
                card.querySelector("[data-origin]").textContent = `Plan origin: ${entry?.origin || "unset (not a manufacturer default)"}.`;
            }
        }
        function safe(action) {
            return () => {
                try { action(); } catch (cause) { invalidate(); renderPlan(); showError(cause); }
            };
        }
        for (const card of cards) {
            const current = card.querySelector("[data-current]");
            current.addEventListener("change", safe(() => {
                const next = planner.setCustom(plan, card.dataset.setting, current.value === "" ? undefined : JSON.parse(current.value));
                invalidate();
                plan = next;
                renderPlan();
                status.textContent = "Updated your session plan only. Preview again before adding suggestions. No radio was changed.";
            }));
            for (const control of card.querySelectorAll("[data-proposed], [data-include]")) {
                control.addEventListener("change", () => {
                    invalidate();
                    status.textContent = "Proposals changed. Preview again; your existing plan is unchanged.";
                });
            }
        }
        previewButton.addEventListener("click", safe(() => {
            invalidate();
            review = planner.preview(plan, cards.filter((card) => card.querySelector("[data-include]").checked)
                .map((card) => ({ id: card.dataset.setting, value: JSON.parse(card.querySelector("[data-proposed]").value) })));
            for (const change of review.changes) {
                const item = document.createElement("li");
                const setting = catalog.settings.find((entry) => entry.setting_id === change.id);
                item.textContent = `${setting.label}: ${planner.label(change.id, change.before?.value)} `
                    + `[${change.before?.origin || "unset"}] → ${planner.label(change.id, change.after.value)} [${change.after.origin}].`;
                diff.appendChild(item);
            }
            panel.hidden = false;
            applyButton.disabled = review.changes.length === 0;
            status.textContent = review.changes.length ? `Previewing ${review.changes.length} plan changes. Nothing applied yet.` : "No selected changes to add.";
        }));
        applyButton.addEventListener("click", safe(() => {
            const next = planner.apply(plan, review);
            const count = review.changes.length;
            invalidate();
            plan = next;
            renderPlan();
            status.textContent = `Added ${count} reviewed changes to this page's session plan. No radio, channels or backups were changed.`;
        }));
        document.querySelector("#cancel-settings").addEventListener("click", () => {
            invalidate();
            status.textContent = "Preview cancelled. Your session plan is unchanged.";
        });
        clearButton.addEventListener("click", () => {
            invalidate();
            plan = planner.empty();
            renderPlan();
            status.textContent = "Settings plan cleared. No factory reset or radio change occurred.";
        });
        controls.forEach((control) => { control.disabled = false; });
        previewButton.disabled = false;
        clearButton.disabled = false;
        // An ordinary paragraph also survives blocked/missing scripts and browser
        // automation that disables execution without changing noscript parsing.
        document.querySelector("#settings-js-required").hidden = true;
    } catch (cause) {
        controls.forEach((control) => { control.disabled = true; });
        previewButton.disabled = true;
        clearButton.disabled = true;
        applyButton.disabled = true;
        showError(cause);
    }
})();
