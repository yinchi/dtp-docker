import "@mantine/core/styles.css";
import { Button, Group, Stack, Text, Title } from "@mantine/core";
import { type ReactNode, Suspense, use, useState } from "react";
import MyAppShell from "./MyAppShell";

/** Top-level React component for the login webpage. */
function App() {
	return (
		<MyAppShell>
			<Main />
		</MyAppShell>
	);
}

/**
 * Main content for the login webpage.
 *
 * Uses the following States:
 * - promise: a new Promise is created on each button click, forcing refresh of the
 *     ClickResultContainer
 * - nClicks: for demo purposes, the app alternates between successful and failure callbacks
 * - loading: used to disable the button when a callback is processing.
 */
function Main() {
	const [promise, setPromise] = useState<Promise<ReactNode> | null>(null);
	const [nClicks, setNClicks] = useState<number>(0);
	const [loading, setLoading] = useState(false);

	/** Calculate the result of clicking the Button. */
	async function getClickResult(nClicks: number): Promise<ReactNode> {
		// TODO: CODE TO HANDLE LOGIN GOES HERE

		// Artificial delay to simulate a fetch()
		await new Promise((resolve) => setTimeout(resolve, 500));

		// Return Text component based on value of nClicks
		if (nClicks % 2 === 0) {
			return (
				<Text fw={700} c={"red"}>
					{"An error occured!"}
				</Text>
			);
		} else {
			return <Text>{"Success!"}</Text>;
		}
	}

	/** Callback for whenever the Button is clicked. */
	function handleClick(): void {
		setNClicks(nClicks + 1);
		setPromise(
			new Promise<ReactNode>((resolve) => {
				setLoading(true);
				resolve(
					getClickResult(nClicks).then((value) => {
						setLoading(false);
						return value;
					}),
				);
			}),
		);
	}

	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>Login</Title>
			<Group>
				<Button onClick={handleClick} disabled={loading}>
					Click me!
				</Button>
			</Group>
			{promise && <ClickResultContainer promise={promise} />}
		</Stack>
	);
}

function ClickResultContainer({ promise }: { promise: Promise<ReactNode> }) {
	return (
		<Suspense fallback={<Text>⌛Logging in...</Text>}>
			<ClickResult promise={promise} />
		</Suspense>
	);
}

function ClickResult({ promise }: { promise: Promise<ReactNode> }) {
	return use(promise);
}

export default App;
