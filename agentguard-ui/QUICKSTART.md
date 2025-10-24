# AgentGuard UI - Quick Start Guide

## Installation & Running

### 1. Install Dependencies

```bash
cd agentguard-ui
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Backend API

In a separate terminal:

```bash
cd ..
source venv/bin/activate
python -m src.api.main
```

The backend API should be running on http://localhost:8000

### 4. Start Frontend

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

## Usage

### Dashboard
1. Enter agent output and ground truth
2. Click "Run Test"
3. View results in the table

### Demo Mode
1. Navigate to Demo tab
2. Follow guided walkthrough
3. Run pre-configured scenarios

### Metrics
1. Navigate to Metrics tab
2. View charts and analytics
3. Track accuracy and latency

## Troubleshooting

**API Connection Error**:
- Ensure backend is running: `curl http://localhost:8000/health`
- Check .env.local has correct API URL

**Build Errors**:
- Clear cache: `rm -rf .next`
- Reinstall: `rm -rf node_modules && npm install`

## Production Deployment

### Build
```bash
npm run build
npm start
```

### Docker
```bash
docker build -t agentguard-ui .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 agentguard-ui
```

### Vercel
```bash
vercel --prod
```

Set environment variable: `NEXT_PUBLIC_API_URL=your_production_api_url`

