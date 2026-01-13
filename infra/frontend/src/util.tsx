import { Badge, Text } from "@mantine/core";
import type { ReactNode } from "react";
import type { User } from "./components/AuthProvider";

/** Returns true if `arr1` and `arr2` share a common string, or undefined if either
 * argument is undefined.
 */
export function commonString(arr1?: string[], arr2?: string[]) {
	if (!arr1 || !arr2) return undefined;
	const set2 = new Set(arr2);
	return arr1.some((val) => set2.has(val));
}

export function userBadges(user: User): ReactNode {
	return user.roles.length > 0 ? (
		user.roles.map((role) => (
			<Badge key={`roleBadge-${role}`} color="cyan">
				{role}
			</Badge>
		))
	) : (
		<Text>(None)</Text>
	);
}
