import "@mantine/core/styles.css";
import { Stack, Title } from "@mantine/core";
import MyAppShell from "../components/MyAppShell";

/** Top-level React component for the login webpage. */
export default function UserAdminApp() {
	return (
		<MyAppShell>
			<UserAdminMain />
		</MyAppShell>
	);
}

function UserAdminMain() {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>User Administration</Title>
		</Stack>
	);
}
