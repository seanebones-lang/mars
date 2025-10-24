# AgentGuard UI

Enterprise-grade web interface for AgentGuard AI Agent Hallucination Detection Platform.

## Features

- **Dashboard**: Real-time overview of test results, accuracy metrics, and performance indicators
- **Test Interface**: Upload and test AI agent outputs with ground truth validation
- **Results Analysis**: Detailed hallucination reports with confidence intervals and flagged segments
- **Metrics & Analytics**: Visual charts tracking accuracy, latency, and risk distribution
- **Demo Mode**: Guided walkthrough with pre-configured enterprise scenarios (IT, Retail, HR)
- **Multi-Turn Support**: Handle conversation chains for realistic agent testing
- **Export Functionality**: Download results as JSON/CSV for audits and compliance

## Tech Stack

- **Framework**: Next.js 15 with React 19
- **UI Library**: Material-UI (MUI) 6
- **State Management**: Zustand 5
- **Charts**: Chart.js 4 with react-chartjs-2
- **API Client**: Axios
- **Language**: TypeScript

## Quick Start

### Prerequisites

- Node.js 18+ 
- Running AgentGuard backend API (http://localhost:8000)

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The UI will be available at http://localhost:3000

### Environment Configuration

Create `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage

### Running Tests

1. Navigate to **Dashboard**
2. Enter agent output and ground truth in the test form
3. Optionally add conversation history (one message per line)
4. Click "Run Test"
5. View results in the table below

### Batch Testing

1. Prepare JSON file with test scenarios:
```json
[
  {
    "agent_output": "Your agent response",
    "ground_truth": "Expected correct response",
    "conversation_history": ["Message 1", "Message 2"]
  }
]
```
2. Click "Upload JSON" in the test form
3. All scenarios will be processed automatically

### Demo Mode

1. Navigate to **Demo** page
2. Follow the guided walkthrough
3. Run each pre-configured scenario
4. See real-time hallucination detection results

### Viewing Metrics

1. Navigate to **Metrics** page
2. Review charts for:
   - Hallucination risk by test
   - Risk distribution (low/medium/high)
   - Latency over time
3. Track progress toward 92% accuracy and <0.5s latency targets

## API Integration

The UI connects to the AgentGuard FastAPI backend:

- `POST /test-agent` - Run hallucination detection
- `GET /health` - Check API status
- `GET /metrics` - Retrieve MLflow metrics

API client is located in `lib/api.ts`.

## Project Structure

```
agentguard-ui/
├── app/
│   ├── layout.tsx         # Root layout with MUI theme
│   ├── page.tsx           # Dashboard page
│   ├── metrics/
│   │   └── page.tsx       # Metrics page
│   └── demo/
│       └── page.tsx       # Demo mode page
├── components/
│   ├── DashboardSummary.tsx   # Summary cards
│   ├── TestAgentForm.tsx      # Test input form
│   ├── ResultsTable.tsx       # Results data grid
│   ├── ResultModal.tsx        # Detailed result view
│   ├── MetricsCharts.tsx      # Chart.js visualizations
│   ├── DemoMode.tsx           # Demo walkthrough
│   └── Navigation.tsx         # App navigation bar
├── lib/
│   ├── store.ts           # Zustand state management
│   ├── api.ts             # API client
│   └── theme.ts           # MUI theme configuration
└── public/                # Static assets
```

## Development

### Adding New Components

```tsx
import { useStore } from '@/lib/store';
import { agentGuardApi } from '@/lib/api';

export default function MyComponent() {
  const { results, addResult } = useStore();
  
  const runTest = async () => {
    const result = await agentGuardApi.testAgent({...});
    addResult(result);
  };
  
  return <div>{/* Your UI */}</div>;
}
```

### State Management

Global state is managed with Zustand (`lib/store.ts`):

- `results` - Array of test results
- `metrics` - Summary metrics
- `loading` - Loading state
- `apiUrl` - Backend API URL
- `ensembleWeights` - Claude/statistical weights

### Styling

Uses MUI theme (`lib/theme.ts`) with custom colors:

- Primary: #1976D2 (blue)
- Error: #FF5252 (red for high risk)
- Warning: #FF9800 (orange for medium risk)
- Success: #4CAF50 (green for low risk)

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Set environment variable in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` - Your production API URL

### Docker

```bash
# Build
docker build -t agentguard-ui .

# Run
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 agentguard-ui
```

### Docker Compose (with backend)

See `docker-compose.yml` in root project directory for full-stack deployment.

## Performance Targets

- **Accuracy**: 92%+ hallucination detection
- **Latency**: <0.5s per test
- **Coverage**: All enterprise scenarios (IT, Retail, HR)

Monitor these metrics in the **Metrics** page.

## Security

- API key management (stored in backend)
- CORS configuration
- Request validation
- SOC 2 compliance-ready

## Troubleshooting

### "Cannot connect to API"
- Ensure backend is running on http://localhost:8000
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify CORS is enabled in FastAPI backend

### Charts not rendering
- Check browser console for Chart.js errors
- Ensure test results exist before viewing Metrics page

### Build errors
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

## License

Proprietary - AgentGuard Platform  
© 2025 Sean McDonnell. All rights reserved.

## Support

For issues or questions:
- Check backend logs: `../logs/agentguard.log`
- Review browser console for errors
- Ensure API health: `curl http://localhost:8000/health`

---

**Built for enterprise reliability testing - Targeting mid-size IT/retail firms**
