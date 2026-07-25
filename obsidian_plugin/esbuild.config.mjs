import esbuild from "esbuild";
import process from "process";

// Minimal built-in Node modules list (avoids extra dep on `builtin-modules`).
const builtins = [
	"assert", "buffer", "child_process", "cluster", "console", "constants",
	"crypto", "dgram", "dns", "domain", "events", "fs", "http", "http2",
	"https", "net", "os", "path", "punycode", "querystring", "readline",
	"repl", "stream", "string_decoder", "sys", "timers", "tls", "tty",
	"url", "util", "v8", "vm", "zlib",
];

const prod = process.argv[2] === "production";

const context = await esbuild.context({
	entryPoints: ["src/main.ts"],
	bundle: true,
	external: [
		"obsidian",
		"electron",
		"@codemirror/autocomplete",
		"@codemirror/collab",
		"@codemirror/commands",
		"@codemirror/language",
		"@codemirror/lint",
		"@codemirror/search",
		"@codemirror/state",
		"@codemirror/view",
		"@lezer/common",
		"@lezer/highlight",
		"@lezer/lr",
		...builtins,
	],
	format: "cjs",
	target: "es2022",
	logLevel: "info",
	sourcemap: prod ? false : "inline",
	treeShaking: true,
	outfile: "main.js",
	minify: prod,
});

if (prod) {
	await context.rebuild();
	process.exit(0);
} else {
	await context.watch();
}
