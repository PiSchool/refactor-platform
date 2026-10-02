/** @type {import('next').NextConfig} */
const API = process.env.PLATFORM_API_ORIGIN || 'http://127.0.0.1:8000';

const nextConfig = {
  output: 'standalone',
  // The dashboard ships no `next/image`, but Next serves the optimizer at
  // /_next/image regardless, and that endpoint has carried unauthenticated
  // remote-execution advisories. Turning it off removes a route this app never
  // asked for rather than relying on the version in the lockfile staying ahead
  // of the next one.
  images: { unoptimized: true },
  experimental: { optimizePackageImports: ['lucide-react'] },
  // Proxy API + WS to the backend so the browser talks to one origin.
  // Streaming (SSE/WS) passes through untouched — Next does not buffer rewrites.
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${API}/api/:path*` },
      { source: '/ws/:path*', destination: `${API}/ws/:path*` },
    ];
  },
};

export default nextConfig;
