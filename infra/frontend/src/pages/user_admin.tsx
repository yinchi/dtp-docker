import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import UserAdminApp from "./UserAdminApp.tsx";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<UserAdminApp />
	</StrictMode>,
);
