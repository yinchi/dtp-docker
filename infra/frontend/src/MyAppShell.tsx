import { AppShell, MantineProvider, Text } from "@mantine/core";

function MyAppShell({ children }: { children: React.ReactNode }) {
	/**
	 * A display wrapper using Mantine's AppShell with a predefined header and footer.
	 *
	 * Also wraps the AppShell in a MantineProvider so that the full page can be rendered in
	 * a single MyAppShell component.
	 *
	 * @param main The main contents of the page to be displayed.
	 */
	const header_height =
		"calc(1rem * var(--mantine-line-height-xl) + 2 * var(--mantine-spacing-md))";
	const footer_height =
		"calc(1rem * var(--mantine-line-height-md) + 2 * var(--mantine-spacing-md))";

	return (
		<MantineProvider>
			<AppShell
				padding={"md"}
				header={{ height: header_height }}
				footer={{ height: footer_height }}
			>
				<AppShell.Header bg={"dark"}>
					<Text size={"xl"} c={"white"} fw={900} px={"md"} py={"sm"}>
						Digital Twin Platform Demo
					</Text>
				</AppShell.Header>
				<AppShell.Main px={"md"} py={"md"} mt={header_height} mb={footer_height}>
					{children}
				</AppShell.Main>
				<AppShell.Footer bg={"dark"}>
					<Text size={"md"} c={"white"} px={"md"} py={"sm"}>
						<Copyright year={2025} /> Anandarup Mukherjee & Yin-Chi Chan, Institute for
						Manufacturing, University of Cambridge
					</Text>
				</AppShell.Footer>
			</AppShell>
		</MantineProvider>
	);
}

function Copyright({ year }: { year: number }) {
	/**
	 * Displays "{year}" or "{year}-{currentYear}" depending on the current year.
	 */
	const currentYear = new Date().getFullYear();
	return currentYear === year ? (
		<>&copy; {year}</>
	) : (
		<>
			&copy; {year}&ndash;{currentYear}
		</>
	);
}

export default MyAppShell;
