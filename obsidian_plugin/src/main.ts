import { Plugin } from "obsidian";
import { captureCurrentNote } from "./capture";
import { processInbox } from "./process";
import {
	DEFAULT_SETTINGS,
	HiveAgiSettingTab,
	type HiveAgiSettings,
} from "./settings";

export default class HiveAgiPlugin extends Plugin {
	declare settings: HiveAgiSettings;

	async onload(): Promise<void> {
		await this.loadSettings();

		this.addCommand({
			id: "hiveagi-capture-current-note",
			name: "Capture current note → 00_Inbox/",
			callback: () => captureCurrentNote(this.app, this.settings),
		});

		this.addCommand({
			id: "hiveagi-process-inbox",
			name: "Process inbox (run LLM Wiki Engine)",
			callback: () => processInbox(this.app, this.settings),
		});

		this.addCommand({
			id: "hiveagi-open-settings",
			name: "Open Hive.AGI settings",
			callback: () => {
				// Obsidian opens setting via the app's internal API.
				// openTabById is not part of the public type; cast to access.
				const appInternal = this.app as unknown as {
					setting?: { open?: () => void; openTabById?: (id: string) => void };
				};
				appInternal.setting?.open?.();
				appInternal.setting?.openTabById?.("hiveagi");
			},
		});

		this.addSettingTab(new HiveAgiSettingTab(this.app, this));
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign(
			{},
			DEFAULT_SETTINGS,
			await this.loadData()
		);
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}
}
