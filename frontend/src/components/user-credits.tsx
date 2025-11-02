import { useCredits } from '@/context/CreditsContext';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import LightSkeleton from '@/components/light-skeleton';
import { formatAmount } from '@/lib/utils';

export default function UserCredits() {
  const { credits, tierData } = useCredits();

  return (
    <div>
      {tierData?.tier_code && (
        <div className="text-muted-foreground flex items-center gap-2 text-sm">
          <Image
            title={tierData.tier_name}
            src={`/ranks/${tierData.tier_code}.png`}
            alt={tierData.tier_code}
            width={32}
            height={32}
          />
          <div>
            <div className="text-primary">{formatAmount(credits)}</div>
            <Badge>
              <span>{tierData.final_discount * 100}% off</span>
            </Badge>
          </div>
        </div>
      )}
      {!!tierData?.tier_code || (
        <div className="text-muted-foreground flex items-center gap-2 text-sm">
          <LightSkeleton className="h-8 w-8 rounded-[50%]" />
          <div>
            <LightSkeleton className="mb-2 h-2 w-20" />
            <LightSkeleton className="h-2 w-12" />
          </div>
        </div>
      )}
    </div>
  );
}
