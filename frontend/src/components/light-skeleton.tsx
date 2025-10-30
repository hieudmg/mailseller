import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export default function LightSkeleton(props: React.ComponentProps<typeof Skeleton>) {
  return <Skeleton {...props} className={cn(props.className, 'opacity-30')} />;
}
