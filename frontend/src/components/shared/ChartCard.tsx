import { BarChart3 } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  BarChart,
  LineChart,
  Area,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { ChartPoint } from '@/lib/types';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  loading?: boolean;
  data?: ChartPoint[] | any[];
  type?: 'area' | 'bar' | 'multiline' | 'donut';
  valuePrefix?: string;
  /** Para multiline: clave que agrupa las series (ej. "year" o "channel") */
  seriesKey?: string;
  /** Para multiline: clave del eje X (ej. "period_label") */
  xKey?: string;
  /** Para multiline: clave del valor (ej. "revenue") */
  valueKey?: string;
}

const COLORS = [
  'hsl(var(--secondary))',
  '#6366f1',
  '#f59e0b',
  '#10b981',
  '#ef4444',
  '#8b5cf6',
  '#14b8a6',
];

const formatValue = (value: number, prefix = '') => {
  if (value >= 1_000_000) return `${prefix}${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000)     return `${prefix}${(value / 1_000).toFixed(1)}k`;
  return `${prefix}${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })}`;
};

const CustomTooltip = ({ active, payload, label, prefix }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border bg-popover/95 px-3 py-2 text-sm shadow-md backdrop-blur min-w-[120px]">
      <p className="text-muted-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="font-semibold" style={{ color: entry.color }}>
          {entry.name}: {prefix}{entry.value?.toLocaleString('es-ES', { maximumFractionDigits: 2 })}
        </p>
      ))}
    </div>
  );
};

/** Transforma [{year, period_label, revenue}, ...] en [{period_label, 2023: x, 2024: y}, ...] */
function pivotMultiline(
  data: any[],
  seriesKey: string,
  xKey: string,
  valueKey: string,
): { pivoted: any[]; series: string[] } {
  const seriesSet = Array.from(new Set(data.map(d => String(d[seriesKey])))).sort();
  const xValues   = Array.from(new Set(data.map(d => String(d[xKey])))).sort(
    (a, b) => {
      const da = data.find(d => String(d[xKey]) === a);
      const db = data.find(d => String(d[xKey]) === b);
      return (da?.period ?? 0) - (db?.period ?? 0);
    }
  );

  const pivoted = xValues.map(x => {
    const row: any = { [xKey]: x };
    seriesSet.forEach(s => {
      const match = data.find(d => String(d[xKey]) === x && String(d[seriesKey]) === s);
      row[s] = match ? match[valueKey] : null;
    });
    return row;
  });

  return { pivoted, series: seriesSet };
}

export function ChartCard({
  title,
  subtitle,
  loading,
  data = [],
  type = 'area',
  valuePrefix = '',
  seriesKey = 'year',
  xKey = 'period_label',
  valueKey = 'revenue',
}: ChartCardProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border bg-card p-6 animate-pulse shadow-sm">
        <div className="h-5 bg-muted rounded w-32 mb-2" />
        <div className="h-4 bg-muted rounded w-48 mb-6" />
        <div className="h-48 bg-muted rounded" />
      </div>
    );
  }

  const hasData = data && data.length > 0;

  const renderChart = () => {
    if (!hasData) return null;

    if (type === 'multiline') {
      const { pivoted, series } = pivotMultiline(data, seriesKey, xKey, valueKey);
      return (
        <LineChart data={pivoted} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            dataKey={xKey}
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
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            iconType="circle"
            iconSize={8}
          />
          {series.map((s, i) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              name={s}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
            />
          ))}
        </LineChart>
      );
    }

    if (type === 'donut') {
      const donutData = (data as ChartPoint[]).map(d => ({ name: d.label, value: d.value }));
      return (
        <PieChart>
          <Pie
            data={donutData}
            cx="50%"
            cy="50%"
            innerRadius={52}
            outerRadius={76}
            paddingAngle={3}
            dataKey="value"
          >
            {donutData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} opacity={0.85} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) =>
              `${valuePrefix}${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })}`
            }
          />
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            iconType="circle"
            iconSize={8}
          />
        </PieChart>
      );
    }

    if (type === 'bar') {
      return (
        <BarChart data={data as ChartPoint[]} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
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
          <Bar dataKey="value" fill="hsl(var(--secondary))" radius={[6, 6, 0, 0]} opacity={0.72} />
        </BarChart>
      );
    }

    // area (default)
    return (
      <AreaChart data={data as ChartPoint[]} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="hsl(var(--secondary))" stopOpacity={0.18} />
            <stop offset="95%" stopColor="hsl(var(--secondary))" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
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
    );
  };

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
      </div>

      {!hasData ? (
        <div className="flex h-48 items-center justify-center rounded-xl border border-dashed bg-muted/40">
          <div className="text-center text-muted-foreground">
            <BarChart3 className="h-10 w-10 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Sin datos disponibles</p>
          </div>
        </div>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()!}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}