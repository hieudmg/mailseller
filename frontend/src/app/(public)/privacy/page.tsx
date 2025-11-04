'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';

export default function PrivacyPolicyPage() {
  const lastUpdated = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-8">
      <PageHeader title="Privacy Policy" subtitle={`Last updated: ${lastUpdated}`} />

      {/* Introduction */}
      <Card>
        <CardHeader>
          <CardTitle>Introduction</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add introduction content here]</p>
        </CardContent>
      </Card>

      {/* Information We Collect */}
      <Card>
        <CardHeader>
          <CardTitle>1. Information We Collect</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <h4 className="font-semibold text-foreground">1.1 Personal Information</h4>
          <p>[Add personal information content here]</p>

          <h4 className="mt-4 font-semibold text-foreground">1.2 Usage Data</h4>
          <p>[Add usage data content here]</p>

          <h4 className="mt-4 font-semibold text-foreground">1.3 Payment Information</h4>
          <p>[Add payment information content here]</p>
        </CardContent>
      </Card>

      {/* How We Use Your Information */}
      <Card>
        <CardHeader>
          <CardTitle>2. How We Use Your Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add how we use your information content here]</p>
        </CardContent>
      </Card>

      {/* Information Sharing and Disclosure */}
      <Card>
        <CardHeader>
          <CardTitle>3. Information Sharing and Disclosure</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add information sharing and disclosure content here]</p>
        </CardContent>
      </Card>

      {/* Data Security */}
      <Card>
        <CardHeader>
          <CardTitle>4. Data Security</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add data security content here]</p>
        </CardContent>
      </Card>

      {/* Data Retention */}
      <Card>
        <CardHeader>
          <CardTitle>5. Data Retention</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add data retention content here]</p>
        </CardContent>
      </Card>

      {/* Your Rights */}
      <Card>
        <CardHeader>
          <CardTitle>6. Your Rights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <h4 className="font-semibold text-foreground">6.1 Access and Correction</h4>
          <p>[Add access and correction content here]</p>

          <h4 className="mt-4 font-semibold text-foreground">6.2 Data Deletion</h4>
          <p>[Add data deletion content here]</p>

          <h4 className="mt-4 font-semibold text-foreground">6.3 Data Portability</h4>
          <p>[Add data portability content here]</p>

          <h4 className="mt-4 font-semibold text-foreground">6.4 Opt-Out</h4>
          <p>[Add opt-out content here]</p>
        </CardContent>
      </Card>

      {/* Cookies and Tracking Technologies */}
      <Card>
        <CardHeader>
          <CardTitle>7. Cookies and Tracking Technologies</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add cookies and tracking technologies content here]</p>
        </CardContent>
      </Card>

      {/* Third-Party Services */}
      <Card>
        <CardHeader>
          <CardTitle>8. Third-Party Services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add third-party services content here]</p>
        </CardContent>
      </Card>

      {/* International Data Transfers */}
      <Card>
        <CardHeader>
          <CardTitle>9. International Data Transfers</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add international data transfers content here]</p>
        </CardContent>
      </Card>

      {/* Children's Privacy */}
      <Card>
        <CardHeader>
          <CardTitle>10. Children&apos;s Privacy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add children's privacy content here]</p>
        </CardContent>
      </Card>

      {/* Changes to Privacy Policy */}
      <Card>
        <CardHeader>
          <CardTitle>11. Changes to This Privacy Policy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add changes to privacy policy content here]</p>
        </CardContent>
      </Card>

      {/* GDPR Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>12. GDPR Compliance (EU Users)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add GDPR compliance content here]</p>
        </CardContent>
      </Card>

      {/* CCPA Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>13. CCPA Compliance (California Residents)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add CCPA compliance content here]</p>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle>14. Contact Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>[Add contact information content here]</p>
        </CardContent>
      </Card>
    </div>
  );
}
