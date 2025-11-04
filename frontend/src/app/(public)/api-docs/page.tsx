'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import CodeBlock from '@/components/api/code-block';
import ApiEndpoint from '@/components/api/api-endpoint';

export default function ApiDocsPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.example.com';

  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-8">
      <PageHeader
        title="API Documentation"
        subtitle="Integrate our services into your application using our RESTful API"
      />

      {/* Authentication Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Badge variant="outline">Authentication</Badge>
          </CardTitle>
          <CardDescription>
            All API requests require authentication using your API token as a URL parameter
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="mb-2 font-semibold">Getting Your API Token</h4>
            <p className="text-muted-foreground mb-2 text-sm">
              After logging in, navigate to your dashboard settings to retrieve your API token. Include this token as a
              <code className="mx-1 rounded bg-slate-800 px-2 py-1 text-purple-400">token</code>
              parameter in your API requests.
            </p>
            <CodeBlock id="auth-param" code={`?token=YOUR_API_TOKEN_HERE`} />
          </div>
        </CardContent>
      </Card>

      {/* Base URL */}
      <Card>
        <CardHeader>
          <CardTitle>Base URL</CardTitle>
        </CardHeader>
        <CardContent>
          <CodeBlock id="base-url" code={apiUrl} />
        </CardContent>
      </Card>

      {/* GET /api/credits */}
      <ApiEndpoint
        method="GET"
        path="/api/credits"
        description="Get your current credit balance"
        queryParams={[{ name: 'token', required: true, description: 'Your API token' }]}
        requestExample={`curl -X GET "${apiUrl}/api/credits?token=YOUR_API_TOKEN"`}
        response={{
          credits: 123.45,
        }}
      />

      {/* GET /api/purchase */}
      <ApiEndpoint
        method="GET"
        path="/api/purchase"
        description="Purchase data items using your credits"
        queryParams={[
          { name: 'amount', required: true, description: 'Number of items to purchase (1-100)' },
          {
            name: 'type',
            required: true,
            description: 'Data type (e.g., "short_gmail", "short_hotmail", "long_gmail")',
          },
          { name: 'token', required: true, description: 'Your API token' },
        ]}
        requestExample={`curl -X GET "${apiUrl}/api/purchase?amount=10&type=short_gmail&token=YOUR_API_TOKEN"`}
        response={{
          status: 'success',
          data: ['email1@gmail.com', 'email2@gmail.com', 'email3@gmail.com'],
          type: 'short_gmail',
          cost: 0.025,
          credit_remaining: 123.425,
        }}
        errors={[
          {
            code: 400,
            description: 'Bad Request - Invalid parameters',
            example: {
              detail: 'Amount must be positive',
            },
          },
          {
            code: 402,
            description: 'Payment Required - Insufficient credits',
            example: {
              detail: 'Insufficient credits. You have 5.00 credits.',
            },
          },
          {
            code: 404,
            description: 'Not Found - No data available',
            example: {
              detail: "No data available in pool for type 'short_gmail'",
            },
          },
        ]}
      />

      {/* GET /api/datapool/size */}
      <ApiEndpoint
        method="GET"
        path="/api/datapool/size"
        description="Get current pool sizes and pricing for all data types"
        requiresAuth={false}
        requestExample={`curl -X GET "${apiUrl}/api/datapool/size"`}
        response={{
          total: 0,
          sizes: {
            short_gmail: {
              pool_size: 1234,
              price: 0.0025,
              name: 'Gmail Short',
              lifetime: 'short',
            },
            short_hotmail: {
              pool_size: 567,
              price: 0.0015,
              name: 'Hotmail Short',
              lifetime: 'short',
            },
            long_gmail: {
              pool_size: 89,
              price: 0.05,
              name: 'Gmail Long',
              lifetime: 'long',
            },
          },
        }}
        notes={[
          'Response is cached for 1 second to improve performance',
          'Pool sizes update in real-time as purchases are made',
          'Prices shown are base prices before any tier discounts',
        ]}
      />

      {/* GET /api/tier */}
      <ApiEndpoint
        method="GET"
        path="/api/tier"
        description="Get your current discount tier and progress information"
        queryParams={[{ name: 'token', required: true, description: 'Your API token' }]}
        requestExample={`curl -X GET "${apiUrl}/api/tier?token=YOUR_API_TOKEN"`}
        response={{
          tier_code: 'bronze',
          tier_name: 'Bronze',
          tier_discount: 0.05,
          deposit_amount: 175.5,
          next_tier: {
            tier_code: 'silver',
            tier_name: 'Silver',
            tier_discount: 0.1,
            required_deposit: 400.0,
            remaining: 224.5,
          },
          custom_discount: null,
          final_discount: 0.05,
          discount_source: 'tier',
          credits: 123.45,
        }}
        responseFields={[
          { name: 'tier_code', description: 'Current tier code (iron, bronze, silver, gold, diamond)' },
          { name: 'tier_discount', description: 'Discount percentage from tier (0.05 = 5%)' },
          { name: 'deposit_amount', description: 'Total deposits in last 7 days' },
          { name: 'custom_discount', description: 'Admin-set discount (overrides tier discount if not null)' },
          { name: 'final_discount', description: 'The actual discount applied to purchases' },
          { name: 'next_tier', description: 'Information about the next tier (null if at max tier)' },
        ]}
      />

      {/* Discount Tiers Card */}
      <Card>
        <CardHeader>
          <CardTitle>Discount Tiers</CardTitle>
          <CardDescription>Deposit more in the next 7 days to unlock better discounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between rounded border border-slate-700 bg-slate-800/50 p-2">
              <span>Iron: $50+ in 7 days</span>
              <span className="font-semibold">0% discount</span>
            </div>
            <div className="flex justify-between rounded border border-slate-700 bg-slate-800/50 p-2">
              <span>Bronze: $150+ in 7 days</span>
              <span className="font-semibold">5% discount</span>
            </div>
            <div className="flex justify-between rounded border border-slate-700 bg-slate-800/50 p-2">
              <span>Silver: $400+ in 7 days</span>
              <span className="font-semibold">10% discount</span>
            </div>
            <div className="flex justify-between rounded border border-slate-700 bg-slate-800/50 p-2">
              <span>Gold: $1,000+ in 7 days</span>
              <span className="font-semibold">15% discount</span>
            </div>
            <div className="flex justify-between rounded border border-slate-700 bg-slate-800/50 p-2">
              <span>Diamond: $2,500+ in 7 days</span>
              <span className="font-semibold">20% discount</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rate Limits & Best Practices */}
      <Card>
        <CardHeader>
          <CardTitle>Best Practices</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="text-muted-foreground list-inside list-disc space-y-2">
            <li>Keep your API token secure and never share it publicly</li>
            <li>The maximum purchase amount per request is 100 items</li>
            <li>Pool sizes are cached for 1 second, so they may not reflect real-time availability</li>
            <li>Handle 402 errors (insufficient credits) gracefully by checking balance first</li>
            <li>Handle 404 errors (no data available) by retrying later or choosing a different type</li>
            <li>Tier discounts are calculated based on deposits made in the last 7 days</li>
            <li>Custom discounts set by admins override tier discounts</li>
          </ul>
        </CardContent>
      </Card>

      {/* Support */}
      <Card>
        <CardHeader>
          <CardTitle>Need Help?</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            If you have questions or need assistance with the API, please contact our support team through your
            dashboard.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
