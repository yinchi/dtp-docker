import { AppShell, Button, Group, MantineProvider, Text } from "@mantine/core";
import { type ReactNode, useEffect } from "react";
import { AuthProvider, useAuth } from "./AuthProvider";

/** Wraps our app in a MantineProvider and AuthProvider. */
function MyAppShell({ children }: { children: ReactNode }) {
	return (
		<MantineProvider>
			<AuthProvider>
				<MyAppShellInner>{children}</MyAppShellInner>
			</AuthProvider>
		</MantineProvider>
	);
}

/** A display wrapper using Mantine's AppShell with a predefined header and footer. */
function MyAppShellInner({ children }: { children: ReactNode }) {
	const headerHeight = "calc(1rem * var(--mantine-line-height-xl) + 2 * var(--mantine-spacing-md))";
	const footerHeight = "calc(1rem * var(--mantine-line-height-md) + 2 * var(--mantine-spacing-md))";
	const { user, loaded, logout } = useAuth();

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
					<Copyright year={2025} /> Anandarup Mukherjee & Yin-Chi Chan, Institute for Manufacturing,
					University of Cambridge
				</Text>
			</AppShell.Footer>
		</AppShell>
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
