'use client';

import React from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  Alert,
  Link,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  PrivacyTipOutlined,
  SecurityOutlined,
  DataUsageOutlined,
  CookieOutlined,
  ContactMailOutlined,
  ShieldOutlined,
  StorageOutlined,
  DeleteOutlined
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export default function PrivacyPolicyPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: 3 }}>
            <PrivacyTipOutlined sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h2" fontWeight={700} color="primary.main">
              Privacy Policy
            </Typography>
          </Box>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            Watcher-AI Enterprise Platform
          </Typography>
          <Chip 
            label="Effective Date: January 1, 2025" 
            color="primary" 
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <Typography variant="body1" color="text.secondary">
            Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your information.
          </Typography>
        </Box>

        {/* Privacy Commitment */}
        <Alert 
          severity="success" 
          icon={<ShieldOutlined />}
          sx={{ mb: 4 }}
        >
          <Typography variant="h6" gutterBottom>
            Our Privacy Commitment
          </Typography>
          <Typography variant="body2">
            We are committed to protecting your privacy and maintaining the highest standards of data security. 
            We collect only the information necessary to provide our services and never sell your personal data.
          </Typography>
        </Alert>

        <Paper sx={{ p: 4, mb: 4 }}>
          {/* Section 1: Information We Collect */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DataUsageOutlined color="primary" />
            1. Information We Collect
          </Typography>
          
          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            1.1 Information You Provide
          </Typography>
          <Typography variant="body1" paragraph>
            We collect information you directly provide to us, including:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Account Information" 
                secondary="Name, email address, company information, and contact details when you create an account" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Usage Data" 
                secondary="AI agent configurations, custom rules, monitoring preferences, and system settings" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Communication Data" 
                secondary="Messages, feedback, and support requests you send to us" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Payment Information" 
                secondary="Billing details for commercial licenses (processed securely through third-party providers)" 
              />
            </ListItem>
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            1.2 Information We Collect Automatically
          </Typography>
          <Typography variant="body1" paragraph>
            When you use our Service, we automatically collect certain information:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Technical Information" 
                secondary="IP address, browser type, device information, operating system, and access times" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Usage Analytics" 
                secondary="Pages visited, features used, session duration, and interaction patterns" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Performance Metrics" 
                secondary="System performance data, error logs, and service availability metrics" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 2: How We Use Your Information */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityOutlined color="primary" />
            2. How We Use Your Information
          </Typography>
          <Typography variant="body1" paragraph>
            We use the information we collect for the following purposes:
          </Typography>

          <TableContainer component={Paper} variant="outlined" sx={{ my: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Purpose</strong></TableCell>
                  <TableCell><strong>Data Used</strong></TableCell>
                  <TableCell><strong>Legal Basis</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Service Provision</TableCell>
                  <TableCell>Account info, usage data, technical data</TableCell>
                  <TableCell>Contract performance</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Platform Improvement</TableCell>
                  <TableCell>Usage analytics, performance metrics</TableCell>
                  <TableCell>Legitimate interest</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Customer Support</TableCell>
                  <TableCell>Account info, communication data</TableCell>
                  <TableCell>Contract performance</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Security & Fraud Prevention</TableCell>
                  <TableCell>Technical info, usage patterns</TableCell>
                  <TableCell>Legitimate interest</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Legal Compliance</TableCell>
                  <TableCell>All data as required</TableCell>
                  <TableCell>Legal obligation</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Divider sx={{ my: 4 }} />

          {/* Section 3: Data Sharing and Disclosure */}
          <Typography variant="h4" gutterBottom>
            3. Data Sharing and Disclosure
          </Typography>
          <Typography variant="body1" paragraph>
            We do not sell, trade, or rent your personal information to third parties. We may share your information only in the following circumstances:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Service Providers" 
                secondary="Trusted third-party vendors who assist in providing our services (hosting, analytics, payment processing)" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Legal Requirements" 
                secondary="When required by law, court order, or to protect our rights and safety" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Business Transfers" 
                secondary="In connection with a merger, acquisition, or sale of assets (with appropriate safeguards)" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Consent" 
                secondary="When you have given explicit consent for specific sharing purposes" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 4: Data Security */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShieldOutlined color="primary" />
            4. Data Security
          </Typography>
          <Typography variant="body1" paragraph>
            We implement enterprise-grade security measures to protect your information:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Encryption" 
                secondary="Data encrypted in transit (TLS 1.3) and at rest (AES-256)" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Access Controls" 
                secondary="Role-based access controls and multi-factor authentication" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Infrastructure Security" 
                secondary="Secure cloud infrastructure with regular security audits" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Monitoring" 
                secondary="Continuous security monitoring and incident response procedures" 
              />
            </ListItem>
          </List>

          <Alert severity="info" sx={{ my: 3 }}>
            <Typography variant="body2">
              <strong>Security Incident Response:</strong> In the unlikely event of a data breach, we will notify affected users 
              within 72 hours and provide detailed information about the incident and remediation steps.
            </Typography>
          </Alert>

          <Divider sx={{ my: 4 }} />

          {/* Section 5: Data Retention */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StorageOutlined color="primary" />
            5. Data Retention
          </Typography>
          <Typography variant="body1" paragraph>
            We retain your information for as long as necessary to provide our services and comply with legal obligations:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Account Data" 
                secondary="Retained while your account is active and for 3 years after account closure" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Usage Analytics" 
                secondary="Aggregated and anonymized data retained for up to 5 years for service improvement" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Legal Records" 
                secondary="Information required for legal compliance retained as required by applicable law" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 6: Your Rights */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DeleteOutlined color="primary" />
            6. Your Privacy Rights
          </Typography>
          <Typography variant="body1" paragraph>
            Depending on your location, you may have the following rights regarding your personal information:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Access" 
                secondary="Request a copy of the personal information we hold about you" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Correction" 
                secondary="Request correction of inaccurate or incomplete information" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Deletion" 
                secondary="Request deletion of your personal information (subject to legal requirements)" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Portability" 
                secondary="Request transfer of your data to another service provider" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Objection" 
                secondary="Object to processing of your information for certain purposes" 
              />
            </ListItem>
          </List>

          <Alert severity="info" sx={{ my: 3 }}>
            <Typography variant="body2">
              To exercise your privacy rights, please contact us at{' '}
              <Link href="mailto:privacy@mothership-ai.com">privacy@mothership-ai.com</Link>. 
              We will respond to your request within 30 days.
            </Typography>
          </Alert>

          <Divider sx={{ my: 4 }} />

          {/* Section 7: Cookies and Tracking */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CookieOutlined color="primary" />
            7. Cookies and Tracking Technologies
          </Typography>
          <Typography variant="body1" paragraph>
            We use cookies and similar technologies to enhance your experience and analyze usage patterns:
          </Typography>

          <TableContainer component={Paper} variant="outlined" sx={{ my: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Cookie Type</strong></TableCell>
                  <TableCell><strong>Purpose</strong></TableCell>
                  <TableCell><strong>Duration</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Essential</TableCell>
                  <TableCell>Required for basic site functionality</TableCell>
                  <TableCell>Session</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Authentication</TableCell>
                  <TableCell>Keep you logged in securely</TableCell>
                  <TableCell>30 days</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Preferences</TableCell>
                  <TableCell>Remember your settings and preferences</TableCell>
                  <TableCell>1 year</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Analytics</TableCell>
                  <TableCell>Understand usage patterns and improve service</TableCell>
                  <TableCell>2 years</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="body2" color="text.secondary">
            You can control cookie preferences through your browser settings. Note that disabling certain cookies may affect site functionality.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 8: International Data Transfers */}
          <Typography variant="h4" gutterBottom>
            8. International Data Transfers
          </Typography>
          <Typography variant="body1" paragraph>
            Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Adequacy Decisions" 
                secondary="Transfers to countries with adequate data protection laws" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Standard Contractual Clauses" 
                secondary="EU-approved contracts for international data transfers" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Certification Programs" 
                secondary="Partners certified under recognized privacy frameworks" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 9: Children's Privacy */}
          <Typography variant="h4" gutterBottom>
            9. Children's Privacy
          </Typography>
          <Typography variant="body1" paragraph>
            Our Service is not intended for children under 16 years of age. We do not knowingly collect personal information 
            from children under 16. If you become aware that a child has provided us with personal information, please contact us 
            immediately.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 10: Changes to Privacy Policy */}
          <Typography variant="h4" gutterBottom>
            10. Changes to This Privacy Policy
          </Typography>
          <Typography variant="body1" paragraph>
            We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy 
            on this page and updating the "Effective Date" at the top.
          </Typography>
          <Typography variant="body1" paragraph>
            For material changes, we will provide additional notice (such as email notification) at least 30 days before the changes take effect.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Contact Information */}
          <Box sx={{ textAlign: 'center', mt: 6 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1 }}>
              <ContactMailOutlined color="primary" />
              Contact Information
            </Typography>
            <Typography variant="body1" paragraph>
              If you have any questions about this Privacy Policy or our data practices, please contact us:
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap', mb: 3 }}>
              <Link 
                href="mailto:privacy@mothership-ai.com"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                privacy@mothership-ai.com
              </Link>
              <Link 
                href="https://watcher.mothership-ai.com" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                watcher.mothership-ai.com
              </Link>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Data Protection Officer: Sean McDonnell
            </Typography>
          </Box>
        </Paper>

        {/* Footer Notice */}
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>Last Updated:</strong> January 1, 2025 | 
            <strong> Version:</strong> 1.0 | 
            <strong> Next Review:</strong> July 1, 2025
          </Typography>
        </Alert>
      </motion.div>
    </Container>
  );
}
