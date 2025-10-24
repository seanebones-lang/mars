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
  Chip
} from '@mui/material';
import {
  SecurityOutlined,
  BusinessOutlined,
  GavelOutlined,
  InfoOutlined,
  ContactMailOutlined
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export default function TermsOfServicePage() {
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
            <GavelOutlined sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h2" fontWeight={700} color="primary.main">
              Terms of Service
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
            Please read these Terms of Service carefully before using the Watcher-AI platform.
          </Typography>
        </Box>

        {/* Important Notice */}
        <Alert 
          severity="warning" 
          icon={<SecurityOutlined />}
          sx={{ mb: 4 }}
        >
          <Typography variant="h6" gutterBottom>
            Proprietary Enterprise Software
          </Typography>
          <Typography variant="body2">
            Watcher-AI is proprietary software owned by Sean McDonnell. Commercial use requires explicit licensing. 
            Unauthorized use is strictly prohibited and will be prosecuted to the full extent of the law.
          </Typography>
        </Alert>

        <Paper sx={{ p: 4, mb: 4 }}>
          {/* Section 1: Acceptance of Terms */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BusinessOutlined color="primary" />
            1. Acceptance of Terms
          </Typography>
          <Typography variant="body1" paragraph>
            By accessing or using the Watcher-AI platform ("Service"), you agree to be bound by these Terms of Service ("Terms"). 
            If you disagree with any part of these terms, you may not access the Service.
          </Typography>
          <Typography variant="body1" paragraph>
            These Terms apply to all visitors, users, and others who access or use the Service, including enterprise clients, 
            developers, and evaluation users.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 2: Description of Service */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoOutlined color="primary" />
            2. Description of Service
          </Typography>
          <Typography variant="body1" paragraph>
            Watcher-AI is an enterprise-grade AI hallucination detection and monitoring platform that provides:
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="Real-time AI agent monitoring and hallucination detection" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Custom rule engines for industry-specific compliance" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Performance analytics and reporting dashboards" />
            </ListItem>
            <ListItem>
              <ListItemText primary="API integration and webhook services" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Enterprise workstation monitoring capabilities" />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 3: Intellectual Property Rights */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityOutlined color="primary" />
            3. Intellectual Property Rights
          </Typography>
          <Typography variant="body1" paragraph>
            The Service and its original content, features, and functionality are and will remain the exclusive property of 
            Sean McDonnell and his licensors. The Service is protected by copyright, trademark, and other laws.
          </Typography>
          <Typography variant="body1" paragraph>
            Our trademarks and trade dress may not be used in connection with any product or service without our prior 
            written consent.
          </Typography>

          <Alert severity="error" sx={{ my: 3 }}>
            <Typography variant="body2" fontWeight={600}>
              Strictly Prohibited Activities:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Reverse engineering, decompiling, or disassembling the software" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Redistributing, sublicensing, or reselling the Service" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Creating derivative works without explicit permission" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Removing or modifying proprietary notices" />
              </ListItem>
            </List>
          </Alert>

          <Divider sx={{ my: 4 }} />

          {/* Section 4: User Accounts and Responsibilities */}
          <Typography variant="h4" gutterBottom>
            4. User Accounts and Responsibilities
          </Typography>
          <Typography variant="body1" paragraph>
            When you create an account with us, you must provide information that is accurate, complete, and current at all times. 
            You are responsible for safeguarding the password and for all activities that occur under your account.
          </Typography>
          <Typography variant="body1" paragraph>
            You agree not to disclose your password to any third party and to take sole responsibility for activities under your account.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 5: Acceptable Use Policy */}
          <Typography variant="h4" gutterBottom>
            5. Acceptable Use Policy
          </Typography>
          <Typography variant="body1" paragraph>
            You may use our Service only for lawful purposes and in accordance with these Terms. You agree not to use the Service:
          </Typography>
          <List>
            <ListItem>
              <ListItemText primary="In any way that violates applicable federal, state, local, or international law" />
            </ListItem>
            <ListItem>
              <ListItemText primary="To attempt to gain unauthorized access to any portion of the Service" />
            </ListItem>
            <ListItem>
              <ListItemText primary="To interfere with or disrupt the Service or servers connected to the Service" />
            </ListItem>
            <ListItem>
              <ListItemText primary="For any commercial purpose without a valid commercial license" />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Section 6: Privacy and Data Protection */}
          <Typography variant="h4" gutterBottom>
            6. Privacy and Data Protection
          </Typography>
          <Typography variant="body1" paragraph>
            Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the Service, 
            to understand our practices.
          </Typography>
          <Typography variant="body1" paragraph>
            We implement appropriate security measures to protect your personal information and maintain enterprise-grade 
            data protection standards.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 7: Commercial Licensing */}
          <Typography variant="h4" gutterBottom>
            7. Commercial Licensing
          </Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Evaluation Use:</strong> The Service may be used for evaluation purposes only without a commercial license.
            </Typography>
          </Alert>
          <Typography variant="body1" paragraph>
            Any commercial use, deployment in production environments, or integration into commercial products requires 
            a separate commercial license agreement with Sean McDonnell.
          </Typography>
          <Typography variant="body1" paragraph>
            For commercial licensing inquiries, please visit{' '}
            <Link href="https://watcher.mothership-ai.com" target="_blank" rel="noopener noreferrer">
              watcher.mothership-ai.com
            </Link>{' '}
            or contact us directly.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 8: Disclaimers and Limitation of Liability */}
          <Typography variant="h4" gutterBottom>
            8. Disclaimers and Limitation of Liability
          </Typography>
          <Typography variant="body1" paragraph>
            THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. SEAN MCDONNELL EXPRESSLY DISCLAIMS ALL 
            WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED.
          </Typography>
          <Typography variant="body1" paragraph>
            IN NO EVENT SHALL SEAN MCDONNELL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE 
            DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 9: Termination */}
          <Typography variant="h4" gutterBottom>
            9. Termination
          </Typography>
          <Typography variant="body1" paragraph>
            We may terminate or suspend your account and bar access to the Service immediately, without prior notice or liability, 
            under our sole discretion, for any reason whatsoever, including without limitation if you breach the Terms.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 10: Changes to Terms */}
          <Typography variant="h4" gutterBottom>
            10. Changes to Terms
          </Typography>
          <Typography variant="body1" paragraph>
            We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is 
            material, we will provide at least 30 days notice prior to any new terms taking effect.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Section 11: Governing Law */}
          <Typography variant="h4" gutterBottom>
            11. Governing Law
          </Typography>
          <Typography variant="body1" paragraph>
            These Terms shall be interpreted and governed by the laws of the jurisdiction in which Sean McDonnell operates, 
            without regard to its conflict of law provisions.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Contact Information */}
          <Box sx={{ textAlign: 'center', mt: 6 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1 }}>
              <ContactMailOutlined color="primary" />
              Contact Information
            </Typography>
            <Typography variant="body1" paragraph>
              If you have any questions about these Terms of Service, please contact us:
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Link 
                href="https://watcher.mothership-ai.com" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                watcher.mothership-ai.com
              </Link>
              <Link 
                href="mailto:legal@mothership-ai.com"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                legal@mothership-ai.com
              </Link>
            </Box>
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
