import { KPI } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KpiCardProps {
  kpi: KPI;
  loading?: boolean;
}

export function KpiCard({ kpi, loading }: KpiCardProps) {
  if (loading) {
    return (
      <div className="bg-background rounded-lg border p-6 animate-pulse">
        <div className="h-4 bg-muted rounded w-24 mb-3" />
        <div className="h-8 bg-muted rounded w-32 mb-2" />
        <div className="h-4 bg-muted rounded w-16" />
      </div>
    );
  }

  const formatValue = (value: number, format: KPI['format']) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 2,
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'number':
      default:
        return new Intl.NumberFormat('en-US').format(value);
    }
  };

  const TrendIcon = kpi.changeType === 'positive' 
    ? TrendingUp 
    : kpi.changeType === 'negative' 
      ? TrendingDown 
      : Minus;

  const trendColor = kpi.changeType === 'positive'
    ? 'text-success'
    : kpi.changeType === 'negative'
      ? 'text-destructive'
      : 'text-muted-foreground';

  return (
    <div className="bg-background rounded-lg border p-6 transition-shadow hover:shadow-card">
      <p className="text-sm font-medium text-muted-foreground mb-1">{kpi.name}</p>
      <p className="text-2xl font-semibold text-foreground mb-2">
        {formatValue(kpi.value, kpi.format)}
      </p>
      <div className={`flex items-center gap-1 text-sm ${trendColor}`}>
        <TrendIcon className="h-4 w-4" />
        <span>{kpi.change > 0 ? '+' : ''}{kpi.change.toFixed(1)}%</span>
        <span className="text-muted-foreground">vs last period</span>
      </div>
    </div>
  );
}
