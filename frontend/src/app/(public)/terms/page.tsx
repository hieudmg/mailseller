'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';

export default function TermsOfServicePage() {
  const lastUpdated = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-8">
      <PageHeader title="Terms of Service" subtitle={`Last updated: ${lastUpdated}`} />

      {/* Introduction */}
      <Card>
        <CardHeader>
          <CardTitle>Introduction</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add introduction content here]</p>
        </CardContent>
      </Card>

      {/* Acceptance of Terms */}
      <Card>
        <CardHeader>
          <CardTitle>1. Acceptance of Terms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add acceptance of terms content here]</p>
        </CardContent>
      </Card>

      {/* User Accounts */}
      <Card>
        <CardHeader>
          <CardTitle>2. User Accounts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add user accounts content here]</p>
        </CardContent>
      </Card>

      {/* Services Description */}
      <Card>
        <CardHeader>
          <CardTitle>3. Services Description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add services description content here]</p>
        </CardContent>
      </Card>

      {/* Payment Terms */}
      <Card>
        <CardHeader>
          <CardTitle>4. Payment Terms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add payment terms content here]</p>
        </CardContent>
      </Card>

      {/* Refund Policy */}
      <Card>
        <CardHeader>
          <CardTitle>5. Refund Policy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add refund policy content here]</p>
        </CardContent>
      </Card>

      {/* Acceptable Use */}
      <Card>
        <CardHeader>
          <CardTitle>6. Acceptable Use</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add acceptable use content here]</p>
        </CardContent>
      </Card>

      {/* Prohibited Activities */}
      <Card>
        <CardHeader>
          <CardTitle>7. Prohibited Activities</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add prohibited activities content here]</p>
        </CardContent>
      </Card>

      {/* Intellectual Property */}
      <Card>
        <CardHeader>
          <CardTitle>8. Intellectual Property</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add intellectual property content here]</p>
        </CardContent>
      </Card>

      {/* Disclaimer of Warranties */}
      <Card>
        <CardHeader>
          <CardTitle>9. Disclaimer of Warranties</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add disclaimer of warranties content here]</p>
        </CardContent>
      </Card>

      {/* Limitation of Liability */}
      <Card>
        <CardHeader>
          <CardTitle>10. Limitation of Liability</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add limitation of liability content here]</p>
        </CardContent>
      </Card>

      {/* Termination */}
      <Card>
        <CardHeader>
          <CardTitle>11. Termination</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add termination content here]</p>
        </CardContent>
      </Card>

      {/* Changes to Terms */}
      <Card>
        <CardHeader>
          <CardTitle>12. Changes to Terms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add changes to terms content here]</p>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle>13. Contact Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add contact information content here]</p>
        </CardContent>
      </Card>
    </div>
  );
}
