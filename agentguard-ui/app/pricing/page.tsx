'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Switch,
  Alert,
  AlertDescription,
} from '@/components/ui';
import { 
  Check, 
  Star, 
  Zap, 
  Shield, 
  Users, 
  Crown,
  Key,
  TrendingUp,
  Clock,
  Headphones,
  Code,
  Database,
  Globe
} from 'lucide-react';

interface PricingTier {
  id: string;
  name: string;
  price_monthly: number;
  queries_per_month: number;
  agents_limit: number;
  api_access: boolean;
  support_level: string;
  features: string[];
  popular?: boolean;
  enterprise?: boolean;
}

interface PricingData {
  tiers: Record<string, PricingTier>;
  currency: string;
  billing_cycle: string;
  free_trial: {
    available: boolean;
    duration_days: number;
    tier: string;
  };
}

export default function PricingPage() {
  const [pricingData, setPricingData] = useState<PricingData | null>(null);
  const [isAnnual, setIsAnnual] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPricingData();
  }, []);

  const loadPricingData = async () => {
    try {
      // Mock pricing data - in production, fetch from API
      const mockPricingData: PricingData = {
        tiers: {
          free: {
            id: 'free',
            name: 'Free',
            price_monthly: 0,
            queries_per_month: 3,
            agents_limit: 1,
            api_access: false,
            support_level: 'community',
            features: [
              'Basic hallucination detection',
              'Web interface access',
              'Community support',
              '3 queries per month',
              '1 agent limit'
            ]
          },
          pro: {
            id: 'pro',
            name: 'Pro',
            price_monthly: 29,
            queries_per_month: 1000,
            agents_limit: 10,
            api_access: true,
            support_level: 'email',
            features: [
              'Advanced multi-model detection',
              'Agent Console & deployment',
              'API access & webhooks',
              'Real-time monitoring',
              'Email support',
              '1,000 queries per month',
              '10 agents limit'
            ],
            popular: true
          },
          enterprise: {
            id: 'enterprise',
            name: 'Enterprise',
            price_monthly: 299,
            queries_per_month: 50000,
            agents_limit: 100,
            api_access: true,
            support_level: 'priority',
            features: [
              'All Pro features',
              'Custom safety rules',
              'SSO integration',
              'Compliance reporting',
              'Priority support',
              'Custom deployment',
              '50,000 queries per month',
              '100 agents limit'
            ],
            enterprise: true
          },
          byok: {
            id: 'byok',
            name: 'Bring Your Own Key',
            price_monthly: 0,
            queries_per_month: -1,
            agents_limit: -1,
            api_access: true,
            support_level: 'email',
            features: [
              'Use your own API keys',
              'Pay only platform fees ($0.01/query)',
              'Unlimited queries',
              'All Pro features',
              'Cost transparency',
              'No monthly subscription'
            ]
          }
        },
        currency: 'USD',
        billing_cycle: 'monthly',
        free_trial: {
          available: true,
          duration_days: 14,
          tier: 'pro'
        }
      };

      setPricingData(mockPricingData);
    } catch (error) {
      console.error('Failed to load pricing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPrice = (tier: PricingTier) => {
    if (tier.price_monthly === 0) return 'Free';
    
    const price = isAnnual ? tier.price_monthly * 10 : tier.price_monthly; // 2 months free annually
    return `$${price}`;
  };

  const getPriceSubtext = (tier: PricingTier) => {
    if (tier.id === 'byok') return 'Platform fee only';
    if (tier.price_monthly === 0) return 'Forever';
    return isAnnual ? '/year' : '/month';
  };

  const formatNumber = (num: number) => {
    if (num === -1) return 'Unlimited';
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toString();
  };

  const getSupportIcon = (level: string) => {
    switch (level) {
      case 'community': return <Users className="h-4 w-4" />;
      case 'email': return <Headphones className="h-4 w-4" />;
      case 'priority': return <Crown className="h-4 w-4" />;
      default: return <Users className="h-4 w-4" />;
    }
  };

  const handleSubscribe = async (tierId: string) => {
    try {
      // In production, create Stripe checkout session
      console.log(`Subscribing to ${tierId}`);
      
      if (tierId === 'free') {
        // Redirect to signup
        window.location.href = '/auth/register';
        return;
      }

      if (tierId === 'byok') {
        // Redirect to BYOK setup
        window.location.href = '/settings/byok';
        return;
      }

      // Mock Stripe checkout
      const checkoutUrl = `https://checkout.stripe.com/pay/demo_${tierId}`;
      window.location.href = checkoutUrl;
      
    } catch (error) {
      console.error('Subscription error:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!pricingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert>
          <AlertDescription>Failed to load pricing information</AlertDescription>
        </Alert>
      </div>
    );
  }

  const tiers = Object.values(pricingData.tiers);

  return (
    <div className="container mx-auto px-4 py-12 max-w-7xl">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Start free, scale as you grow. Enterprise-grade AI safety for every team.
        </p>
        
        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <span className={`text-sm ${!isAnnual ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
            Monthly
          </span>
          <Switch
            checked={isAnnual}
            onCheckedChange={setIsAnnual}
          />
          <span className={`text-sm ${isAnnual ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
            Annual
          </span>
          {isAnnual && (
            <Badge className="bg-green-100 text-green-800 ml-2">
              Save 20%
            </Badge>
          )}
        </div>

        {/* Free Trial Banner */}
        {pricingData.free_trial.available && (
          <Alert className="max-w-md mx-auto mb-8">
            <Star className="h-4 w-4" />
            <AlertDescription>
              Start with a {pricingData.free_trial.duration_days}-day free trial of Pro features
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
        {tiers.map((tier) => (
          <Card 
            key={tier.id} 
            className={`relative ${
              tier.popular 
                ? 'border-blue-500 shadow-lg scale-105' 
                : tier.enterprise 
                ? 'border-purple-500' 
                : 'border-gray-200'
            }`}
          >
            {tier.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-blue-500 text-white px-3 py-1">
                  Most Popular
                </Badge>
              </div>
            )}
            
            {tier.enterprise && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-purple-500 text-white px-3 py-1">
                  Enterprise
                </Badge>
              </div>
            )}

            <CardHeader className="text-center pb-4">
              <div className="mb-4">
                {tier.id === 'free' && <Zap className="h-8 w-8 text-gray-600 mx-auto" />}
                {tier.id === 'pro' && <TrendingUp className="h-8 w-8 text-blue-600 mx-auto" />}
                {tier.id === 'enterprise' && <Crown className="h-8 w-8 text-purple-600 mx-auto" />}
                {tier.id === 'byok' && <Key className="h-8 w-8 text-green-600 mx-auto" />}
              </div>
              
              <CardTitle className="text-xl font-bold">{tier.name}</CardTitle>
              
              <div className="mt-4">
                <span className="text-4xl font-bold text-gray-900">
                  {getPrice(tier)}
                </span>
                <span className="text-gray-600 ml-1">
                  {getPriceSubtext(tier)}
                </span>
              </div>

              {tier.id === 'byok' && (
                <p className="text-sm text-gray-600 mt-2">
                  $0.01 per query + your API costs
                </p>
              )}
            </CardHeader>

            <CardContent className="pt-0">
              {/* Key Metrics */}
              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Queries/month</span>
                  <span className="font-medium">{formatNumber(tier.queries_per_month)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Agents</span>
                  <span className="font-medium">{formatNumber(tier.agents_limit)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">API Access</span>
                  <span className="font-medium">
                    {tier.api_access ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Support</span>
                  <div className="flex items-center gap-1">
                    {getSupportIcon(tier.support_level)}
                    <span className="font-medium capitalize">{tier.support_level}</span>
                  </div>
                </div>
              </div>

              {/* Features */}
              <div className="space-y-2 mb-6">
                {tier.features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>

              {/* CTA Button */}
              <Button
                onClick={() => handleSubscribe(tier.id)}
                className={`w-full ${
                  tier.popular 
                    ? 'bg-blue-600 hover:bg-blue-700' 
                    : tier.enterprise
                    ? 'bg-purple-600 hover:bg-purple-700'
                    : tier.id === 'byok'
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-gray-600 hover:bg-gray-700'
                }`}
              >
                {tier.id === 'free' ? 'Get Started Free' : 
                 tier.id === 'byok' ? 'Setup BYOK' :
                 tier.id === 'enterprise' ? 'Contact Sales' :
                 'Start Free Trial'}
              </Button>

              {tier.id === 'pro' && pricingData.free_trial.available && (
                <p className="text-xs text-gray-500 text-center mt-2">
                  {pricingData.free_trial.duration_days} days free, then ${tier.price_monthly}/month
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Feature Comparison */}
      <div className="mb-16">
        <h2 className="text-2xl font-bold text-center mb-8">Feature Comparison</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="border border-gray-200 px-4 py-3 text-left">Feature</th>
                {tiers.map((tier) => (
                  <th key={tier.id} className="border border-gray-200 px-4 py-3 text-center">
                    {tier.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { name: 'Hallucination Detection', free: true, pro: true, enterprise: true, byok: true },
                { name: 'Web Interface', free: true, pro: true, enterprise: true, byok: true },
                { name: 'Agent Console', free: false, pro: true, enterprise: true, byok: true },
                { name: 'API Access', free: false, pro: true, enterprise: true, byok: true },
                { name: 'Real-time Monitoring', free: false, pro: true, enterprise: true, byok: true },
                { name: 'Webhooks', free: false, pro: true, enterprise: true, byok: true },
                { name: 'Custom Safety Rules', free: false, pro: false, enterprise: true, byok: false },
                { name: 'SSO Integration', free: false, pro: false, enterprise: true, byok: false },
                { name: 'Compliance Reporting', free: false, pro: false, enterprise: true, byok: false },
                { name: 'Priority Support', free: false, pro: false, enterprise: true, byok: false },
              ].map((feature, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="border border-gray-200 px-4 py-3 font-medium">
                    {feature.name}
                  </td>
                  {tiers.map((tier) => (
                    <td key={tier.id} className="border border-gray-200 px-4 py-3 text-center">
                      {feature[tier.id as keyof typeof feature] ? (
                        <Check className="h-5 w-5 text-green-600 mx-auto" />
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="mb-16">
        <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {[
            {
              question: "What happens when I exceed my query limit?",
              answer: "Free users will be prompted to upgrade. Paid users can purchase additional queries or upgrade to a higher tier."
            },
            {
              question: "How does BYOK (Bring Your Own Key) work?",
              answer: "You provide your own API keys for Claude, GPT-4, etc. You pay us a small platform fee ($0.01/query) plus your actual API costs."
            },
            {
              question: "Can I change plans anytime?",
              answer: "Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately."
            },
            {
              question: "What's included in the free trial?",
              answer: "14 days of full Pro features including unlimited queries, agent console, and API access."
            },
            {
              question: "Do you offer enterprise discounts?",
              answer: "Yes, we offer volume discounts and custom pricing for large enterprises. Contact our sales team."
            },
            {
              question: "How accurate is the hallucination detection?",
              answer: "Our advanced ensemble model achieves 99%+ accuracy using multiple AI models and statistical validation."
            }
          ].map((faq, index) => (
            <div key={index} className="space-y-2">
              <h3 className="font-medium text-gray-900">{faq.question}</h3>
              <p className="text-gray-600 text-sm">{faq.answer}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="text-center bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">Ready to secure your AI agents?</h2>
        <p className="text-lg mb-6 opacity-90">
          Join thousands of developers building safer AI with AgentGuard
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button 
            onClick={() => handleSubscribe('free')}
            className="bg-white text-blue-600 hover:bg-gray-100"
          >
            Start Free
          </Button>
          <Button 
            onClick={() => handleSubscribe('pro')}
            className="bg-blue-700 hover:bg-blue-800 border border-blue-500"
          >
            Try Pro Free
          </Button>
        </div>
      </div>
    </div>
  );
}
