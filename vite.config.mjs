import { defineConfig } from "vite";
import path from "path";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default defineConfig({
    plugins: [
        viteStaticCopy({
            targets: [
                {
                    src: path.resolve(__dirname, "static/assets/scss/soft-ui-dashboard.scss"),
                    dest: "../css"
                }
            ]
        })
    ],
    css: {
        preprocessorOptions: {
            scss: {} // Remove additionalData to prevent double import
        }
    },
    build: {
        outDir: "static/assets/css",
        emptyOutDir: false,
        rollupOptions: {
            input: path.resolve(__dirname, "static/assets/scss/soft-ui-dashboard.scss"),
            output: {
                assetFileNames: "soft-ui-dashboard.css"
            }
        }
    }
});
