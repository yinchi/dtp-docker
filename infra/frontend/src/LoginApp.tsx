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
 * Uses two States:
 * - promise: a new timeout Promise is created on each button click, forcing refresh of the
 *     MessageContainer
 * - nClicks: for demo purposes, the app alternates between successful and failure callbacks
 */
function Main() {
	const [promise, setPromise] = useState<Promise<void> | null>(null);
	const [nClicks, setNClicks] = useState<number>(0);
	const [message, setMessage] = useState<ReactNode>(null);

	/** Calculate the message contents. */
	async function getStatusMessage(nClicks: number): Promise<ReactNode> {
		// TODO: CODE TO HANDLE LOGIN GOES HERE

		// Artificial delay
		await new Promise((resolve) => setTimeout(resolve, 1000));

		// Return Text component based on value of nClicks
		if (nClicks % 2 === 0) {
			return (
				<Text fw={"bold"} c={"red"}>
					{"Fail!"}
				</Text>
			);
		} else {
			return <Text>{"Success!"}</Text>;
		}
	}

	/** Callback for whenever the Button is clicked. */
	async function handleClick(): Promise<void> {
		setNClicks(nClicks + 1);
		setPromise(
			new Promise<void>((resolve) => {
				getStatusMessage(nClicks).then((msg) => {
					// TODO: CODE TO HANDLE LOGIN RESULT GOES HERE
					setMessage(msg);

					// Mark Promise as resolved
					resolve();
				});
			}),
		);
	}

	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>Login</Title>
			<Group>
				<Button onClick={handleClick}>Click me!</Button>
			</Group>
			{promise && <MessageContainer message={message} promise={promise} />}
		</Stack>
	);
}

function MessageContainer({
	message,
	promise,
}: {
	messageError?: Error;
	message: ReactNode;
	promise: Promise<void>;
}) {
	return (
		// Reset the ErrorBoundary when a new Promise is passed, i.e. when the button is clicked.
		// This triggers generation of a new Message.
		<Suspense fallback={<p>⌛Downloading message...</p>}>
			<Message message={message} promise={promise} />
		</Suspense>
	);
}

function Message({ message, promise }: { message: ReactNode; promise: Promise<void> }) {
	use(promise);
	return message;
}

export default App;
