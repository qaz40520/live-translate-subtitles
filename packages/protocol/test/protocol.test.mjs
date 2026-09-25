import assert from "node:assert/strict";
import test from "node:test";

test("protocol source declares version one", async () => {
  const source = await import("node:fs/promises").then((fs) =>
    fs.readFile(new URL("../src/index.ts", import.meta.url), "utf8"),
  );
  assert.match(source, /PROTOCOL_VERSION = 1/);
});

