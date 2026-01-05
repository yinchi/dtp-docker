import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import MyAccountApp from "./MyAccountApp.tsx";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<MyAccountApp />
	</StrictMode>,
);
