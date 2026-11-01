import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
function scripts(directory) {
    return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
        const filename = path.join(directory, entry.name);
        return entry.isDirectory() ? scripts(filename) : /\.(?:m?js)$/.test(entry.name) ? [filename] : [];
    });
}
const files = [path.join(root, "playwright.config.mjs"),
    ...["src/radio_loadout/web/static", "tests/js", "tests/e2e", "scripts"].flatMap((dir) => scripts(path.join(root, dir)))];
for (const filename of files) {
    const result = spawnSync(process.execPath, ["--check", filename], { stdio: "inherit" });
    if (result.error) throw result.error;
    if (result.status !== 0) process.exit(result.status || 1);
}
console.log(`JavaScript syntax checks passed: ${files.length} files`);
