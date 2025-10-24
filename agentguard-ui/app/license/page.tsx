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
  Card,
  CardContent,
  Grid,
  Button
} from '@mui/material';
import {
  CopyrightOutlined,
  SecurityOutlined,
  BusinessOutlined,
  WarningOutlined,
  ContactMailOutlined,
  VerifiedUserOutlined,
  MonetizationOnOutlined,
  BlockOutlined
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export default function LicenseInformationPage() {
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
            <CopyrightOutlined sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h2" fontWeight={700} color="primary.main">
              License Information
            </Typography>
          </Box>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            Watcher-AI Proprietary Software License
          </Typography>
          <Chip 
            label="Proprietary License - All Rights Reserved" 
            color="error" 
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <Typography variant="body1" color="text.secondary">
            This software is proprietary and protected by copyright law. Commercial use requires explicit licensing.
          </Typography>
        </Box>

        {/* License Status Alert */}
        <Alert 
          severity="error" 
          icon={<SecurityOutlined />}
          sx={{ mb: 4 }}
        >
          <Typography variant="h6" gutterBottom>
            Proprietary Software - Not Open Source
          </Typography>
          <Typography variant="body2">
            This software is NOT open source and is NOT free software. All rights are reserved by Sean McDonnell. 
            Unauthorized use, copying, or distribution is strictly prohibited and will be prosecuted to the full extent of the law.
          </Typography>
        </Alert>

        {/* License Types */}
        <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
          Available License Types
        </Typography>

        <Grid container spacing={4} sx={{ mb: 6 }}>
          {/* Evaluation License */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: '100%', border: '2px solid', borderColor: 'info.main' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <VerifiedUserOutlined color="info" />
                  <Typography variant="h5" color="info.main">
                    Evaluation License
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Limited license for evaluation and testing purposes only.
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Non-commercial use only" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="30-day evaluation period" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="No production deployment" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="No redistribution rights" />
                  </ListItem>
                </List>
                <Typography variant="h6" color="info.main" sx={{ mt: 2 }}>
                  FREE
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Commercial License */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: '100%', border: '2px solid', borderColor: 'success.main' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <MonetizationOnOutlined color="success" />
                  <Typography variant="h5" color="success.main">
                    Commercial License
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Full commercial license for production deployment and business use.
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Production deployment rights" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Commercial use permitted" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Priority support included" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Custom integration support" />
                  </ListItem>
                </List>
                <Button 
                  variant="contained" 
                  color="success" 
                  sx={{ mt: 2 }}
                  href="https://watcher.mothership-ai.com"
                  target="_blank"
                >
                  Contact for Pricing
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Paper sx={{ p: 4, mb: 4 }}>
          {/* Copyright Notice */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CopyrightOutlined color="primary" />
            Copyright Notice
          </Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Copyright © 2025 Sean McDonnell. All rights reserved.
            </Typography>
            <Typography variant="body2">
              This software and all associated documentation, code, algorithms, designs, and methodologies are the 
              exclusive intellectual property of Sean McDonnell.
            </Typography>
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
            Protected Elements Include:
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Source Code and Binaries" 
                secondary="All source code, compiled binaries, and executable files" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Documentation" 
                secondary="Technical specifications, user manuals, and API documentation" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="User Interface Designs" 
                secondary="All UI/UX designs, layouts, and visual elements" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Algorithms and Business Logic" 
                secondary="Proprietary algorithms, AI models, and business processes" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Database Schemas" 
                secondary="Data structures, database designs, and data models" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="API Designs" 
                secondary="API specifications, endpoints, and integration methods" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Restrictions */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BlockOutlined color="error" />
            License Restrictions
          </Typography>
          
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Strictly Prohibited Activities
            </Typography>
            <Typography variant="body2">
              The following activities are strictly prohibited without explicit written permission:
            </Typography>
          </Alert>

          <List>
            <ListItem>
              <ListItemText 
                primary="Commercial Use Without License" 
                secondary="Any commercial use, deployment, or integration requires a separate commercial license" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Redistribution" 
                secondary="Redistribution in any form (source code, binaries, or documentation) is strictly prohibited" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Reverse Engineering" 
                secondary="Reverse engineering, decompiling, or disassembling the software is prohibited" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Modification" 
                secondary="Modification, adaptation, or creation of derivative works without permission is prohibited" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Removal of Notices" 
                secondary="Removing or modifying copyright notices, license terms, or proprietary markings is prohibited" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Sublicensing" 
                secondary="Sublicensing, leasing, or transferring rights to third parties is prohibited" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* License Terms */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BusinessOutlined color="primary" />
            License Terms
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Evaluation License Terms
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Purpose" 
                secondary="Software may be used for evaluation and testing purposes only" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Duration" 
                secondary="Evaluation period is limited to 30 days from first use" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Scope" 
                secondary="Non-commercial use only - no production deployment permitted" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Support" 
                secondary="Limited community support only - no guaranteed response times" 
              />
            </ListItem>
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Commercial License Terms
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Commercial Use" 
                secondary="Full rights for commercial deployment and business use" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Production Deployment" 
                secondary="Authorized for production environments and customer-facing applications" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Support" 
                secondary="Priority technical support with guaranteed response times" 
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="Updates" 
                secondary="Access to software updates and new features during license term" 
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 4 }} />

          {/* Third-Party Components */}
          <Typography variant="h4" gutterBottom>
            Third-Party Components
          </Typography>
          <Typography variant="body1" paragraph>
            This software may include third-party components that are subject to their own license terms. 
            The use of third-party components does not affect Sean McDonnell's ownership of the original work 
            and derivative works created.
          </Typography>
          <Typography variant="body1" paragraph>
            All third-party components are properly licensed and attributed. A complete list of third-party 
            components and their licenses is available upon request.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Disclaimer */}
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningOutlined color="warning" />
            Disclaimer
          </Typography>
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>NO WARRANTY:</strong> This software is provided "AS IS" without warranty of any kind, 
              express or implied, including but not limited to the warranties of merchantability, fitness for 
              a particular purpose, and noninfringement.
            </Typography>
          </Alert>
          <Typography variant="body1" paragraph>
            In no event shall Sean McDonnell be liable for any claim, damages, or other liability, whether in 
            an action of contract, tort, or otherwise, arising from, out of, or in connection with the software 
            or the use or other dealings in the software.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Legal Enforcement */}
          <Typography variant="h4" gutterBottom>
            Legal Enforcement
          </Typography>
          <Typography variant="body1" paragraph>
            Sean McDonnell actively protects intellectual property rights and will pursue legal action against 
            any unauthorized use, copying, distribution, or infringement of this software.
          </Typography>
          <Typography variant="body1" paragraph>
            Violations of this license may result in immediate termination of your rights to use the software 
            and may subject you to civil and criminal penalties.
          </Typography>

          <Divider sx={{ my: 4 }} />

          {/* Contact Information */}
          <Box sx={{ textAlign: 'center', mt: 6 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1 }}>
              <ContactMailOutlined color="primary" />
              Licensing Inquiries
            </Typography>
            <Typography variant="body1" paragraph>
              For commercial licensing, questions about license terms, or to report license violations:
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap', mb: 3 }}>
              <Link 
                href="https://watcher.mothership-ai.com" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                watcher.mothership-ai.com
              </Link>
              <Link 
                href="mailto:licensing@mothership-ai.com"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                licensing@mothership-ai.com
              </Link>
            </Box>
            <Button 
              variant="contained" 
              size="large"
              href="https://watcher.mothership-ai.com"
              target="_blank"
              sx={{ mt: 2 }}
            >
              Get Commercial License
            </Button>
          </Box>
        </Paper>

        {/* Footer Notice */}
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>License Version:</strong> 1.0 | 
            <strong> Last Updated:</strong> January 1, 2025 | 
            <strong> This notice must remain intact in all copies and derivative works.</strong>
          </Typography>
        </Alert>
      </motion.div>
    </Container>
  );
}
