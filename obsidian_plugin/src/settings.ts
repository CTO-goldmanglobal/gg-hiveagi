import { App, PluginSettingTab, Setting } from "obsidian";
import type HiveAgiPlugin from "./main";

export interface HiveAgiSettings {
	/** Python binary used to invoke `python -m llm_wiki_engine`. */
	pythonPath: string;
	/** Run engine in mock mode (no API keys needed). */
	mockMode: boolean;
	/** Vault-relative subdir for raw capture JSON. */
	inboxSubdir: string;
	/** Vault-relative subdir for processed entries. */
	entriesSubdir: string;
	/** Vault-relative subdir for quarantined items. */
	quarantineSubdir: string;
	/** Working directory of the repo root (where llm_wiki_engine lives). */
	repoRootPath: string;
}

export const DEFAULT_SETTINGS: HiveAgiSettings = {
	pythonPath: "python3",
	mockMode: true,
	inboxSubdir: "00_Inbox",
	entriesSubdir: "01_Entries",
	quarantineSubdir: "99_Archive/quarantine",
	repoRootPath: "",
};

export class HiveAgiSettingTab extends PluginSettingTab {
	plugin: HiveAgiPlugin;

	constructor(app: App, plugin: HiveAgiPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		containerEl.createEl("h3", { text: "Hive.AGI — LLM Wiki Engine bridge" });

		new Setting(containerEl)
			.setName("Repo root path")
			.setDesc(
				"Absolute path to the gg-hiveagi repo (where llm_wiki_engine/ lives). " +
					"Required for the Process command to find the Python module."
			)
			.addText((text) =>
				text
					.setPlaceholder("/Users/you/GG-HiveAGI")
					.setValue(this.plugin.settings.repoRootPath)
					.onChange(async (value) => {
						this.plugin.settings.repoRootPath = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Python binary")
			.setDesc("Path to the Python interpreter (default: python3).")
			.addText((text) =>
				text
					.setPlaceholder("python3")
					.setValue(this.plugin.settings.pythonPath)
					.onChange(async (value) => {
						this.plugin.settings.pythonPath = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Mock mode")
			.setDesc(
				"Run the engine in mock mode (no MiniMax/DeepSeek API keys needed). " +
					"Turn off once you have configured .env with real keys."
			)
			.addToggle((toggle) =>
				toggle
					.setValue(this.plugin.settings.mockMode)
					.onChange(async (value) => {
						this.plugin.settings.mockMode = value;
						await this.plugin.saveSettings();
					})
			);

		containerEl.createEl("h4", { text: "Vault subdirectories" });

		new Setting(containerEl)
			.setName("Inbox subdir")
			.addText((text) =>
				text
					.setValue(this.plugin.settings.inboxSubdir)
					.onChange(async (value) => {
						this.plugin.settings.inboxSubdir = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Entries subdir")
			.addText((text) =>
				text
					.setValue(this.plugin.settings.entriesSubdir)
					.onChange(async (value) => {
						this.plugin.settings.entriesSubdir = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Quarantine subdir")
			.addText((text) =>
				text
					.setValue(this.plugin.settings.quarantineSubdir)
					.onChange(async (value) => {
						this.plugin.settings.quarantineSubdir = value;
						await this.plugin.saveSettings();
					})
			);
	}
}
