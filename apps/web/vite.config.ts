import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const contractsSource = new URL(
  "../../packages/typescript/curios-contracts/src/index.ts",
  import.meta.url,
).pathname;

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@curiosos/curios-contracts": contractsSource,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
