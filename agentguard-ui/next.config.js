/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production domain configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? 'https://api.watcher.mothership-ai.com/:path*'
          : 'http://localhost:8000/:path*',
      },
    ];
  },
  
  // SEO and performance optimizations
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Image optimization for production
  images: {
    domains: ['watcher.mothership-ai.com', 'mothership-ai.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // Compression and optimization
  compress: true,
  poweredByHeader: false,
  
  // Environment-specific settings
  env: {
    SITE_URL: process.env.NODE_ENV === 'production' 
      ? 'https://watcher.mothership-ai.com'
      : 'http://localhost:3000',
  },
};

module.exports = nextConfig;
