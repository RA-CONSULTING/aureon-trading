import { expect, test } from "@playwright/test";

test("coding cockpit exposes the capability forge quality lane", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Aureon Coding Organism")).toBeVisible();
  await expect(page.getByText("Human Coding Cockpit")).toBeVisible();
  await expect(page.getByText("Local Capability Forge")).toBeVisible();
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
  await expect(page.locator('video[src*="/aureon_visual_artifacts/"]')).toBeVisible();
});
