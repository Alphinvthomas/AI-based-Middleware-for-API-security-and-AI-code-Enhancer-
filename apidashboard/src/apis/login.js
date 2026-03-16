// Simple standalone login “API” for the dashboard.
// This is intentionally client-only and does not depend on any backend.

export async function login({ email, password }) {
  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 200));

  const validEmail = "testemail@email.com";
  const validPassword = "test12345";

  if (email === validEmail && password === validPassword) {
    return { status: "ok", message: "Login successful" };
  }

  return { status: "error", message: "Invalid credentials" };
}
