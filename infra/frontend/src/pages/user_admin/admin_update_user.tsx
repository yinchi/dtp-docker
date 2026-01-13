import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import AdminUpdateUserApp from "./AdminUpdateUserApp";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<AdminUpdateUserApp />
	</StrictMode>,
);
