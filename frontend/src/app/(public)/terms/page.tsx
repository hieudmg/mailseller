'use client';

import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';
import { TelegramLink } from '@/components/telegram-link';

export default function TermsOfServicePage() {
  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-8">
      <PageHeader title="Terms of Service" subtitle={`Last updated: 01/06/2025`} />
      <Card>
        <CardContent className="text-muted-foreground">
          <p className="text-left whitespace-pre-wrap">
            1. Introduction
            <br />
            Welcome to {process.env.NEXT_PUBLIC_SITE_NAME}. By using our website and purchasing our email accounts, you
            agree to be bound by these Terms of Service.
            <br />
            <br />
            2. Use of Our Services
            <br />
            Our services include the sale of email accounts for personal or business use. Users must comply with all
            applicable laws and regulations, including those pertaining to privacy and electronic communications.
            <br />
            <br />
            3. Anti-Spam Policy
            <br />
            {process.env.NEXT_PUBLIC_SITE_NAME} maintains a strict anti-spam policy. Customers are prohibited from using
            purchased email accounts for sending unsolicited commercial emails or spam. Users must ensure their use of
            email accounts adheres to all applicable anti-spam laws, including but not limited to the CAN-SPAM Act.
            Violations of this policy may result in immediate termination of your account and potential legal action.
            <br />
            <br />
            4. Refund Policy
            <br />
            We offer refunds under the following conditions: If the email account provided does not work as declared. If
            there is a technical issue with the account that we cannot resolve. Refund requests must be made within 24h
            of the purchase. Refunds are processed within 7 days after the request has been confirmed and approved.
            <br />
            <br />
            5. Accounts Security
            <br />
            Privacy of Activity: {process.env.NEXT_PUBLIC_SITE_NAME} respects the privacy of its users. We do not
            monitor the activities or content within the email accounts. Responsibility for content and activity within
            each account rests solely with the account holder. Security Obligations: Customers are responsible for
            maintaining the confidentiality and security of their account information, including passwords. It is
            advised that users take all necessary measures to secure their accounts, such as using strong passwords and
            regularly updating them. Liability for Misuse: {process.env.NEXT_PUBLIC_SITE_NAME} is not liable for any
            loss or damage arising from unauthorized use of your account, failure to comply with security obligations,
            or any activities that take place within your account. We encourage users to report any unauthorized use of
            their accounts as soon as it is noticed. Compliance with Laws: While we do not monitor accounts activities,
            users are expected to use their accounts lawfully and in compliance with all applicable laws and
            regulations. Illegal use of accounts may result in termination of the service and legal action, if
            necessary.
            <br />
            <br />
            6. Interaction with Authorities
            <br />
            Compliance with Laws: {process.env.NEXT_PUBLIC_SITE_NAME} operates in full compliance with the applicable
            laws and regulations. We are committed to cooperating with law enforcement authorities and regulatory bodies
            as required by law. Law Enforcement Requests: In cases where we receive a valid legal request from a law
            enforcement or government agency, we may disclose necessary information pertaining to an account. This
            includes, but is not limited to, situations involving investigations of criminal activities, national
            security, or when legally mandated. Notification to Users: Unless prohibited by law or court order, we aim
            to notify our users before disclosing their personal information in response to legal requests. This is to
            ensure transparency and to give users the opportunity to challenge such requests where possible. Protection
            of Rights and Safety: We reserve the right to disclose any information about our users to law enforcement or
            other government officials as we, in our sole discretion, believe necessary or appropriate to respond to
            claims and legal process, to protect the property and rights of {process.env.NEXT_PUBLIC_SITE_NAME} or a
            third party, to protect the safety of the public or any person, or to prevent or stop activity we consider
            to be illegal or unethical. Court Orders: In the event of receiving court order, or other legal process,
            {process.env.NEXT_PUBLIC_SITE_NAME} policy is to respond in accordance with applicable law. Our response may
            include submitting user data as instructed by the legal order. Contacting Us for Legal Matters: For any
            legal inquiries or to respond to legal processes, please contact us via Telegram <TelegramLink />.
            <br />
            <br />
            7. Limitation of Liability
            <br />
            {process.env.NEXT_PUBLIC_SITE_NAME} will not be liable for any indirect, incidental, special, consequential,
            or punitive damages arising from the use of our services.
            <br />
            <br />
            8. Amendments to the Terms of Service
            <br />
            We reserve the right to modify these terms at any time. Continued use of the site after changes constitutes
            acceptance of the new Terms of Service.
            <br />
            10. Contact Information For any questions about these Terms of Service, please contact us via Telegram{' '}
            <TelegramLink />.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
