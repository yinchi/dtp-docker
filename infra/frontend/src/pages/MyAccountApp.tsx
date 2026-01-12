import "@mantine/core/styles.css";
import { Badge, Button, Group, PasswordInput, Stack, Table, Text, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { ModalsProvider, modals } from "@mantine/modals";
import { type ReactNode, useEffect, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import MyAppShell from "../components/MyAppShell";

/** Top-level React component for the login webpage. */
export default function MyAccountApp() {
	return (
		<MyAppShell>
			<ModalsProvider>
				<MyAccountMain />
			</ModalsProvider>
		</MyAppShell>
	);
}

function MyAccountMain() {
	const { user, loaded } = useAuth();
	const [userInfoTable, setUserInfoTable] = useState<ReactNode | null>(null);
	const [submitting, setSubmitting] = useState(false);

	const form = useForm({
		mode: "uncontrolled",
		initialValues: {
			oldPassword: "",
			newPassword: "",
			confirmNewPassword: "",
		},
		validate: {
			oldPassword: (value) => (value.length < 1 ? "Please enter your existing password" : null),
			newPassword: (value) => (value.length < 1 ? "Please enter a new password" : null),
			confirmNewPassword: (value, values) =>
				value !== values.newPassword ? "Passwords do not match" : null,
		},
	});

	/** Open a modal for okay password change status. */
	const okayModal = () =>
		modals.open({
			title: (
				<Text fw={900} size="lg">
					Success!
				</Text>
			),
			children: (
				<>
					<Text>Password updated.</Text>
					<Button
						fullWidth
						onClick={() => {
							modals.closeAll();
						}}
						mt="md"
					>
						OK
					</Button>
				</>
			),
		});

	/** Open a modal for error password change status.
	 * @param errMsg The error message to show.
	 */
	const errorModal = (errMsg: string) =>
		modals.open({
			title: (
				<Text fw={900} size="lg" c={"red"}>
					Error!
				</Text>
			),
			children: (
				<>
					<Text>{errMsg}</Text>
					<Button
						fullWidth
						onClick={() => {
							modals.closeAll();
						}}
						mt="md"
					>
						OK
					</Button>
				</>
			),
		});

	/** Handle submission of password change form. */
	async function changePassword() {
		setSubmitting(true);

		const { oldPassword, newPassword } = form.getValues();

		const fetchResult = await fetch("/auth/users/me", {
			method: "PATCH",
			credentials: "include",
			headers: {
				accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				current_password: oldPassword,
				new_password: newPassword,
			}),
		})
			.then(async (response) => {
				const content = await response.json();
				response.ok ? okayModal() : errorModal(content.detail);
				return { status: response.status, content: content };
			})
			.catch((error) => {
				console.error(error);
				errorModal(`${error}`);
				return null;
			});
		console.log(fetchResult?.status, fetchResult?.content);

		setSubmitting(false);
	}

	useEffect(() => {
		if (loaded && user) {
			setUserInfoTable(
				<Group>
					<Table w={"auto"} variant="vertical" withTableBorder>
						<Table.Tr>
							<Table.Th fw={900}>User name:</Table.Th>
							<Table.Td>{user.user_name}</Table.Td>
						</Table.Tr>
						<Table.Tr>
							<Table.Th fw={900}>User ID:</Table.Th>
							<Table.Td>{user.user_id}</Table.Td>
						</Table.Tr>
						<Table.Tr>
							<Table.Th fw={900}>User roles:</Table.Th>
							<Table.Td>
								{user.roles.length > 0 ? (
									user.roles.map((role) => (
										<Badge key={`roleBadge-${role}`} color="cyan">
											{role}
										</Badge>
									))
								) : (
									<>(None)</>
								)}
							</Table.Td>
						</Table.Tr>
					</Table>
				</Group>,
			);
		}
	}, [loaded, user]);

	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={1}>My Account</Title>
			{userInfoTable}
			<form onSubmit={form.onSubmit(changePassword)}>
				<Stack m={0} p={0} gap={"md"}>
					<Title order={2}>Change password</Title>
					<PasswordInput
						size="md"
						w={400}
						label="Existing password"
						key={form.key("oldPassword")}
						{...form.getInputProps("oldPassword")}
					/>
					<PasswordInput
						size="md"
						w={400}
						label="New password"
						key={form.key("newPassword")}
						{...form.getInputProps("newPassword")}
					/>
					<PasswordInput
						size="md"
						w={400}
						label="Repeat new password"
						key={form.key("confirmNewPassword")}
						{...form.getInputProps("confirmNewPassword")}
					/>
					<Group>
						<Button size="md" type="submit" disabled={submitting}>
							Change password
						</Button>
					</Group>
				</Stack>
			</form>
		</Stack>
	);
}
