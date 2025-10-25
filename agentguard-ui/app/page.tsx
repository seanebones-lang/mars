'use client';

import React from 'react';
import {
  Container, Box, Typography, Button, Grid, Card, CardContent,
  Stack, Chip, Avatar, AvatarGroup, alpha, useTheme
} from '@mui/material';
import {
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Code as CodeIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  ArrowForward as ArrowForwardIcon,
  GitHub as GitHubIcon,
  AutoAwesome as AutoAwesomeIcon,
  Shield as ShieldIcon,
  Bolt as BoltIcon,
  Psychology as PsychologyIcon,
  CloudDone as CloudDoneIcon
} from '@mui/icons-material';
import Link from 'next/link';

export default function LandingPage() {
  const theme = useTheme();

  const features = [
    {
      icon: <ShieldIcon sx={{ fontSize: 40 }} />,
      title: 'Hallucination Detection',
      description: 'Catch AI hallucinations in real-time with <100ms latency. Multi-model consensus for 95%+ accuracy.',
      color: '#FF6B6B'
    },
    {
      icon: <SecurityIcon sx={{ fontSize: 40 }} />,
      title: 'Prompt Injection Protection',
      description: 'Block malicious prompts before they reach your AI. OWASP Top 10 compliant security.',
      color: '#4ECDC4'
    },
    {
      icon: <SpeedIcon sx={{ fontSize: 40 }} />,
      title: 'Streaming Validation',
      description: 'Token-level analysis for streaming responses. Flag issues as they happen, not after.',
      color: '#95E1D3'
    },
    {
      icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
      title: 'Semantic Caching',
      description: 'Save 40-60% on API costs with intelligent embedding-based caching.',
      color: '#F38181'
    },
    {
      icon: <CodeIcon sx={{ fontSize: 40 }} />,
      title: 'Native Integrations',
      description: 'LangChain, LlamaIndex, CrewAI - drop-in callbacks for your existing code.',
      color: '#AA96DA'
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      title: 'Real-time Analytics',
      description: 'Beautiful dashboards showing safety metrics, costs, and performance trends.',
      color: '#FCBAD3'
    }
  ];

  const stats = [
    { value: '95%', label: 'Detection Accuracy' },
    { value: '<100ms', label: 'Response Time' },
    { value: '40-60%', label: 'Cost Savings' },
    { value: '99.9%', label: 'Uptime SLA' }
  ];

  const testimonials = [
    {
      quote: "AgentGuard caught hallucinations that would have cost us thousands in customer trust.",
      author: "Sarah Chen",
      role: "CTO, AI Startup",
      avatar: "SC"
    },
    {
      quote: "The streaming validation is a game-changer. We catch issues in real-time, not after deployment.",
      author: "Marcus Johnson",
      role: "Lead Engineer, Enterprise AI",
      avatar: "MJ"
    },
    {
      quote: "Semantic caching alone paid for itself in the first month. 45% reduction in API costs.",
      author: "Priya Patel",
      role: "Head of AI, FinTech",
      avatar: "PP"
    }
  ];

  const pricingTiers = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started',
      features: [
        '100 queries per month',
        'Basic hallucination detection',
        'Prompt injection protection',
        'Community support',
        'API access (rate limited)'
      ],
      cta: 'Start Free',
      highlighted: false
    },
    {
      name: 'Pro',
      price: '$49',
      period: 'per month',
      description: 'For serious developers',
      features: [
        '10,000 queries per month',
        'Advanced multi-model detection',
        'Streaming validation',
        'Semantic caching',
        'Priority support',
        'Custom webhooks',
        'Advanced analytics'
      ],
      cta: 'Start Pro Trial',
      highlighted: true
    },
    {
      name: 'Business',
      price: '$299',
      period: 'per month',
      description: 'For growing teams',
      features: [
        '100,000 queries per month',
        'Everything in Pro',
        'Team collaboration',
        'SSO & RBAC',
        'SLA guarantees',
        'Dedicated support',
        'Custom models',
        'On-premise option'
      ],
      cta: 'Contact Sales',
      highlighted: false
    }
  ];

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
          pt: { xs: 8, md: 12 },
          pb: { xs: 8, md: 12 }
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={6}>
              <Stack spacing={3}>
                <Chip
                  icon={<AutoAwesomeIcon />}
                  label="Production-Ready AI Safety"
                  color="primary"
                  sx={{ width: 'fit-content' }}
                />
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    fontWeight: 800,
                    lineHeight: 1.2,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}
                >
                  Ship AI Agents with Confidence
                </Typography>
                <Typography variant="h5" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  Real-time hallucination detection, prompt injection protection, and semantic caching.
                  <strong> Save 40-60% on API costs</strong> while keeping your AI safe.
                </Typography>
                <Stack direction="row" spacing={2}>
                  <Button
                    component={Link}
                    href="/signup"
                    variant="contained"
                    size="large"
                    endIcon={<ArrowForwardIcon />}
                    sx={{
                      py: 1.5,
                      px: 4,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      boxShadow: 4
                    }}
                  >
                    Start Free
                  </Button>
                  <Button
                    component={Link}
                    href="/docs"
                    variant="outlined"
                    size="large"
                    startIcon={<CodeIcon />}
                    sx={{ py: 1.5, px: 4, fontSize: '1.1rem' }}
                  >
                    View Docs
                  </Button>
                </Stack>
                <Stack direction="row" spacing={2} alignItems="center">
                  <AvatarGroup max={4}>
                    <Avatar sx={{ bgcolor: '#FF6B6B' }}>SC</Avatar>
                    <Avatar sx={{ bgcolor: '#4ECDC4' }}>MJ</Avatar>
                    <Avatar sx={{ bgcolor: '#95E1D3' }}>PP</Avatar>
                    <Avatar sx={{ bgcolor: '#F38181' }}>AK</Avatar>
                  </AvatarGroup>
                  <Typography variant="body2" color="text.secondary">
                    Trusted by <strong>500+ developers</strong>
                  </Typography>
                </Stack>
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box
                sx={{
                  bgcolor: 'background.paper',
                  borderRadius: 4,
                  p: 3,
                  boxShadow: 8,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                }}
              >
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  5-Minute Integration
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    bgcolor: alpha(theme.palette.common.black, 0.8),
                    color: '#00ff00',
                    p: 2,
                    borderRadius: 2,
                    overflow: 'auto',
                    fontSize: '0.85rem',
                    fontFamily: 'monospace'
                  }}
                >
{`pip install agentguard-sdk

from agentguard import AgentGuard

guard = AgentGuard(api_key="your_key")

result = await guard.check_safety(
    user_input="Tell me about Mars",
    agent_response="Mars is the 4th planet..."
)

if result.is_safe:
    return agent_response
else:
    return "Safety check failed"`}
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Grid container spacing={4}>
          {stats.map((stat, index) => (
            <Grid item xs={6} md={3} key={index}>
              <Box textAlign="center">
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 800,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}
                >
                  {stat.value}
                </Typography>
                <Typography variant="h6" color="text.secondary">
                  {stat.label}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Features Section */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), py: 10 }}>
        <Container maxWidth="lg">
          <Box textAlign="center" mb={8}>
            <Typography variant="h2" gutterBottom fontWeight={700}>
              Everything You Need for Safe AI
            </Typography>
            <Typography variant="h5" color="text.secondary">
              Production-grade safety features that scale with your business
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'transform 0.3s, box-shadow 0.3s',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: 8
                    }
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: 3,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: alpha(feature.color, 0.1),
                        color: feature.color,
                        mb: 3
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Typography variant="h5" gutterBottom fontWeight={600}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Box textAlign="center" mb={8}>
          <Typography variant="h2" gutterBottom fontWeight={700}>
            Loved by Developers
          </Typography>
          <Typography variant="h5" color="text.secondary">
            See what teams are saying about AgentGuard
          </Typography>
        </Box>
        <Grid container spacing={4}>
          {testimonials.map((testimonial, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card sx={{ height: '100%', p: 3 }}>
                <CardContent>
                  <Typography variant="body1" paragraph sx={{ fontStyle: 'italic', mb: 3 }}>
                    "{testimonial.quote}"
                  </Typography>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                      {testimonial.avatar}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {testimonial.author}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {testimonial.role}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Pricing Section */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), py: 10 }}>
        <Container maxWidth="lg">
          <Box textAlign="center" mb={8}>
            <Typography variant="h2" gutterBottom fontWeight={700}>
              Simple, Transparent Pricing
            </Typography>
            <Typography variant="h5" color="text.secondary">
              Start free, scale as you grow
            </Typography>
          </Box>
          <Grid container spacing={4} justifyContent="center">
            {pricingTiers.map((tier, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    position: 'relative',
                    border: tier.highlighted ? `3px solid ${theme.palette.primary.main}` : '1px solid',
                    borderColor: tier.highlighted ? 'primary.main' : 'divider',
                    transform: tier.highlighted ? 'scale(1.05)' : 'scale(1)',
                    transition: 'transform 0.3s'
                  }}
                >
                  {tier.highlighted && (
                    <Chip
                      label="Most Popular"
                      color="primary"
                      sx={{
                        position: 'absolute',
                        top: -12,
                        left: '50%',
                        transform: 'translateX(-50%)'
                      }}
                    />
                  )}
                  <CardContent sx={{ p: 4 }}>
                    <Typography variant="h4" gutterBottom fontWeight={700}>
                      {tier.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {tier.description}
                    </Typography>
                    <Box mb={3}>
                      <Typography variant="h2" component="span" fontWeight={800}>
                        {tier.price}
                      </Typography>
                      <Typography variant="h6" component="span" color="text.secondary">
                        /{tier.period}
                      </Typography>
                    </Box>
                    <Button
                      component={Link}
                      href="/signup"
                      variant={tier.highlighted ? 'contained' : 'outlined'}
                      fullWidth
                      size="large"
                      sx={{ mb: 3, py: 1.5 }}
                    >
                      {tier.cta}
                    </Button>
                    <Stack spacing={2}>
                      {tier.features.map((feature, idx) => (
                        <Stack direction="row" spacing={1} key={idx}>
                          <CheckCircleIcon color="success" fontSize="small" />
                          <Typography variant="body2">{feature}</Typography>
                        </Stack>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Container maxWidth="md" sx={{ py: 10 }}>
        <Card
          sx={{
            background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
            color: 'white',
            p: 6,
            textAlign: 'center'
          }}
        >
          <Typography variant="h2" gutterBottom fontWeight={700}>
            Ready to Ship Safe AI?
          </Typography>
          <Typography variant="h5" paragraph sx={{ opacity: 0.9 }}>
            Join 500+ developers building the future of AI safely
          </Typography>
          <Stack direction="row" spacing={2} justifyContent="center" mt={4}>
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: 'primary.main',
                py: 1.5,
                px: 4,
                fontSize: '1.1rem',
                '&:hover': {
                  bgcolor: alpha('#ffffff', 0.9)
                }
              }}
              endIcon={<ArrowForwardIcon />}
            >
              Start Free Today
            </Button>
            <Button
              component={Link}
              href="/docs"
              variant="outlined"
              size="large"
              sx={{
                borderColor: 'white',
                color: 'white',
                py: 1.5,
                px: 4,
                fontSize: '1.1rem',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: alpha('#ffffff', 0.1)
                }
              }}
              startIcon={<GitHubIcon />}
            >
              View on GitHub
            </Button>
          </Stack>
        </Card>
      </Container>

      {/* Footer */}
      <Box sx={{ bgcolor: alpha(theme.palette.common.black, 0.02), py: 6 }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Typography variant="h5" gutterBottom fontWeight={700}>
                AgentGuard
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Production-grade AI safety for developers who ship fast.
              </Typography>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Product
              </Typography>
              <Stack spacing={1}>
                <Link href="/features" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Features</Typography>
                </Link>
                <Link href="/pricing" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Pricing</Typography>
                </Link>
                <Link href="/docs" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Documentation</Typography>
                </Link>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Company
              </Typography>
              <Stack spacing={1}>
                <Link href="/about" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">About</Typography>
                </Link>
                <Link href="/blog" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Blog</Typography>
                </Link>
                <Link href="/careers" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Careers</Typography>
                </Link>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Resources
              </Typography>
              <Stack spacing={1}>
                <Link href="/status" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Status</Typography>
                </Link>
                <Link href="/support" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Support</Typography>
                </Link>
                <Link href="/security" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Security</Typography>
                </Link>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                Legal
              </Typography>
              <Stack spacing={1}>
                <Link href="/privacy" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Privacy</Typography>
                </Link>
                <Link href="/terms" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="text.secondary">Terms</Typography>
                </Link>
              </Stack>
            </Grid>
          </Grid>
          <Box mt={6} pt={4} borderTop={1} borderColor="divider">
            <Typography variant="body2" color="text.secondary" textAlign="center">
              © 2025 AgentGuard. All rights reserved. Made with ❤️ for developers.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}
