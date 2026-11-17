import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_ACTIONS === "true";

const nextConfig: NextConfig = {
  ...(isGitHubPages
    ? {
        output: "export",
        basePath: "/musical-portal",
        assetPrefix: "/musical-portal",
        trailingSlash: true,
        images: { unoptimized: true },
        // Worker-only modules use Cloudflare virtual types that are absent
        // from the static GitHub Pages build.
        typescript: { ignoreBuildErrors: true },
      }
    : {}),
};

export default nextConfig;
