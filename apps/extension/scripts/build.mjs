import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const browser = process.argv[2] ?? "chrome";
if (!new Set(["chrome", "firefox"]).has(browser)) {
  throw new Error(`Unsupported TARGET_BROWSER: ${browser}`);
}

const extensionRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outdir = path.join(extensionRoot, "dist", browser);
await rm(outdir, { force: true, recursive: true });
await mkdir(outdir, { recursive: true });

await build({
  bundle: true,
  entryPoints: {
    background: path.join(extensionRoot, "src", "background.ts"),
    content: path.join(extensionRoot, "src", "content.ts"),
    popup: path.join(extensionRoot, "src", "popup.ts"),
  },
  format: "esm",
  outdir,
  platform: "browser",
  sourcemap: true,
  target: "es2022",
});

await cp(
  path.join(extensionRoot, "manifests", `${browser}.json`),
  path.join(outdir, "manifest.json"),
);
await cp(
  path.join(extensionRoot, "src", "popup.html"),
  path.join(outdir, "popup.html"),
);

console.log(`Built ${browser} extension in ${outdir}`);
