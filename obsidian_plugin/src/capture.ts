import { App, Notice, FuzzySuggestModal } from "obsidian";
import {
	DOMAINS,
	TRIGGER_TYPES,
	type Domain,
	type RawData,
	type TriggerType,
} from "./types";
import type { HiveAgiSettings } from "./settings";

/** Parse a note's body, stripping a leading YAML frontmatter block. */
function extractBodyAndFrontmatter(
	content: string
): { body: string; frontmatter: Record<string, string> } {
	const fmMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n?/);
	if (!fmMatch) {
		return { body: content, frontmatter: {} };
	}
	const fmText = fmMatch[1];
	const body = content.slice(fmMatch[0].length);
	const frontmatter: Record<string, string> = {};
	for (const line of fmText.split("\n")) {
		const idx = line.indexOf(":");
		if (idx === -1) continue;
		const key = line.slice(0, idx).trim();
		const value = line
			.slice(idx + 1)
			.trim()
			.replace(/^"(.*)"$/, "$1");
		if (key) frontmatter[key] = value;
	}
	return { body, frontmatter };
}

/** Pick a value from a list via a concrete suggester subclass. */
async function pickFromList<T extends string>(
	app: App,
	placeholder: string,
	items: T[]
): Promise<T> {
	return new Promise((resolve, reject) => {
		class PickerModal extends FuzzySuggestModal<T> {
			constructor(appInstance: App) {
				super(appInstance);
				this.setPlaceholder(placeholder);
			}
			getItems(): T[] {
				return items;
			}
			getItemText(item: T): string {
				return item;
			}
			onChooseItem(item: T): void {
				if (item) resolve(item);
				else reject(new Error("No item selected"));
			}
		}
		const modal = new PickerModal(app);
		modal.open();
	});
}

/**
 * Capture the active note into a RawData JSON and write it to 00_Inbox/.
 * Filename follows vault-structure-spec: YYYY-MM-DD_HHMM_<slug>.json
 */
export async function captureCurrentNote(
	app: App,
	settings: HiveAgiSettings
): Promise<void> {
	const file = app.workspace.getActiveFile();
	if (!file || file.extension !== "md") {
		new Notice("Hive.AGI: Open a Markdown note first.");
		return;
	}

	const content = await app.vault.read(file);
	const { body, frontmatter } = extractBodyAndFrontmatter(content);

	// Derive trigger_type / domain from frontmatter or prompt the user.
	let triggerType: TriggerType;
	const fmTrigger = frontmatter["trigger_type"] as TriggerType | undefined;
	if (fmTrigger && TRIGGER_TYPES.includes(fmTrigger)) {
		triggerType = fmTrigger;
	} else {
		try {
			triggerType = await pickFromList(
				app,
				"Select trigger type",
				TRIGGER_TYPES
			);
		} catch {
			new Notice("Hive.AGI: Capture cancelled.");
			return;
		}
	}

	let domain: Domain;
	const fmDomain = frontmatter["domain"] as Domain | undefined;
	if (fmDomain && DOMAINS.includes(fmDomain)) {
		domain = fmDomain;
	} else {
		try {
			domain = await pickFromList(app, "Select domain", DOMAINS);
		} catch {
			new Notice("Hive.AGI: Capture cancelled.");
			return;
		}
	}

	// Tags: from frontmatter (comma-split) or note's Obsidian tags.
	const rawTags = frontmatter["tags"];
	const tags: string[] = rawTags
		? rawTags
				.split(",")
				.map((t) => t.trim())
				.filter(Boolean)
		: app.metadataCache.getFileCache(file)?.tags?.map((t) => t.tag.replace(/^#/, "")) ??
		  [];

	// GPS: from frontmatter (nested or flat) or default 0,0 (user can edit later).
	const gps = {
		lat: Number(frontmatter["gps_lat"] ?? frontmatter["lat"] ?? 0),
		lng: Number(frontmatter["gps_lng"] ?? frontmatter["lng"] ?? 0),
	};

	const rawData: RawData = {
		timestamp: new Date().toISOString(),
		gps,
		trigger_type: triggerType,
		domain,
		human_description: body.trim() || `(captured from ${file.basename})`,
		human_label: frontmatter["human_label"] ?? "",
		tags,
	};

	// Build inbox path: <inboxSubdir>/YYYY-MM-DD_HHMM_<slug>.json
	const now = new Date();
	const pad = (n: number) => String(n).padStart(2, "0");
	const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(
		now.getDate()
	)}_${pad(now.getHours())}${pad(now.getMinutes())}`;
	const slug = file.basename.replace(/[^A-Za-z0-9]+/g, "_").slice(0, 40);
	const inboxPath = `${settings.inboxSubdir}/${stamp}_${slug}.json`;

	// Ensure inbox dir exists, then write.
	await ensureDir(app, settings.inboxSubdir);
	await app.vault.create(inboxPath, JSON.stringify(rawData, null, 2));

	new Notice(`Hive.AGI: Captured → ${inboxPath}`);
}

/** Create a folder if missing (Obsidian vault adapter has no mkdir, use adapter). */
async function ensureDir(app: App, subdir: string): Promise<void> {
	const existing = app.vault.getAbstractFileByPath(subdir);
	if (!existing) {
		await app.vault.createFolder(subdir).catch(() => {
			// ignore "already exists" race
		});
	}
}
