import { BarChart3 } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  BarChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { ChartPoint } from '@/lib/types';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  loading?: boolean;
  data?: ChartPoint[];
  type?: 'area' | 'bar';
  valuePrefix?: string;
}

const formatValue = (value: number, prefix = '') => {
  if (value >= 1_000_000) return `${prefix}${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000)     return `${prefix}${(value / 1_000).toFixed(1)}k`;
  return `${prefix}${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })}`;
};

const CustomTooltip = ({ active, payload, label, prefix }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-background border rounded-lg shadow-lg px-3 py-2 text-sm">
      <p className="text-muted-foreground mb-1">{label}</p>
      <p className="font-semibold text-foreground">
        {prefix}{payload[0].value.toLocaleString('es-ES', { maximumFractionDigits: 2 })}
      </p>
    </div>
  );
};

export function ChartCard({
  title,
  subtitle,
  loading,
  data = [],
  type = 'area',
  valuePrefix = '',
}: ChartCardProps) {
  if (loading) {
    return (
      <div className="bg-background rounded-lg border p-6 animate-pulse">
        <div className="h-5 bg-muted rounded w-32 mb-2" />
        <div className="h-4 bg-muted rounded w-48 mb-6" />
        <div className="h-48 bg-muted rounded" />
      </div>
    );
  }

  const hasData = data && data.length > 0;

  return (
    <div className="bg-background rounded-lg border p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
      </div>

      {!hasData ? (
        <div className="h-48 bg-muted/50 rounded-lg flex items-center justify-center border border-dashed">
          <div className="text-center text-muted-foreground">
            <BarChart3 className="h-10 w-10 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Sin datos disponibles</p>
          </div>
        </div>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            {type === 'area' ? (
              <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="hsl(var(--secondary))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--secondary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => formatValue(v, valuePrefix)}
                  width={50}
                />
                <Tooltip content={<CustomTooltip prefix={valuePrefix} />} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="hsl(var(--secondary))"
                  strokeWidth={2}
                  fill="url(#colorValue)"
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </AreaChart>
            ) : (
              <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => formatValue(v, valuePrefix)}
                  width={50}
                />
                <Tooltip content={<CustomTooltip prefix={valuePrefix} />} />
                <Bar
                  dataKey="value"
                  fill="hsl(var(--secondary))"
                  radius={[4, 4, 0, 0]}
                  opacity={0.85}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}