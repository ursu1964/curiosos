export const apiBoundaryPaths = [
  "/health/live",
  "/health/ready",
  "/providers",
] as const;

export type ApiBoundaryPath = (typeof apiBoundaryPaths)[number];

export function apiBoundaryUrl(path: ApiBoundaryPath, baseUrl = ""): string {
  const trimmedBaseUrl = baseUrl.trim();
  if (trimmedBaseUrl === "") {
    return path;
  }

  const normalizedBaseUrl = trimmedBaseUrl.endsWith("/")
    ? trimmedBaseUrl
    : `${trimmedBaseUrl}/`;
  return new URL(path, normalizedBaseUrl).toString();
}
