import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'text' | 'card' | 'avatar' | 'button';
}

export function LoadingSkeleton({ className, variant = 'text' }: LoadingSkeletonProps) {
  const baseClasses = 'animate-pulse bg-muted rounded';
  
  const variants = {
    text: 'h-4 w-full',
    card: 'h-32 w-full',
    avatar: 'h-10 w-10 rounded-full',
    button: 'h-10 w-24',
  };

  return <div className={cn(baseClasses, variants[variant], className)} />;
}

interface PageLoadingProps {
  message?: string;
}

export function PageLoading({ message = 'Loading...' }: PageLoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="h-8 w-8 border-2 border-secondary border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
