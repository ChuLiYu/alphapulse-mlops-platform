export const config = {
  isDemoMode: import.meta.env.VITE_DEMO_MODE === "true",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "",
} as const;
