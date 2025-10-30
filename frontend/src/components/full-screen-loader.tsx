import { Spinner } from '@/components/ui/spinner';
import React from 'react';

export default function FullScreenLoader() {
  return (
    <div className="h-screen w-screen">
      <div className="flex h-full w-full items-center justify-center">
        <Spinner className="size-24" />
      </div>
    </div>
  );
}
