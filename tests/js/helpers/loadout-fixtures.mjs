import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";

export const fixture = (name) => JSON.parse(readFileSync(new URL(`../../fixtures/loadouts/${name}`, import.meta.url), "utf8"));
export const catalog = () => fixture("catalog-v1.json");
export function validator() {
    const context = createContext({ structuredClone });
    for (const name of ["backup-format.js", "settings-plan.js", "loadout-format.js"]) {
        runInContext(readFileSync(new URL(`../../../src/radio_loadout/web/static/${name}`, import.meta.url), "utf8"), context);
    }
    return context.RadioLoadoutDocument.createValidator([catalog()], { channels: 2000 });
}
