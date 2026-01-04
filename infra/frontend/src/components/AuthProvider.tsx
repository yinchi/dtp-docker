import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
} from "react";

/** Represents an authenticated user. */
export interface User {
	user_id: string;
	user_name: string;
	roles: string[];
}

/** The type returned by `AuthContext.Provider`. */
type AuthState = {
	user: User | null;
	loaded: boolean;
	refresh: () => Promise<void>; // (Re)validate the bearer token
	logout: () => void; // Delete the bearer token
};

/** The context returned by calling `useAuth()` within an `AuthProvider`. */
const AuthContext = createContext<AuthState | null>(null);

/** The Authentication context provider. */
export function AuthProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<User | null>(null);
	const [loaded, setLoaded] = useState<boolean>(false);

	/** Fetch user information using the stored bearer token.
	 *
	 * Sets `user` to the  authenticated user, or null if the token is invalid or missing
	 * (or `fetch` fails).
	 */
	const refresh = useCallback(async () => {
		try {
			const res = await fetch(`/auth/users/me`, {
				headers: { accept: "application/json" },
				credentials: "include",
			});
			if (!res.ok) {
				console.warn("/auth/users/me returned", res.status);
				setUser(null);
				return;
			}
			setUser((await res.json()) as User);
		} catch (err) {
			console.error("/auth/users/me fetch failed", err);
			setUser(null);
		}
	}, []);

	// Call `refresh` once on component mount and set `loaded` to true
	useEffect(() => {
		refresh().finally(() => setLoaded(true));
	}, [refresh]);

	/** Log the user out by deleting the stored bearer token, and redirect user to /login. */
	const logout = useCallback(() => {
		fetch(`/auth/logout`, {
			method: "POST",
			credentials: "include",
			headers: { accept: "application/json" },
		}).finally(() => {
			setUser(null);
			window.location.href = "/login";
		});
	}, []);

	const value = useMemo<AuthState>(
		() => ({ user, loaded, refresh, logout }),
		[user, loaded, refresh, logout],
	);

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Fetch the AuthState from an AuthProvider.
 * @returns The AuthState.
 * @throws Error, if called outside of an AuthProvider.
 */
export function useAuth() {
	const ctx = useContext(AuthContext);
	if (!ctx) throw new Error("useAuth must be used within AuthProvider");
	return ctx;
}
