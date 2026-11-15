import { test, expect, Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { mkdirSync } from "node:fs";
import path from "node:path";
const images = path.resolve("../../docs/images");
mkdirSync(images, { recursive: true });

async function account(page: Page) {
  const email = randomUUID() + "@example.test";
  const response = await page.request.post("/api/auth/register", {
    data: { email, password: randomUUID() + "!test" },
  });
  expect(response.ok()).toBeTruthy();
}

async function draft(page: Page) {
  await account(page);
  await page.goto("/jobs/syn-job-001");
  await page.getByRole("button", { name: "Analyze this opportunity" }).click();
  await expect(
    page.getByText("awaiting approval", { exact: true }),
  ).toBeVisible({ timeout: 45000 });
  await page.getByRole("link", { name: "Open proposal studio" }).click();
  await expect(page.getByLabel("Draft editor")).toBeVisible();
}

test("onboarding persists profile and uploaded portfolio", async ({ page }) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "New here? Create an account" })
    .click();
  await page.getByLabel("Email address").fill(randomUUID() + "@example.test");
  await page
    .getByLabel("Password", { exact: true })
    .fill(randomUUID() + "!test");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Set up your workspace." }),
  ).toBeVisible();
  await page.getByLabel("Portfolio persona").selectOption("web");
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("saved");
  await page
    .getByLabel("Upload portfolio")
    .setInputFiles({
      name: "case.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(
        "Built a React portal with TypeScript and audited accessibility.",
      ),
    });
  await expect(page.getByRole("status")).toContainText("indexed");
  await page.reload();
  await expect(page.getByLabel("Portfolio persona")).toHaveValue("web");
});

test("approval resumes saved interrupt and submits once", async ({ page }) => {
  await draft(page);
  await page.screenshot({
    path: path.join(images, "proposal-studio.png"),
    fullPage: true,
  });
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Approve proposal" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Approve proposal" }).click();
  await expect(page.getByText("submitted", { exact: true })).toBeVisible({
    timeout: 30000,
  });
  const analytics = await (await page.request.get("/api/analytics")).json();
  expect(analytics.wallet.weekly_spent).toBe(10);
  await page.reload();
  expect(
    (await (await page.request.get("/api/analytics")).json()).wallet
      .weekly_spent,
  ).toBe(10);
});

test("rejecting requires a reason and spends no Connects", async ({ page }) => {
  await draft(page);
  await expect(
    page.getByRole("button", { name: "Reject draft" }),
  ).toBeDisabled();
  await page
    .getByLabel("Rejection reason")
    .fill("The delivery window does not fit my schedule.");
  await page.getByRole("button", { name: "Reject draft" }).click();
  await expect(page.getByText("rejected", { exact: true })).toBeVisible({
    timeout: 30000,
  });
  expect(
    (await (await page.request.get("/api/analytics")).json()).wallet
      .weekly_spent,
  ).toBe(0);
});

test("editing verifies the exact text before approval", async ({ page }) => {
  await draft(page);
  const editor = page.getByLabel("Draft editor");
  const original = await editor.inputValue();
  await editor.fill(original + "\n\nI propose a weekly milestone check-in.");
  await page.getByRole("button", { name: "Save & verify edit" }).click();
  await expect(page.getByRole("status")).toContainText("verified");
  await page.getByRole("button", { name: "Approve proposal" }).click();
  await expect(page.getByText("submitted", { exact: true })).toBeVisible({
    timeout: 30000,
  });
  const runId = new URL(page.url()).pathname.split("/").pop();
  const result = await (await page.request.get("/api/runs/" + runId)).json();
  expect(result.state.outcome.text).toContain("weekly milestone check-in");
});

test("unavailable marketplace produces a useful degraded banner", async ({
  page,
}) => {
  await account(page);
  await page.route("**/api/jobs?*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Marketplace unavailable. Your work is saved.",
      }),
    }),
  );
  await page.goto("/inbox");
  await expect(page.getByRole("alert")).toContainText(
    "Marketplace unavailable",
  );
});

test("inbox is responsive and captures actual UI", async ({ page }) => {
  await account(page);
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto("/inbox");
  await expect(
    page.getByRole("heading", { name: "Find work worth your time." }),
  ).toBeVisible();
  await expect(page.locator(".job-card").first()).toBeVisible();
  await page.screenshot({ path: path.join(images, "inbox-desktop.png") });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".sidebar")).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, -244, 0)",
  );
  await page.screenshot({
    path: path.join(images, "inbox-mobile.png"),
    fullPage: false,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    page.getByRole("link", { name: "Messages", exact: true }),
  ).toBeVisible();
});
