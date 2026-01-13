import "@mantine/core/styles.css";
import { Anchor, Group, Stack, Table, Text, Title } from "@mantine/core";
import { type ReactNode, useEffect, useState } from "react";
import type { User } from "../../components/AuthProvider";
import MyAppShell from "../../components/MyAppShell";
import { userBadges } from "../../util";

/** Top-level React component for the user admin webpage. */
export default function AdminUpdateUserApp(): ReactNode {
	const userId = new URLSearchParams(window.location.search).get("id") ?? "";

	return (
		<MyAppShell>
			<Stack m={0} p={0} gap={"md"}>
				<Text>
					<Anchor href="/">🏠 Home</Anchor>&nbsp;/&nbsp;
					<Anchor href="/user_admin">User administration</Anchor>&nbsp;/
				</Text>
				<UpdateUserMain user_id={userId} />
			</Stack>
		</MyAppShell>
	);
}

function UpdateUserMain({ user_id }: { user_id: string }): ReactNode {
	const [user, setUser] = useState<User | null>(null);
	const [isLoading, setIsLoading] = useState(false);

	useEffect(() => {
		if (!user_id) {
			setUser(null);
			setIsLoading(false);
			return;
		}

		setIsLoading(true);

		fetch(`/auth/users/${user_id}`, {
			method: "GET",
			credentials: "include",
			headers: {
				accept: "application/json",
			},
		})
			.then(async (response) => {
				if (!response.ok) return null;
				const fetchedUser: User = await response.json();
				return fetchedUser;
			})
			.then((fetchedUser) => {
				setUser(fetchedUser);
			})
			.catch((err: unknown) => {
				console.error(err);
				setUser(null);
			})
			.finally(() => {
				setIsLoading(false);
			});
	}, [user_id]);

	if (!user_id) {
		return <Text c={"red"}>No user specified.</Text>;
	}
	if (isLoading) {
		return <Text>Loading user…</Text>;
	}
	if (!user) {
		return <Text c={"red"}>Could not find the specified user.</Text>;
	}

	return (
		<>
			<Title order={1}>Update user {user.user_id}</Title>
			<Text fw={700}>Current user info:</Text>
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
						<Table.Td>{userBadges(user)}</Table.Td>
					</Table.Tr>
				</Table>
			</Group>
			<UpdateUserNameComponent user={user} />
			<UpdatePasswordComponent user={user} />
			<UpdateRolesComponent user={user} />
		</>
	);
}

// const userNameForm = useForm({
//   mode: "uncontrolled",
//   initialValues: {
//     userName: ""
//   },
//   validate: {
//     userName: (value) => (value.length < 1 ? "Please enter a username" : null)
//   }
// });

// const passwordForm = useForm({
//   mode: "uncontrolled",
//   initialValues: {
//     newPassword: "",
//     confirmNewPassword: "",
//   },
//   validate: {
//     newPassword: (value) => (value.length < 1 ? "Please enter a password" : null),
//     confirmNewPassword: (value, values) =>
//       value !== values.newPassword ? "Passwords do not match" : null,
//   },
// });

function UpdateUserNameComponent({ user }: { user: User }): ReactNode {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={2}> Change username</Title>
			{/* TODO: form to submit new username */}
			<Text>{user.user_name}</Text>
			<Text>TODO</Text>
		</Stack>
	);
}

function UpdatePasswordComponent({ user }: { user: User }): ReactNode {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={2}> Change password</Title>
			{/* TODO: form to submit new password (with confirmation password input) */}
			<Text>{user.user_name}</Text>
			<Text>TODO</Text>
		</Stack>
	);
}

function UpdateRolesComponent({ user }: { user: User }): ReactNode {
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Title order={2}> Edit roles</Title>
			{/* TODO: form to change roles */}
			<Text>{user.user_name}</Text>
			<Text>TODO</Text>
		</Stack>
	);
}
