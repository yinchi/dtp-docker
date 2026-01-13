import "@mantine/core/styles.css";
import { Anchor, Button, Group, Stack, Table, Text, Title } from "@mantine/core";
import { type ReactNode, useCallback, useEffect, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import MyAppShell from "../components/MyAppShell";
import { commonString, userBadges } from "../util";

/** Top-level React component for the user admin webpage. */
export default function UserAdminApp(): ReactNode {
	return (
		<MyAppShell>
			<UserAdminMain />
		</MyAppShell>
	);
}

/** Main content for the user admin webpage */
function UserAdminMain(): ReactNode {
	const { user, loaded } = useAuth();
	if (!loaded) return null;
	if (!user || !commonString(user.roles, ["admin", "users:admin"])) {
		return (
			<Stack m={0} p={0} gap={"md"}>
				<Title order={1}>Not authorized</Title>
				<Text>You are not authorized to view this page.</Text>
				<Anchor onClick={() => history.back()}>Go Back</Anchor>
			</Stack>
		);
	}
	return (
		<Stack m={0} p={0} gap={"md"}>
			<Text>
				<Anchor href="/">🏠 Home</Anchor>&nbsp;/
			</Text>
			<Title order={1}>User Administration</Title>
			<Title order={2}>Users</Title>
			<UsersTable />
			{/* TODO: Modal dialog for adding a new user */}
			<Group>
				<Button>Add User...</Button>
			</Group>
			<Title order={2}>Roles</Title>
			{/* TODO: Component for displaying roles, adding/deleting roles */}
			<Text>TODO: rolesAdminComponent</Text>
		</Stack>
	);
}

/** Users table with controls to update user information.
 *
 * Prototype version: displays all users
 * TODO: pagination (both frontend and DB), sorting, etc.
 */
function UsersTable() {
	interface User {
		user_id: string;
		user_name: string;
		roles: string[];
	}

	const userTableRow = useCallback((user: User) => {
		return (
			<Table.Tr>
				<Table.Td>{user.user_id}</Table.Td>
				<Table.Td>{user.user_name}</Table.Td>
				<Table.Td>{userBadges(user)}</Table.Td>
				<Table.Td>
					<Button component="a" href={`/user_admin/update_user?id=${user.user_id}`}>
						Update info...
					</Button>
				</Table.Td>
			</Table.Tr>
		);
	}, []);

	const userTableContents = useCallback(
		(users: User[]) => {
			return (
				<Table.ScrollContainer minWidth={800} maxHeight={500}>
					<Table w={"auto"} horizontalSpacing={"xl"} striped highlightOnHover withTableBorder>
						<Table.Thead>
							<Table.Tr>
								<Table.Th>User ID</Table.Th>
								<Table.Th>User name ↓</Table.Th>
								<Table.Th>User roles</Table.Th>
								<Table.Th>Update user details</Table.Th>
							</Table.Tr>
						</Table.Thead>
						<Table.Tbody>{users.map(userTableRow, users)}</Table.Tbody>
					</Table>
				</Table.ScrollContainer>
			);
		},
		[userTableRow],
	);

	const [contents, setContents] = useState<ReactNode | null>(null);

	useEffect(() => {
		fetch("/auth/users", {
			method: "GET",
			credentials: "include",
			headers: {
				accept: "application/json",
			},
		})
			.then(async (response) => {
				if (response.ok) {
					const users: User[] = (await response.json()).users;
					// Sort by username
					users.sort((userA: User, userB: User) => userA.user_name.localeCompare(userB.user_name));
					setContents(userTableContents(users));
				} else {
					setContents(<Text c={"red"}>Could not load users info.</Text>);
				}
			})
			.catch((error) => {
				console.error(error);
				setContents(<Text c={"red"}>Could not load users info.</Text>);
			});
	}, [userTableContents]);

	return contents;
}
