import { KPI } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KpiCardProps {
  kpi: KPI;
  loading?: boolean;
}

export function KpiCard({ kpi, loading }: KpiCardProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border bg-card p-6 animate-pulse shadow-sm">
        <div className="h-4 bg-muted rounded w-24 mb-3" />
        <div className="h-8 bg-muted rounded w-32 mb-2" />
        <div className="h-4 bg-muted rounded w-16" />
      </div>
    );
  }

  const formatValue = (value: number, format: KPI['format']) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('es-ES', {
          style: 'currency',
          currency: 'EUR',
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
    ? 'bg-success/10 text-success'
    : kpi.changeType === 'negative'
      ? 'bg-destructive/10 text-destructive'
      : 'bg-muted text-muted-foreground';

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{kpi.name}</p>
      <p className="mb-3 text-3xl font-semibold tracking-tight text-foreground">
        {formatValue(kpi.value, kpi.format)}
      </p>
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${trendColor}`}>
          <TrendIcon className="h-3.5 w-3.5" />
          <span>{kpi.change > 0 ? '+' : ''}{kpi.change.toFixed(1)}%</span>
        </span>
        <span className="text-xs text-muted-foreground">vs last period</span>
      </div>
    </div>
  );
}