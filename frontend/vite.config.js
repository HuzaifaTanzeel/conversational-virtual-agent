import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      // Same-origin proxy for the Gecko pano CDN. The CDN serves tiles without
      // an Access-Control-Allow-Origin header, so the browser blocks them as
      // WebGL textures (krpano loads them crossorigin) -> black tour. Proxying
      // makes the tiles first-party so no CORS check applies.
      "/resort-cdn": {
        target: "https://vt-cdn.geckodigital.app",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/resort-cdn/, ""),
      },
    },
  },
});
