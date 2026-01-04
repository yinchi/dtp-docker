import { StrictMode } from "react";
import { CookiesProvider } from "react-cookie";
import { createRoot } from "react-dom/client";
import LoginApp from "./LoginApp.tsx";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<CookiesProvider>
			<LoginApp />
		</CookiesProvider>
	</StrictMode>,
);
