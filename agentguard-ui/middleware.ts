/**
 * Next.js Middleware for Enterprise Security
 * Implements CSRF protection, rate limiting, and security headers
 */

import { NextRequest, NextResponse } from 'next/server';

// Security configuration
const SECURITY_CONFIG = {
  RATE_LIMIT_WINDOW: 60 * 1000, // 1 minute
  RATE_LIMIT_MAX_REQUESTS: 100,
  CSRF_HEADER_NAME: 'X-CSRF-Token',
  ALLOWED_ORIGINS: [
    'https://watcher.mothership-ai.com',
    'https://agentguard-ui.vercel.app',
    'http://localhost:3000',
    'http://localhost:3001',
  ],
};

// In-memory rate limiting store (use Redis in production)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

function getRateLimitKey(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIp = request.headers.get('x-real-ip');
  const ip = forwarded?.split(',')[0] || realIp || 'unknown';
  return `rate_limit:${ip}`;
}

function checkRateLimit(request: NextRequest): boolean {
  const key = getRateLimitKey(request);
  const now = Date.now();
  const record = rateLimitStore.get(key);

  if (!record || now > record.resetTime) {
    // Reset or create new record
    rateLimitStore.set(key, {
      count: 1,
      resetTime: now + SECURITY_CONFIG.RATE_LIMIT_WINDOW,
    });
    return true;
  }

  if (record.count >= SECURITY_CONFIG.RATE_LIMIT_MAX_REQUESTS) {
    return false;
  }

  record.count++;
  return true;
}

function validateCSRF(request: NextRequest): boolean {
  // Skip CSRF for GET requests and API routes
  if (request.method === 'GET' || request.nextUrl.pathname.startsWith('/api/')) {
    return true;
  }

  const origin = request.headers.get('origin');
  const referer = request.headers.get('referer');
  
  // Check origin header
  if (origin && !SECURITY_CONFIG.ALLOWED_ORIGINS.includes(origin)) {
    return false;
  }

  // Check referer header as fallback
  if (!origin && referer) {
    const refererOrigin = new URL(referer).origin;
    if (!SECURITY_CONFIG.ALLOWED_ORIGINS.includes(refererOrigin)) {
      return false;
    }
  }

  return true;
}

function addSecurityHeaders(response: NextResponse): NextResponse {
  // Additional security headers not covered in next.config.js
  response.headers.set('X-DNS-Prefetch-Control', 'off');
  response.headers.set('X-Download-Options', 'noopen');
  response.headers.set('X-Permitted-Cross-Domain-Policies', 'none');
  
  // Cache control for sensitive pages
  if (response.url.includes('/dashboard') || response.url.includes('/workstations')) {
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
    response.headers.set('Pragma', 'no-cache');
    response.headers.set('Expires', '0');
  }

  return response;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for static assets and Next.js internals
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  // Rate limiting check
  if (!checkRateLimit(request)) {
    return new NextResponse('Rate limit exceeded', {
      status: 429,
      headers: {
        'Retry-After': '60',
        'X-RateLimit-Limit': SECURITY_CONFIG.RATE_LIMIT_MAX_REQUESTS.toString(),
        'X-RateLimit-Remaining': '0',
      },
    });
  }

  // CSRF protection
  if (!validateCSRF(request)) {
    return new NextResponse('CSRF validation failed', {
      status: 403,
      headers: {
        'X-Security-Error': 'CSRF_VALIDATION_FAILED',
      },
    });
  }

  // Create response and add security headers
  const response = NextResponse.next();
  return addSecurityHeaders(response);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
