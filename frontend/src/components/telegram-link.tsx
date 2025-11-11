import { ComponentProps } from 'react';
import Link from 'next/link';
import { ExternalLinkIcon } from 'lucide-react';

export function TelegramLink({ children, ...props }: ComponentProps<'a'>) {
  return (
    <Link
      href={`https://t.me/${process.env.NEXT_PUBLIC_TELEGRAM_ACCOUNT}`}
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      <span className="inline-flex items-center gap-2 whitespace-nowrap">
        {children || '@' + process.env.NEXT_PUBLIC_TELEGRAM_ACCOUNT} <ExternalLinkIcon size={14} />
      </span>
    </Link>
  );
}
