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
  
  // CRITICAL SECURITY HEADERS - Enterprise Grade Protection
  async headers() {
    // Strict Content Security Policy to prevent XSS attacks
    const cspHeader = `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline' https://vercel.live https://va.vercel-scripts.com;
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
      img-src 'self' blob: data: https: *.mothership-ai.com *.vercel.app;
      font-src 'self' https://fonts.gstatic.com;
      connect-src 'self' https://api.watcher.mothership-ai.com wss://api.watcher.mothership-ai.com https://watcher-api.onrender.com wss://watcher-api.onrender.com ws://localhost:8000 http://localhost:8000;
      frame-ancestors 'none';
      base-uri 'self';
      form-action 'self';
      object-src 'none';
      upgrade-insecure-requests;
    `.replace(/\s{2,}/g, ' ').trim();

    return [
      {
        source: '/(.*)',
        headers: [
          // Prevent XSS attacks
          {
            key: 'Content-Security-Policy',
            value: cspHeader,
          },
          // Prevent clickjacking
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
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          // Permissions policy (restrict dangerous features)
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=()',
          },
          // Cross-Origin policies
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'credentialless',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'same-origin',
          },
        ],
      },
    ];
  },

  // Secure image optimization for production
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'watcher.mothership-ai.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'mothership-ai.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.vercel.app',
        port: '',
        pathname: '/**',
      },
    ],
    formats: ['image/webp', 'image/avif'],
    dangerouslyAllowSVG: false,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
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
