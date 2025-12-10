import "@mantine/core/styles.css";
import { Button, Group, PasswordInput, Stack, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useState } from "react";
import MyAppShell from "../components/MyAppShell";
import { hostURL } from "../config";

/** Top-level React component for the login webpage. */
function LoginApp() {
	return (
		<MyAppShell>
			<LoginMain />
		</MyAppShell>
	);
}

/** Main content for the login webpage. */
function LoginMain() {
	// Used to disable the button when a callback is processing
	const [loading, setLoading] = useState(false);

	const form = useForm({
		mode: "uncontrolled",
		initialValues: {
			userName: "",
			password: "",
		},
		validate: {
			userName: (value) => (value.length < 1 ? "Please enter a username" : null),
			password: (value) => (value.length < 1 ? "Please enter a password" : null),
		},
	});

	/** Perform the login function. */
	async function doLogin(): Promise<void> {
		setLoading(true);

		const { userName, password: rawPassword } = form.getValues();

		const fetchResult = await fetch(`${hostURL}/auth/token`, {
			method: "POST",
			headers: {
				accept: "application/json",
				"Content-Type": "application/x-www-form-urlencoded",
			},
			body: `grant_type=password&username=${userName}&password=${rawPassword}`,
		})
			.then(async (response) => {
				const content = await response.json();
				return { status: response.status, content: content };
			})
			.catch((error) => {
				console.error(error);
				form.setErrors({ password: `${error}` });
				return null;
			});

		console.log(fetchResult?.status, fetchResult?.content);

		if (fetchResult?.status === 200) {
			// Successful login
			const accessToken = fetchResult?.content?.access_token;
			if (typeof accessToken === "string" && accessToken.trim().length > 0) {
				sessionStorage.setItem("accessToken", accessToken);
				window.location.href = `/`;
			} else {
				form.setErrors({ password: "An unknown error occured." });
				return;
			}
		} else {
			form.setErrors({ password: fetchResult?.content?.detail ?? "An unknown error occured." });
		}

		setLoading(false);
	}

	return (
		<form onSubmit={form.onSubmit(doLogin)}>
			<Stack m={0} p={0} gap={"md"}>
				<Title order={1}>Login</Title>
				<TextInput
					size="md"
					w={400}
					label="Username"
					key={form.key("userName")}
					{...form.getInputProps("userName")}
				/>
				<PasswordInput
					size="md"
					w={400}
					label="Password"
					key={form.key("password")}
					{...form.getInputProps("password")}
				/>
				<Group>
					<Button size="md" type="submit" disabled={loading}>
						Login
					</Button>
				</Group>
			</Stack>
		</form>
	);
}

export default LoginApp;
