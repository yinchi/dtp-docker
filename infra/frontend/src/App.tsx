import "@mantine/core/styles.css";
import { Stack, Text, Title } from "@mantine/core";
import MyAppShell from "./MyAppShell";

function App() {
	return (
		<MyAppShell>
			<Main />
		</MyAppShell>
	);
}

function Main() {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>Hello, World!</Title>
			<Text>Placeholder page</Text>
			<Text>Second paragraph for testing default spacing in the Stack component</Text>
		</Stack>
	);
}

export default App;
