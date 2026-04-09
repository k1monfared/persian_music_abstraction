import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: resolve(__dirname),
  publicDir: resolve(__dirname, "../build/data"),
  server: {
    open: true,
  },
  build: {
    outDir: resolve(__dirname, "../build/web"),
    emptyOutDir: true,
  },
});
