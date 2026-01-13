import "@mantine/core/styles.css";
import { Anchor, Button, Card, Group, Stack, Text, Title } from "@mantine/core";
import { type ReactNode, useEffect, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import MyAppShell from "../components/MyAppShell";
import { commonString, userBadges } from "../util";

/** Top-level React component for the main webpage. */
function MainApp(): ReactNode {
	return (
		<MyAppShell>
			<Main />
		</MyAppShell>
	);
}

/** Main content for the main webpage. */
function Main(): ReactNode {
	const { user, loaded } = useAuth();
	const [roleBadges, setRoleBadges] = useState<ReactNode | null>(null);
	const [whoami, setWhoami] = useState<ReactNode | null>(null);

	const whoamiHeader = (
		<Title order={3}>Whoami Result (for testing Traefik ForwardAuth middleware)</Title>
	);

	useEffect(() => {
		if (loaded && user) {
			fetch(`/whoami`, {
				headers: { accept: "text/plain" },
				credentials: "include",
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
					setRoleBadges(userBadges(user));
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
	}, [loaded, user]);

	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>Hello{loaded && user ? `, ${user.user_name}` : ""}!</Title>
			<Group gap={"xs"}>
				<Text>Your roles:</Text>
				{roleBadges}
			</Group>
			<Group gap={"sm"} align="stretch">
				<ButtonCard href="/me" color="cyan" title="My Account">
					<Text>
						Change username/
						<wbr />
						password
					</Text>
				</ButtonCard>
				{commonString(user?.roles, ["admin", "users:admin"]) ? (
					<ButtonCard href="/user_admin" color="cyan" title="User administration">
						<Text>
							Add/
							<wbr />
							remove/
							<wbr />
							modify users
						</Text>
					</ButtonCard>
				) : null}
			</Group>
			{whoami}
		</Stack>
	);
}

function ButtonCard({
	href,
	color,
	title,
	children,
}: {
	href: string;
	color: string;
	title: string;
	children?: ReactNode;
}): ReactNode {
	return (
		<Anchor href={href} m={0} p={0} display="block" h="100%" style={{ alignSelf: "stretch" }}>
			<Button
				color={color}
				h="100%"
				m={0}
				p={0}
				styles={{
					root: { height: "100%", width: "100%" },
					inner: { height: "100%", alignItems: "flex-start" },
				}}
			>
				<Card shadow="sm" bg={"transparent"} c={"white"} w={300} h="100%">
					<Text size={"xl"} fw={900} style={{ textWrap: "wrap" }}>
						{title}
					</Text>
					{children}
				</Card>
			</Button>
		</Anchor>
	);
}

export default MainApp;
