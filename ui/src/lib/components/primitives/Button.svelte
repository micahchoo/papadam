<!--
  Button primitive — typed wrapper over <button>.

  Architecture boundary: primitives are leaves — no imports from api, stores,
  or components. bits-ui 0.21 uses Melt UI (Svelte 4); upgrade to bits-ui 2.x
  when a Svelte 5-native release is available.

  Usage:
    <Button variant="primary" onclick={handler}>Label</Button>
    <Button variant="danger" disabled={loading}>Delete</Button>
-->
<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

	interface Props {
		variant?: Variant;
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
	}

	const {
		variant = 'primary',
		disabled = false,
		type = 'button',
		onclick,
		children
	}: Props = $props();

	const classes: Record<Variant, string> = {
		primary: 'bg-blue-950 text-white hover:bg-blue-700',
		secondary: 'bg-gray-200 text-gray-700 hover:bg-gray-300',
		danger: 'bg-red-500 text-white hover:bg-red-600',
		ghost: 'bg-transparent text-blue-600 hover:underline'
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class="rounded px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 {classes[
		variant
	]}"
>
	{@render children()}
</button>
