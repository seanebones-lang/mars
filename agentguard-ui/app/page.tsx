'use client';

import { Container, Box, Typography, Tabs, Tab } from '@mui/material';
import { useState } from 'react';
import DashboardSummary from '@/components/DashboardSummary';
import TestAgentForm from '@/components/TestAgentForm';
import ResultsTable from '@/components/ResultsTable';
import SystemHealthDashboard from '@/components/SystemHealthDashboard';
import { useStore } from '@/lib/store';

export default function Home() {
  const [activeTab, setActiveTab] = useState(0);
  const { results, realtimeResults } = useStore();
  
  // Calculate system metrics
  const allResults = [...results, ...realtimeResults];
  const totalChecks = allResults.length;
  const flaggedCount = allResults.filter(r => (r as any).flagged || r.hallucination_risk > 0.5).length;
  const flaggedRate = totalChecks > 0 ? (flaggedCount / totalChecks) * 100 : 0;
  const avgRisk = totalChecks > 0 
    ? allResults.reduce((sum, r) => sum + (r.hallucination_risk || 0), 0) / totalChecks * 100
    : 0;
  const avgResponseTime = totalChecks > 0
    ? allResults.reduce((sum, r) => sum + ((r as any).processing_time_ms || 0), 0) / totalChecks
    : 0;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          AI Agent Safety Platform
        </Typography>
        <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
          Validate AI Agents Before Deployment
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Test your AI agents for hallucinations, fabrications, and reliability issues. Prevent unsafe AI responses from reaching customers.
        </Typography>
      </Box>

      {/* Dashboard Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="Agent Validator" />
          <Tab label="Safety Dashboard" />
          <Tab label="Test Results" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {activeTab === 0 && (
        <>
          <DashboardSummary />
          <Box sx={{ mb: 4 }}>
            <TestAgentForm />
          </Box>
        </>
      )}

      {activeTab === 1 && (
        <Box sx={{ overflow: 'visible' }}>
          <SystemHealthDashboard
            overallRisk={avgRisk}
            systemHealth={95} // Mock system health
            responseTime={avgResponseTime}
            activeAgents={3} // IT, Retail, HR
            totalChecks={totalChecks}
            flaggedRate={flaggedRate}
          />
        </Box>
      )}

      {activeTab === 2 && (
        <ResultsTable />
      )}
    </Container>
  );
}
