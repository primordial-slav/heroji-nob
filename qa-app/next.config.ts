import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  serverExternalPackages: ['better-sqlite3'],
  webpack: (config) => {
    // react-pdf needs canvas polyfill disabled
    config.resolve.alias.canvas = false
    return config
  },
}

export default nextConfig
