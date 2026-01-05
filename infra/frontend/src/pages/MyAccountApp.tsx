import "@mantine/core/styles.css";
import { Stack, Title } from "@mantine/core";
import MyAppShell from "../components/MyAppShell";

/** Top-level React component for the login webpage. */
export default function MyAccountApp() {
	return (
		<MyAppShell>
			<MyAccountMain />
		</MyAppShell>
	);
}

function MyAccountMain() {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>My Account</Title>
		</Stack>
	);
}
