/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output configuration for Render deployment
  output: 'standalone',
  
  // API proxy configuration
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Prevent XSS attacks
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          // Prevent MIME type sniffing
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          // Enhanced XSS protection
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          // Strict referrer policy
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          // HTTPS Strict Transport Security (HSTS)
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
        ],
      },
    ];
  },

  // Image optimization
  images: {
    domains: ['localhost', 'watcher-api.onrender.com', 'mothership-ai.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // Performance optimizations
  compress: true,
  poweredByHeader: false,
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'AgentGuard',
    NEXT_PUBLIC_APP_VERSION: '1.0.0',
    NEXT_PUBLIC_COMPANY_NAME: 'Mothership AI',
    NEXT_PUBLIC_DOMAIN: 'watcher.mothership-ai.com',
    NEXT_PUBLIC_SUPPORT_EMAIL: 'info@mothership-ai.com',
  },
};

module.exports = nextConfig;
