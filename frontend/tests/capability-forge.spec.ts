import { expect, test } from "@playwright/test";

test("unified console opens as a categorized operations dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Aureon Unified Autonomous Console" })).toBeVisible();
  await expect(page.getByTestId("dashboard-content-overview")).toBeVisible();
  await expect(page.getByRole("tab", { name: /Overview/ })).toHaveAttribute("data-state", "active");
  await expect(page.getByRole("heading", { name: "Organism Pulse" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Runtime Mirror" })).toBeVisible();
  await expect(page.getByText("Human Coding Cockpit")).not.toBeVisible();

  await page.getByTestId("dashboard-tab-inventory").click();
  await expect(page).toHaveURL(/#inventory$/);
  await expect(page.getByText("Work Order Filters")).toBeVisible();
  await expect(page.getByText("Source Surface Filters")).toBeVisible();

  await page.getByRole("button", { name: "Blocked" }).click();
  await expect(page.getByText("Frontend Evolution Queue")).toBeVisible();
});

test("coding cockpit exposes the capability forge quality lane", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("dashboard-tab-coding").click();

  await expect(page.getByText("Aureon Coding Organism")).toBeVisible();
  await expect(page.getByText("Human Coding Cockpit")).toBeVisible();
  await expect(page.getByText("Autonomous Coding Capability Gates", { exact: true })).toBeVisible();
  await expect(page.getByText("coding_capabilities_unblocked_with_autonomous_gates", { exact: true })).toBeVisible();
  await expect(page.getByText("GitHub and open-source reference scan", { exact: true })).toBeVisible();
  await expect(page.getByText("Local Capability Forge", { exact: true })).toBeVisible();
  await expect(page.getByText("Complex Build Stress Certification", { exact: true })).toBeVisible();
  await expect(page.getByText("complex_build_stress_certified_after_repairs", { exact: true })).toBeVisible();
  await expect(page.getByText("cases 10/10", { exact: true })).toBeVisible();
  await expect(page.getByText("Ollama Cognitive Handshake")).toBeVisible();
  await expect(page.getByText("Ollama reachable")).toBeVisible();
  await expect(page.getByText("Handshake Proof")).toBeVisible();
  await expect(page.getByText("Quality Checks")).toBeVisible();
  await expect(page.getByText("Client Approval Controls")).toBeVisible();
  await expect(page.getByText("Metacognitive Creative Process Guardian")).toBeVisible();
  await expect(page.getByText("HNC/Auris ready").first()).toBeVisible();
  await expect(page.getByText("roles 41/41")).toBeVisible();
  await expect(page.getByText("score 100%")).toBeVisible();
  await expect(page.getByText("Finished Artifacts")).toBeVisible();
  await expect(page.locator("video").first()).toBeVisible();
  await expect(page.locator('video[src*="/aureon_visual_artifacts/"]').first()).toBeVisible();
});
