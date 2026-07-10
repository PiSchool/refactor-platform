/** @type {import('next').NextConfig} */
const API = process.env.PLATFORM_API_ORIGIN || 'http://127.0.0.1:8000';

const nextConfig = {
  output: 'standalone',
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
