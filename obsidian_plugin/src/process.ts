import { App, Notice } from "obsidian";
import * as path from "path";
import type { HiveAgiSettings } from "./settings";

// Desktop Obsidian runs on Electron — Node's `require` is available.
// Cast through globalThis to satisfy the bundler / TS without `obsidian` types.
const nodeRequire = (globalThis as unknown as {
	require?: NodeRequire;
}).require ?? (window as unknown as { require?: NodeRequire }).require;

interface SpawnedChild {
	stdout: { on: (e: string, cb: (d: Buffer) => void) => void };
	stderr: { on: (e: string, cb: (d: Buffer) => void) => void };
	on: (e: string, cb: (code: number) => void) => void;
}

/**
 * Invoke the Python LLM Wiki Engine via shell.
 *
 * Spawns:
 *   <pythonPath> -m llm_wiki_engine process
 *       --inbox      <vault>/<inboxSubdir>
 *       --entries    <vault>/<entriesSubdir>
 *       --quarantine <vault>/<quarantineSubdir>
 *       [--mock]
 *
 * CWD = settings.repoRootPath (so `llm_wiki_engine` is importable).
 */
export async function processInbox(
	app: App,
	settings: HiveAgiSettings
): Promise<void> {
	if (!settings.repoRootPath) {
		new Notice("Hive.AGI: Set the repo root path in plugin settings first.");
		return;
	}
	if (!nodeRequire) {
		new Notice("Hive.AGI: Node require unavailable (desktop-only plugin).");
		return;
	}

	const vaultRoot = getVaultRoot(app);
	if (!vaultRoot) {
		new Notice("Hive.AGI: Cannot determine vault root path.");
		return;
	}

	const inbox = path.join(vaultRoot, settings.inboxSubdir);
	const entries = path.join(vaultRoot, settings.entriesSubdir);
	const quarantine = path.join(vaultRoot, settings.quarantineSubdir);

	const args = [
		"-m",
		"llm_wiki_engine",
		"process",
		"--inbox",
		inbox,
		"--entries",
		entries,
		"--quarantine",
		quarantine,
	];
	if (settings.mockMode) args.push("--mock");

	const fs = nodeRequire("fs") as typeof import("fs");
	const { spawn } = nodeRequire("child_process") as {
		spawn: (
			cmd: string,
			args: string[],
			opts: { cwd: string }
		) => SpawnedChild;
	};

	// Ensure output dirs exist.
	for (const dir of [entries, quarantine]) {
		if (!fs.existsSync(dir)) {
			fs.mkdirSync(dir, { recursive: true });
		}
	}

	new Notice("Hive.AGI: Processing inbox ...");

	const child = spawn(settings.pythonPath, args, {
		cwd: settings.repoRootPath,
	});

	let stdoutBuf = "";
	let stderrBuf = "";
	child.stdout.on("data", (d: Buffer) => {
		stdoutBuf += d.toString();
	});
	child.stderr.on("data", (d: Buffer) => {
		stderrBuf += d.toString();
	});

	child.on("exit", (code: number) => {
		if (code === 0) {
			new Notice("Hive.AGI: Inbox processed. See Entries folder.");
		} else {
			new Notice(`Hive.AGI: Process failed (exit ${code}). Check console.`);
			console.error(
				"[Hive.AGI] process exit",
				code,
				"\nstdout:",
				stdoutBuf,
				"\nstderr:",
				stderrBuf
			);
		}
	});
}

/** Best-effort vault FS root via the desktop adapter. */
function getVaultRoot(app: App): string | null {
	try {
		const adapter = (
			app.vault as unknown as {
				adapter?: { getBasePath?: () => string };
			}
		).adapter;
		if (adapter && typeof adapter.getBasePath === "function") {
			return adapter.getBasePath();
		}
	} catch {
		// fall through
	}
	return null;
}
