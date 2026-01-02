import "@mantine/core/styles.css";
import { Badge, Group, Stack, Text, Title } from "@mantine/core";
import { type ReactNode, useEffect, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import MyAppShell from "../components/MyAppShell";
import { hostURL } from "../config";

/** Top-level React component for the main webpage. */
function MainApp() {
	return (
		<MyAppShell>
			<Main />
		</MyAppShell>
	);
}

/** Main content for the main webpage. */
function Main() {
	const { user, loaded, authFetch } = useAuth();
	const [roles, setRoles] = useState<ReactNode | null>(null);
	const [whoami, setWhoami] = useState<ReactNode | null>(null);

	const whoamiHeader = (
		<Title order={3}>Whoami Result (for testing Traefik ForwardAuth middleware)</Title>
	);

	useEffect(() => {
		if (loaded && user) {
			authFetch(`${hostURL}/whoami`, {
				headers: { accept: "text/plain" },
			})
				.then(async (res) => {
					if (!res.ok) {
						setWhoami(
							<pre style={{ color: "red" }}>'whoami' fetch failed, not authenticated?</pre>,
						);
					}
					setWhoami(
						<Stack m={0} p={0} gap={0}>
							{whoamiHeader}
							<pre>{await res.text()}</pre>
						</Stack>,
					);
					setRoles(
						user.roles.map((role) => (
							<Badge key={`roleBadge-${role}`} color="lime">
								{role}
							</Badge>
						)),
					);
				})
				.catch(() =>
					setWhoami(
						<Stack m={0} p={0} gap={0}>
							{whoamiHeader}
							<pre style={{ color: "red" }}>'whoami' fetch failed.</pre>
						</Stack>,
					),
				);
		}
	}, [authFetch, loaded, user]);

	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>Hello{loaded && user ? `, ${user.user_name}` : ""}!</Title>
			<Group gap={"xs"}>
				<Text>Your roles:</Text>
				{roles}
			</Group>
			{whoami}
		</Stack>
	);
}

export default MainApp;
