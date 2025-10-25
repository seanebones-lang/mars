# Render Deployment Checklist - AgentGuard Monorepo

**Mothership AI**  
**Date:** October 25, 2025  
**Deployment Type:** Monorepo (Backend + Frontend)

---

## Pre-Deployment Verification

### Repository Configuration
- [x] render.yaml exists and configured for monorepo
- [x] Backend service configured (agentguard-api)
- [x] Frontend service configured (agentguard-ui)
- [x] Python runtime specified (python-3.14.0)
- [x] Node runtime auto-detected (20.x)
- [x] Health checks configured
- [x] Auto-deploy enabled on main branch

### Backend Files
- [x] requirements-render.txt exists with all dependencies
- [x] runtime.txt specifies python-3.14.0
- [x] src/api/main.py exists with FastAPI app
- [x] Health endpoint at /health
- [x] CORS middleware configured
- [x] Environment variables documented

### Frontend Files
- [x] agentguard-ui/package.json exists
- [x] Next.js 16.0.0 configured
- [x] React 19.2.0 configured
- [x] next.config.js with standalone output
- [x] Security headers configured
- [x] API proxy configuration
- [x] Environment variables documented

---

## Deployment Steps

### Step 1: Connect Repository to Render
- [ ] Log in to Render Dashboard
- [ ] Click "New +" → "Blueprint"
- [ ] Connect GitHub repository: seanebones-lang/mars
- [ ] Select branch: main
- [ ] Click "Apply"
- [ ] Wait for services to be created

### Step 2: Configure Backend Environment Variables
- [ ] Navigate to agentguard-api service
- [ ] Go to Environment tab
- [ ] Add required variables:
  - [ ] ENVIRONMENT=production
  - [ ] LOG_LEVEL=INFO
  - [ ] DEBUG=false
  - [ ] CLAUDE_API_KEY (from Anthropic)
  - [ ] OPENAI_API_KEY (from OpenAI)
  - [ ] JWT_SECRET (auto-generated)
  - [ ] API_KEY_SECRET (auto-generated)
  - [ ] CORS_ORIGINS=* (update after frontend deploy)
  - [ ] ENABLE_MULTIMODAL=true
  - [ ] ENABLE_BIAS_AUDITING=true
  - [ ] ENABLE_RED_TEAMING=true
  - [ ] ENABLE_COMPLIANCE_REPORTING=true
- [ ] Save changes

### Step 3: Deploy Backend
- [ ] Wait for automatic deployment to complete
- [ ] Check build logs for errors
- [ ] Verify health check passes
- [ ] Note backend URL: https://agentguard-api.onrender.com

### Step 4: Configure Frontend Environment Variables
- [ ] Navigate to agentguard-ui service
- [ ] Verify NEXT_PUBLIC_API_URL is set (auto-linked)
- [ ] Verify company information:
  - [ ] NEXT_PUBLIC_SUPPORT_EMAIL=info@mothership-ai.com
  - [ ] NEXT_PUBLIC_COMPANY_NAME=Mothership AI
  - [ ] NEXT_PUBLIC_COMPANY_URL=https://mothership-ai.com
  - [ ] NEXT_PUBLIC_DOMAIN=watcher.mothership-ai.com

### Step 5: Deploy Frontend
- [ ] Wait for automatic deployment to complete
- [ ] Check build logs for errors
- [ ] Verify health check passes
- [ ] Note frontend URL: https://agentguard-ui.onrender.com

### Step 6: Update CORS Configuration
- [ ] Go back to agentguard-api → Environment
- [ ] Update CORS_ORIGINS to include frontend URL
- [ ] CORS_ORIGINS=https://agentguard-ui.onrender.com
- [ ] Save and wait for redeploy

---

## Post-Deployment Verification

### Backend API Tests
- [ ] Health check: `curl https://agentguard-api.onrender.com/health`
- [ ] API docs: Visit https://agentguard-api.onrender.com/docs
- [ ] Test endpoint with API key
- [ ] Verify logs show no errors
- [ ] Check metrics (CPU, memory)

### Frontend UI Tests
- [ ] Homepage loads: https://agentguard-ui.onrender.com
- [ ] Dashboard accessible
- [ ] API connection working (check browser console)
- [ ] No console errors
- [ ] Images and assets load
- [ ] Navigation works
- [ ] Forms submit correctly

### Integration Tests
- [ ] Frontend can call backend API
- [ ] Authentication flow works
- [ ] Real-time features work (if applicable)
- [ ] Webhooks configured (if applicable)
- [ ] Error handling works

---

## Custom Domain Configuration (Optional)

### Backend Domain (api.watcher.mothership-ai.com)
- [ ] Add custom domain in Render
- [ ] Configure DNS CNAME record
- [ ] Wait for SSL certificate
- [ ] Update frontend NEXT_PUBLIC_API_URL
- [ ] Update CORS_ORIGINS

### Frontend Domain (watcher.mothership-ai.com)
- [ ] Add custom domain in Render
- [ ] Configure DNS CNAME record
- [ ] Wait for SSL certificate
- [ ] Update backend CORS_ORIGINS
- [ ] Test custom domain

---

## Monitoring Setup

### Render Dashboard
- [ ] Enable email notifications
- [ ] Configure Slack webhook (optional)
- [ ] Set up uptime monitoring
- [ ] Configure alert thresholds

### External Monitoring
- [ ] Set up Cloudflare (if using)
- [ ] Configure Sentry error tracking
- [ ] Set up log aggregation
- [ ] Configure performance monitoring

---

## Security Checklist

- [ ] All environment variables secured
- [ ] No secrets in code
- [ ] HTTPS enforced (automatic)
- [ ] CORS configured correctly
- [ ] Security headers enabled
- [ ] API keys rotated
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] SQL injection protection
- [ ] XSS protection

---

## Performance Checklist

- [ ] Backend workers configured (2)
- [ ] Frontend build optimized
- [ ] Images optimized
- [ ] Caching configured
- [ ] CDN enabled (Cloudflare recommended)
- [ ] Database indexed
- [ ] Redis caching (if configured)
- [ ] Response compression enabled

---

## Troubleshooting

### If Backend Fails
1. Check build logs for errors
2. Verify Python version (3.14.0)
3. Check requirements-render.txt
4. Verify environment variables
5. Check health endpoint code
6. Review application logs

### If Frontend Fails
1. Check build logs for errors
2. Verify Node version
3. Check package.json dependencies
4. Verify NEXT_PUBLIC_API_URL
5. Check next.config.js
6. Review build output

### If Services Can't Connect
1. Verify NEXT_PUBLIC_API_URL is correct
2. Check CORS configuration
3. Verify both services are running
4. Check network tab in browser
5. Review backend logs for CORS errors

---

## Rollback Plan

### If Deployment Fails
1. Go to Render Dashboard → Service → Events
2. Find last successful deployment
3. Click "Rollback to this deploy"
4. Confirm rollback
5. Verify services are working

### If Git-Based Rollback Needed
```bash
git revert HEAD
git push origin main
```

---

## Success Criteria

### Backend
- [ ] Health check returns 200 OK
- [ ] API documentation accessible
- [ ] Test endpoints work
- [ ] Logs show no errors
- [ ] CPU < 50%, Memory < 80%

### Frontend
- [ ] Homepage loads in < 2 seconds
- [ ] All pages accessible
- [ ] API calls succeed
- [ ] No console errors
- [ ] Lighthouse score > 90

### Integration
- [ ] End-to-end user flow works
- [ ] Authentication functional
- [ ] Data persists correctly
- [ ] Real-time features work
- [ ] Error handling graceful

---

## Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Monitor logs continuously
- [ ] Watch for errors
- [ ] Test all major features
- [ ] Verify performance metrics
- [ ] Check user feedback

### Week 1
- [ ] Review error rates
- [ ] Optimize performance
- [ ] Fix any issues
- [ ] Update documentation
- [ ] Plan improvements

### Month 1
- [ ] Analyze usage patterns
- [ ] Review costs
- [ ] Scale if needed
- [ ] Security audit
- [ ] Performance optimization

---

## Contact and Support

**Internal Team:**
- Chief Engineer: Sean McDonnell
- Team: Mothership AI Engineering
- Email: info@mothership-ai.com

**Render Support:**
- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Support: https://render.com/support

---

## Deployment Sign-Off

**Deployed By:** ___________________________  
**Date:** ___________________________  
**Time:** ___________________________  
**Backend URL:** ___________________________  
**Frontend URL:** ___________________________  

**Verification:**
- [ ] All tests passed
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team notified
- [ ] Deployment successful

---

**Mothership AI**  
Enterprise AI Safety & Governance Platform  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)
