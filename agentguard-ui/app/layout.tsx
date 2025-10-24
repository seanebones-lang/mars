'use client';

import { Inter } from 'next/font/google';
import './globals.css';
import { WatcherThemeProvider, useThemeMode } from '@/contexts/ThemeContext';
import Navigation from '@/components/Navigation';
import PersistentAlerts from '@/components/PersistentAlerts';
import RealtimeStatsOverlay from '@/components/RealtimeStatsOverlay';
import AIAssistantWidget from '@/components/AIAssistantWidget';
import { Toaster } from 'react-hot-toast';
import { Box, Typography, Link } from '@mui/material';
import { LinkedIn } from '@mui/icons-material';

const inter = Inter({ subsets: ['latin'] });

function AppContent({ children }: { children: React.ReactNode }) {
  const { darkMode, toggleDarkMode } = useThemeMode();

  return (
    <>
      <Navigation darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />
      <main>
        {children}
      </main>
      
      {/* Global Persistent Alerts */}
      <PersistentAlerts position="top-right" maxWidth={420} />
      
      {/* Real-time Stats Overlay */}
      <RealtimeStatsOverlay position="top-left" maxWidth={350} />
      
      {/* AI Assistant Widget - Available on every page */}
      <AIAssistantWidget position="bottom-right" />
      
      {/* Footer with contact info */}
      <Box
        component="footer"
        sx={{
          mt: 8,
          py: 4,
          px: 2,
          borderTop: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          textAlign: 'center',
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          © 2025 Watcher-AI. Real-Time Hallucination Defense for Enterprise AI Systems.
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 3, mb: 2, flexWrap: 'wrap' }}>
          <Link
            href="mailto:info@mothership-ai.com"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: 'primary.main',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            📧 info@mothership-ai.com
          </Link>
          
          <Link
            href="https://watcher.mothership-ai.com"
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: 'primary.main',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            watcher.mothership-ai.com
          </Link>
        </Box>
        
        {/* Legal Links */}
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
          <Link
            href="/terms"
            sx={{
              color: 'text.secondary',
              textDecoration: 'none',
              fontSize: '0.875rem',
              '&:hover': {
                textDecoration: 'underline',
                color: 'primary.main',
              },
            }}
          >
            Terms of Service
          </Link>
          
          <Link
            href="/privacy"
            sx={{
              color: 'text.secondary',
              textDecoration: 'none',
              fontSize: '0.875rem',
              '&:hover': {
                textDecoration: 'underline',
                color: 'primary.main',
              },
            }}
          >
            Privacy Policy
          </Link>
          
          <Link
            href="/license"
            sx={{
              color: 'text.secondary',
              textDecoration: 'none',
              fontSize: '0.875rem',
              '&:hover': {
                textDecoration: 'underline',
                color: 'primary.main',
              },
            }}
          >
            License
          </Link>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            Built by Sean McDonnell
          </Typography>
          
          <Link
            href="https://www.linkedin.com/in/sean-mcdonnell-077b15b8"
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: 'primary.main',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            <LinkedIn fontSize="small" />
            LinkedIn
          </Link>
          
          <Link
            href="https://github.com/seanebones-lang"
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: 'primary.main',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            GitHub
          </Link>
        </Box>
      </Box>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: darkMode ? '#1A1F2E' : '#FFFFFF',
            color: darkMode ? '#E2E8F0' : '#1A202C',
            border: darkMode ? '1px solid #334155' : '1px solid #E2E8F0',
          },
        }}
      />
    </>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>Watcher-AI | Real-Time Hallucination Defense</title>
        <meta name="description" content="Watcher-AI catches AI hallucinations before they impact your business. Enterprise-grade real-time monitoring for AI agents and systems." />
        <meta name="keywords" content="AI hallucination detection, enterprise AI monitoring, real-time AI defense, AI agent testing" />
        <meta name="author" content="Sean McDonnell, Mothership-AI" />
        <meta property="og:title" content="Watcher-AI | Real-Time Hallucination Defense" />
        <meta property="og:description" content="Enterprise-grade AI monitoring that catches hallucinations before they impact your business" />
        <meta property="og:url" content="https://watcher.mothership-ai.com" />
        <meta property="og:type" content="website" />
        <meta property="og:site_name" content="Watcher-AI" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Watcher-AI | Real-Time Hallucination Defense" />
        <meta name="twitter:description" content="Enterprise-grade AI monitoring that catches hallucinations before they impact your business" />
        <link rel="canonical" href="https://watcher.mothership-ai.com" />
      </head>
      <body className={inter.className}>
        <WatcherThemeProvider>
          <AppContent>{children}</AppContent>
        </WatcherThemeProvider>
      </body>
    </html>
  );
}
