<script lang="ts">
	import { page } from '$app/stores';
	import * as m from '$lib/i18n/messages';
	import { isAuthenticated, uiConfig, exhibitEnabled } from '$lib/stores';

	function navClass(path: string, exact = false): string {
		const active = exact
			? $page.url.pathname === path
			: $page.url.pathname === path || $page.url.pathname.startsWith(path + '/');
		return `font-body text-sm tracking-wide hover:underline underline-offset-4${active ? ' underline font-semibold' : ''}`;
	}
</script>

<nav
	class="sticky top-0 z-50 border-b-2 border-gray-900"
	style="background-color: var(--brand-primary, #1e3a5f);"
>
	<div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
		<!-- Brand / Masthead -->
		<a href="/" class="flex items-center gap-2 text-white">
			{#if $uiConfig?.brand_logo_url}
				<img src={$uiConfig.brand_logo_url} alt="" class="h-8" />
			{/if}
			<h1 class="font-heading text-2xl font-black tracking-tight">
				{$uiConfig?.brand_name ?? 'Papad.alt'}
			</h1>
		</a>

		<!-- Navigation links -->
		<div class="flex flex-wrap items-center gap-4 text-white">
			<a href="/" class={navClass('/', true)}>{m.nav_home()}</a>
			<a href="/groups" class={navClass('/groups')}>{m.nav_collections()}</a>
			{#if $isAuthenticated}
				<a href="/annotations" class={navClass('/annotations')}>{m.nav_annotations()}</a>
			{/if}
			{#if $exhibitEnabled}
				<a href="/exhibits" class={navClass('/exhibits')}>{m.nav_exhibits()}</a>
			{/if}
			{#if $isAuthenticated}
				<a href="/settings" class={navClass('/settings', true)}>{m.nav_settings()}</a>
				<a href="/auth/logout" class={navClass('/auth/logout', true)}>{m.nav_logout()}</a>
			{:else}
				<a href="/auth/login" class={navClass('/auth/login', true)}>{m.nav_login()}</a>
			{/if}
		</div>
	</div>
</nav>
