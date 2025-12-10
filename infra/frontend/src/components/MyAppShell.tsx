import { AppShell, Button, Group, MantineProvider, Text } from "@mantine/core";
import { useCallback, useEffect, useState } from "react";
import { hostURL } from "../config";

/**
 * A display wrapper using Mantine's AppShell with a predefined header and footer.
 *
 * Also wraps the AppShell in a MantineProvider so that the full page can be rendered in
 * a single MyAppShell component.
 *
 */
function MyAppShell({ children }: { children: React.ReactNode }) {
	const headerHeight = "calc(1rem * var(--mantine-line-height-xl) + 2 * var(--mantine-spacing-md))";
	const footerHeight = "calc(1rem * var(--mantine-line-height-md) + 2 * var(--mantine-spacing-md))";

	/** JSON object structure for the `/auth/user/me` API endpoint. */
	interface User {
		user_id: string;
		user_name: string;
		roles: string[];
	}

	/** Get the username of the logged in user, or return null if not logged in. */
	const getUser = useCallback(async (): Promise<User | null> => {
		const bearerToken = sessionStorage.getItem("accessToken");
		return await fetch(`${hostURL}/auth/user/me`, {
			method: "GET",
			headers: {
				accept: "application/json",
				Authorization: `Bearer ${bearerToken}`,
			},
			mode: "cors",
		})
			.then(async (response) => {
				const content: User = await response.json();
				return response.status === 200 ? content : null;
			})
			.catch(() => {
				console.error("An error occured.");
				return null;
			});
	}, []);

	/** Logout if logged in. */
	function logout(): void {
		sessionStorage.removeItem("accessToken");
		window.location.href = "/login";
	}

	const [user, setUser] = useState<User | null>(null);
	const [loaded, setLoaded] = useState<boolean>(false);

	// Fetch the username, set `user` to the fetched value, and mark the page as loaded.
	useEffect(() => {
		getUser()
			.then((user) => setUser(user))
			.then(() => setLoaded(true));
	}, [getUser]);

	// Once the page is loaded, check if we need to redirect
	useEffect(() => {
		console.log(user, window.location.pathname);

		// If not logged in and not on login page, redirect to login page
		if (loaded && !user && !window.location.pathname.startsWith("/login")) {
			window.location.href = "/login";
		}

		// If logged in and on login page, redirect to homepage
		if (loaded && user && window.location.pathname.startsWith("/login")) {
			window.location.href = "/";
		}
	}, [user, loaded]);

	return (
		<MantineProvider>
			<AppShell padding={"md"} header={{ height: headerHeight }} footer={{ height: footerHeight }}>
				<AppShell.Header bg={"dark"}>
					<Group c={"white"} px={"md"} py={"sm"} justify="space-between">
						<Text size={"xl"} fw={900}>
							Digital Twin Platform Demo
						</Text>
						<Group>
							{user ? (
								<>
									<Text size="sm">👤 {user.user_name}</Text>
									<Button size="sm" onClick={logout}>
										Logout
									</Button>
								</>
							) : null}
						</Group>
					</Group>
				</AppShell.Header>
				<AppShell.Main px={"md"} py={"md"} mt={headerHeight} mb={footerHeight}>
					{loaded && (user || window.location.pathname.startsWith("/login")) ? children : null}
				</AppShell.Main>
				<AppShell.Footer bg={"dark"}>
					<Text size={"md"} c={"white"} px={"md"} py={"sm"}>
						<Copyright year={2025} /> Anandarup Mukherjee & Yin-Chi Chan, Institute for
						Manufacturing, University of Cambridge
					</Text>
				</AppShell.Footer>
			</AppShell>
		</MantineProvider>
	);
}

/** Copyright text for the footer.
 *
 * @param year The current year.
 */
function Copyright({ year }: { year: number }) {
	const currentYear = new Date().getFullYear();
	return currentYear === year ? (
		<>&copy; {year}</>
	) : (
		<>
			&copy; {year}&ndash;{currentYear}
		</>
	);
}

export default MyAppShell;
