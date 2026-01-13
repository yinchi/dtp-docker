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
			input: Object.fromEntries(
				globSync(path.resolve(__dirname, "src/pages", "**/*.html")).map((absPath) => {
					const relFromPagesRoot = path
						.relative(path.resolve(__dirname, "src/pages"), absPath)
						.replaceAll(path.sep, "/");
					const key = relFromPagesRoot.replace(/\.html$/i, "");
					return [key, absPath];
				}),
			),
		},
	},
});
