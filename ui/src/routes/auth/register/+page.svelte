<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth, isAxiosError } from '$lib/api';

	let username = $state('');
	let email = $state('');
	let firstName = $state('');
	let lastName = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleRegister() {
		if (!username || !email || !password) {
			error = 'Username, email and password are required.';
			return;
		}
		loading = true;
		error = '';
		try {
			await auth.register({
				username,
				email,
				password,
				first_name: firstName,
				last_name: lastName
			});
			await goto('/auth/login');
		} catch (err: unknown) {
			if (isAxiosError(err)) {
				if (!err.response) {
					error = 'Unable to reach the server.';
				} else {
					const data = err.response.data as Record<string, string[] | string>;
					const messages = Object.entries(data)
						.map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
						.join('\n');
					error = messages || 'Registration failed.';
				}
			} else {
				error = 'Registration failed.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-[70vh] items-center justify-center">
	<div class="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
		<h1 class="mb-6 text-center text-2xl font-bold text-gray-700">Create Account</h1>

		{#if error}
			<p class="mb-4 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); void handleRegister(); }}>
			<label class="mb-1 block text-sm font-medium text-gray-600" for="username">Username</label>
			<input
				id="username"
				type="text"
				bind:value={username}
				placeholder="choose a username"
				class="mb-4 w-full rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="email">Email</label>
			<input
				id="email"
				type="email"
				bind:value={email}
				placeholder="you@example.com"
				class="mb-4 w-full rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<div class="mb-4 grid grid-cols-2 gap-2">
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-600" for="firstName"
						>First name (optional)</label
					>
					<input
						id="firstName"
						type="text"
						bind:value={firstName}
						class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
					/>
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-600" for="lastName">Last name (optional)</label>
					<input
						id="lastName"
						type="text"
						bind:value={lastName}
						class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
					/>
				</div>
			</div>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="password">Password</label>
			<input
				id="password"
				type="password"
				bind:value={password}
				placeholder="••••••••"
				class="mb-6 w-full rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<button
				type="submit"
				disabled={loading}
				class="w-full rounded bg-brand-primary px-4 py-2 text-white hover:opacity-90 disabled:opacity-50"
			>
				{loading ? 'Creating account…' : 'Create Account'}
			</button>
		</form>

		<p class="mt-4 text-center text-sm text-gray-500">
			Already registered? <a href="/auth/login" class="text-blue-600 hover:underline">Sign in</a>
		</p>
	</div>
</div>
