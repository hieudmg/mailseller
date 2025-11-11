'use client';

import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { TelegramLink } from '@/components/telegram-link';

export default function PrivacyPolicyPage() {
  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-8">
      <PageHeader title="Privacy Policy" subtitle={`Last updated: 01/06/2025`} />

      <Card>
        <CardContent className="text-muted-foreground space-y-4">
          We agree not to keep any records on any activity other than that which is required. What we store includes:
          <ol className="mt-2 list-inside list-decimal pl-4">
            <li>Your e-mail address</li>
            <li>Your encrypted password</li>
            <li>Your current balance</li>
            <li>Account refill history and payment details</li>
            <li>Purchase history (24h)</li>
          </ol>
          <br />
          Customers have the option to delete their account by contacting us via Telegram <TelegramLink />.
          <br />
          Removal will be performed not earlier than 48h after the request is made.
          <br />
          If you have any questions of concerns about any of this, then feel free to contact us via Telegram{' '}
          <TelegramLink />, and a support agent will get back to you as soon as possible.
        </CardContent>
      </Card>
    </div>
  );
}
