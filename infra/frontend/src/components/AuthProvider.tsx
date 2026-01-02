import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
} from "react";
import { hostURL } from "../config";

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
	authFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>; // Wrapper for authenticated fetch
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
		const bearerToken = sessionStorage.getItem("accessToken");
		if (!bearerToken) {
			setUser(null);
			return;
		}

		try {
			const res = await fetch(`${hostURL}/auth/user/me`, {
				headers: { accept: "application/json", Authorization: `Bearer ${bearerToken}` },
				mode: "cors",
			});
			setUser(res.ok ? ((await res.json()) as User) : null);
		} catch {
			setUser(null);
		}
	}, []);

	// Call `refresh` once on component mount and set `loaded` to true
	useEffect(() => {
		refresh().finally(() => setLoaded(true));
	}, [refresh]);

	/** Log the user out by deleting the stored bearer token, and redirect user to /login. */
	const logout = useCallback(() => {
		sessionStorage.removeItem("accessToken");
		setUser(null);
		window.location.href = "/login";
	}, []);

	/** Wraps a `fetch` call to add an Authorization header. */
	const authFetch = useCallback(
		async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
			const bearerToken = sessionStorage.getItem("accessToken");

			const nextInit: RequestInit = { ...init };
			const headers = new Headers(init?.headers);

			// Set CORS unless a fetch mode has already been explicitly set
			nextInit.mode = init?.mode ?? "cors";

			// Default accept header if not already set
			if (!headers.has("accept")) {
				headers.set("accept", "application/json");
			}

			// Add bearer token authorization
			if (bearerToken) {
				headers.set("Authorization", `Bearer ${bearerToken}`);
			}

			nextInit.headers = headers;

			return fetch(input, nextInit);
		},
		[],
	);

	const value = useMemo<AuthState>(
		() => ({ user, loaded, authFetch, refresh, logout }),
		[user, loaded, authFetch, refresh, logout],
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
