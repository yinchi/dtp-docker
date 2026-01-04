import { StrictMode } from "react";
import { CookiesProvider } from "react-cookie";
import { createRoot } from "react-dom/client";
import MainApp from "./MainApp.tsx";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<CookiesProvider>
			<MainApp />
		</CookiesProvider>
	</StrictMode>,
);
