import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  test: {
    // node, not jsdom: everything tested here is contract-facing logic, and
    // jsdom's ESM loading breaks under this toolchain
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
});
