import { Suspense } from 'react';
import { LoginForm } from '@/components/login-form';

function LoginFormWrapper() {
  return <LoginForm />;
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center p-8">Loading...</div>}>
      <LoginFormWrapper />
    </Suspense>
  );
}
