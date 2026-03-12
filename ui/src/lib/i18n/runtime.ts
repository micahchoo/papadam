/**
 * Stub Paraglide runtime.
 * Will be replaced by actual Paraglide generation in Phase 5 (l10n).
 */

export const sourceLanguageTag = 'en';
export const availableLanguageTags = ['en'] as const;
export type AvailableLanguageTag = (typeof availableLanguageTags)[number];

export function languageTag(): AvailableLanguageTag {
	return 'en';
}

export function setLanguageTag(_tag: AvailableLanguageTag | (() => AvailableLanguageTag)): void {
	// no-op in stub
}

export function isAvailableLanguageTag(tag: unknown): tag is AvailableLanguageTag {
	return typeof tag === 'string' && (availableLanguageTags as readonly string[]).includes(tag);
}

export function onSetLanguageTag(_fn: (tag: AvailableLanguageTag) => void): void {
	// no-op in stub
}
