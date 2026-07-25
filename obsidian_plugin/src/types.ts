/**
 * RawData — TypeScript mirror of P1's pydantic RawData model.
 *
 * The JSON written by the Capture command MUST satisfy this shape,
 * so that P1's `llm_wiki_engine` can parse it (RawData(**data)).
 *
 * Keep in sync with:
 *   - llm_wiki_engine/models.py (RawData)
 *   - specs/seed-package-schema-v1.md (trigger_type / domain enums)
 */

export type TriggerType =
	| "aesthetic_gaze"
	| "anomaly_detection"
	| "professional_judgment"
	| "manual"
	| "other";

export type Domain =
	| "tourism"
	| "legal"
	| "medical"
	| "industrial"
	| "education"
	| "other";

export interface Gps {
	lat: number;
	lng: number;
}

export interface RawData {
	/** ISO 8601 timestamp, e.g. "2026-07-25T19:30:00Z" */
	timestamp: string;
	/** Nested GPS — matches P1 contract (NOT flat gps_lat/gps_lng) */
	gps: Gps;
	trigger_type: TriggerType;
	domain: Domain;
	human_description: string;
	human_label?: string;
	tags: string[];
	hardware?: string;
	trigger_duration?: number;
}

/** Enum value lists for UI suggesters. */
export const TRIGGER_TYPES: TriggerType[] = [
	"aesthetic_gaze",
	"anomaly_detection",
	"professional_judgment",
	"manual",
	"other",
];

export const DOMAINS: Domain[] = [
	"tourism",
	"legal",
	"medical",
	"industrial",
	"education",
	"other",
];
