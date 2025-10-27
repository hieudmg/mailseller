import { Mail } from 'lucide-react';
import React from 'react';

export default function Icon() {
  return (
    <div className="inline-flex items-center gap-2 text-xl font-black">
      <Mail className="size-8" />
      <span className="gradient-text">{process.env.NEXT_PUBLIC_SITE_NAME}</span>
    </div>
  );
}
