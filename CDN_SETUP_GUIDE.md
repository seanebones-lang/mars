# CDN Setup Guide (Cloudflare)

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P1-2: Performance optimization through CDN**

---

## Overview

This guide covers setting up Cloudflare CDN for the AgentGuard platform to improve performance globally.

### Benefits
- **Faster Load Times**: Content served from edge locations near users
- **Reduced Bandwidth**: Caching reduces origin server load
- **DDoS Protection**: Included with Cloudflare
- **Image Optimization**: Automatic image compression and format conversion
- **Global Reach**: 200+ edge locations worldwide

---

## Prerequisites

- Cloudflare account (from WAF setup)
- Domain configured in Cloudflare
- DNS records proxied through Cloudflare (orange cloud)

---

## Step 1: Enable CDN Features

### 1.1 Auto Minify

1. Go to **Speed** → **Optimization**
2. Enable **Auto Minify**:
   -  JavaScript
   -  CSS
   -  HTML

### 1.2 Brotli Compression

1. Go to **Speed** → **Optimization**
2. Enable **Brotli** compression

### 1.3 Early Hints

1. Go to **Speed** → **Optimization**
2. Enable **Early Hints** (HTTP 103)

---

## Step 2: Configure Caching

### 2.1 Caching Level

1. Go to **Caching** → **Configuration**
2. Set **Caching Level** to **Standard**

### 2.2 Browser Cache TTL

1. Go to **Caching** → **Configuration**
2. Set **Browser Cache TTL** to **4 hours** (or **Respect Existing Headers**)

### 2.3 Cache Rules

Create custom cache rules:

#### Rule 1: Cache Static Assets
```yaml
Name: Cache Static Assets
If: (http.request.uri.path matches "^/static/.*")
Then:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week
```

#### Rule 2: Cache Images
```yaml
Name: Cache Images
If: (http.request.uri.path matches "\.(jpg|jpeg|png|gif|webp|svg|ico)$")
Then:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week
```

#### Rule 3: Cache JavaScript/CSS
```yaml
Name: Cache JS/CSS
If: (http.request.uri.path matches "\.(js|css)$")
Then:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 week
  - Browser Cache TTL: 1 day
```

#### Rule 4: Bypass Cache for API
```yaml
Name: Bypass API Cache
If: (http.request.uri.path starts with "/api/")
Then:
  - Cache Level: Bypass
```

---

## Step 3: Image Optimization

### 3.1 Enable Polish (Pro+ plan)

1. Go to **Speed** → **Optimization**
2. Enable **Polish**:
   - **Lossless**: No quality loss
   - **Lossy**: Better compression, slight quality loss

### 3.2 Enable WebP

1. Polish automatically converts images to WebP for supported browsers

### 3.3 Mirage (Pro+ plan)

1. Enable **Mirage** for lazy loading and adaptive image quality

---

## Step 4: Configure Page Rules

### Rule 1: Cache Everything for Static Content

```yaml
URL: watcher.mothership-ai.com/static/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week
```

### Rule 2: Bypass Cache for API

```yaml
URL: watcher.mothership-ai.com/api/*
Settings:
  - Cache Level: Bypass
```

### Rule 3: Cache Health Endpoint (Short TTL)

```yaml
URL: watcher.mothership-ai.com/health
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 10 seconds
  - Browser Cache TTL: 10 seconds
```

---

## Step 5: Argo Smart Routing (Business+ plan)

### 5.1 Enable Argo

1. Go to **Traffic** → **Argo**
2. Enable **Argo Smart Routing**
3. Cost: $5/month + $0.10/GB

### Benefits
- Faster routing through Cloudflare's network
- 30% average improvement in performance
- Automatic failover

---

## Step 6: Configure Cache Headers in Application

### 6.1 Update Next.js Configuration

```javascript
// agentguard-ui/next.config.js

module.exports = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/image:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, stale-while-revalidate=604800',
          },
        ],
      },
    ];
  },
};
```

### 6.2 Update API Cache Headers

```python
# In src/api/main.py

from fastapi.responses import Response

@app.get("/health")
async def health_check():
    response = get_health_status()
    return Response(
        content=json.dumps(response),
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=10, s-maxage=10"
        }
    )

@app.get("/metrics")
async def metrics():
    response = get_metrics()
    return Response(
        content=json.dumps(response),
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=30, s-maxage=30"
        }
    )
```

---

## Step 7: Test CDN Configuration

### 7.1 Check Cache Status

```bash
# Check if response is cached
curl -I https://watcher.mothership-ai.com/health

# Look for headers:
# CF-Cache-Status: HIT (cached)
# CF-Cache-Status: MISS (not cached)
# CF-Cache-Status: BYPASS (cache bypassed)
# CF-Cache-Status: DYNAMIC (not cacheable)
```

### 7.2 Test from Multiple Locations

Use tools like:
- https://www.webpagetest.org/
- https://tools.pingdom.com/
- https://gtmetrix.com/

### 7.3 Check Image Optimization

```bash
# Check if image is optimized
curl -I https://watcher.mothership-ai.com/logo.png

# Look for:
# CF-Polished: origSize=100000, status=success
# Content-Type: image/webp (if browser supports)
```

---

## Step 8: Monitor CDN Performance

### 8.1 Cloudflare Analytics

1. Go to **Analytics** → **Traffic**
2. Monitor:
   - Requests
   - Bandwidth
   - Cache hit ratio
   - Response time

### 8.2 Cache Hit Ratio

**Target**: > 80% cache hit ratio

**Optimization**:
- Increase cache TTL for static content
- Add more cache rules
- Use query string sorting

### 8.3 Bandwidth Savings

**Expected**: 60-80% bandwidth reduction

---

## Step 9: Advanced Optimizations

### 9.1 Tiered Caching (Enterprise)

- Multi-level caching
- Regional cache nodes
- Better cache hit ratios

### 9.2 Cache Reserve (Enterprise)

- Persistent cache storage
- 99%+ cache hit ratio
- Reduced origin load

### 9.3 Cloudflare Workers

Deploy edge functions for:
- A/B testing
- Personalization
- API aggregation
- Response transformation

---

## Performance Targets

### Before CDN
- **TTFB**: 200-500ms
- **Page Load**: 2-3 seconds
- **Bandwidth**: 100 GB/month

### After CDN
- **TTFB**: 50-100ms (5x improvement)
- **Page Load**: 0.5-1 second (3x improvement)
- **Bandwidth**: 20-40 GB/month (60-80% reduction)
- **Cache Hit Ratio**: > 80%

---

## Troubleshooting

### Issue: Low Cache Hit Ratio

**Causes**:
- Short TTL
- Too many unique URLs
- Query strings not sorted

**Solutions**:
- Increase cache TTL
- Use cache rules to normalize URLs
- Enable query string sorting

### Issue: Stale Content

**Causes**:
- Long cache TTL
- No cache invalidation

**Solutions**:
- Use shorter TTL for dynamic content
- Implement cache purging on updates
- Use stale-while-revalidate

### Issue: High Origin Load

**Causes**:
- Cache bypass rules
- Low cache hit ratio
- Large files not cached

**Solutions**:
- Review cache rules
- Increase cache TTL
- Enable Argo for better routing

---

## Cost Optimization

### Free Plan
- Basic CDN
- Unlimited bandwidth
- Basic caching

### Pro Plan ($20/month)
- Image optimization (Polish)
- Mirage (lazy loading)
- Mobile optimization

### Business Plan ($200/month)
- Argo Smart Routing
- Custom cache rules
- 100% uptime SLA

**Recommendation**: Pro plan for production

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AgentGuard Team | Initial version |

**Last Updated**: October 24, 2025

---

**Mothership AI**  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

