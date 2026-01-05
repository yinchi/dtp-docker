import path from "node:path";
import react from "@vitejs/plugin-react";
import { globSync } from "glob";
import { defineConfig } from "vite";

export default defineConfig({
	root: path.resolve(__dirname, "src/pages"),
	plugins: [react()],
	build: {
		outDir: path.resolve(__dirname, "dist"),
		emptyOutDir: true,
		rollupOptions: {
			input: globSync(path.resolve(__dirname, "src/pages", "*.html")),
		},
	},
});
