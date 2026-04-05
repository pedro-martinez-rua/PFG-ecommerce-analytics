import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getReport } from '@/lib/api';
import { SavedReport, KPI } from '@/lib/types';
import { KpiCard, ChartCard, PageLoading } from '@/components/shared';
import {
  ArrowLeft, Calendar, Sparkles, FileText,
  TrendingUp, Users, Package, Truck,
  Clock, CheckCircle2
} from 'lucide-react';

// ─── Mapeo KPI snapshot → KpiCard ────────────────────────────────────

const KPI_CONFIG: Array<{
  key: string;
  name: string;
  format: KPI['format'];
  invert?: boolean;
}> = [
  { key: 'total_revenue',        name: 'Revenue Total',      format: 'currency' },
  { key: 'order_count',          name: 'Pedidos',            format: 'number' },
  { key: 'avg_order_value',      name: 'Valor Medio Pedido', format: 'currency' },
  { key: 'net_revenue',          name: 'Revenue Neto',       format: 'currency' },
  { key: 'gross_margin_pct',     name: 'Margen Bruto',       format: 'percentage' },
  { key: 'total_discounts',      name: 'Descuentos',         format: 'currency', invert: true },
  { key: 'discount_rate',        name: 'Tasa Descuento',     format: 'percentage', invert: true },
  { key: 'unique_customers',     name: 'Clientes Únicos',    format: 'number' },
  { key: 'repeat_purchase_rate', name: 'Tasa Recompra',      format: 'percentage' },
  { key: 'avg_customer_ltv',     name: 'LTV Medio',          format: 'currency' },
  { key: 'return_rate',          name: 'Tasa Devoluciones',  format: 'percentage', invert: true },
  { key: 'refund_rate',          name: 'Tasa Reembolsos',    format: 'percentage', invert: true },
  { key: 'avg_delivery_days',    name: 'Días Entrega',       format: 'number', invert: true },
  { key: 'delayed_orders_pct',   name: 'Pedidos Retrasados', format: 'percentage', invert: true },
];

function mapKpis(snapshot: Record<string, any>): KPI[] {
  return KPI_CONFIG
    .map(({ key, name, format, invert }) => {
      const d = snapshot[key];
      if (!d || d.availability === 'missing' || d.value === null) return null;
      const change = d.growth_pct ?? 0;
      const positive = invert ? change < 0 : change > 0;
      return {
        id: key, name, format, tenantId: '',
        value: d.value,
        previousValue: d.vs_previous ?? d.value,
        change: Math.abs(change),
        changeType: (change === 0 ? 'neutral' : positive ? 'positive' : 'negative') as KPI['changeType'],
      };
    })
    .filter(Boolean) as KPI[];
}

// ─── Grupos de KPIs ───────────────────────────────────────────────────

const KPI_GROUPS = [
  {
    title: 'Ventas',
    icon: TrendingUp,
    keys: ['total_revenue', 'order_count', 'avg_order_value', 'net_revenue'],
  },
  {
    title: 'Rentabilidad',
    icon: Package,
    keys: ['gross_margin_pct', 'total_discounts', 'discount_rate', 'refund_rate'],
  },
  {
    title: 'Clientes',
    icon: Users,
    keys: ['unique_customers', 'repeat_purchase_rate', 'avg_customer_ltv'],
  },
  {
    title: 'Operación',
    icon: Truck,
    keys: ['return_rate', 'avg_delivery_days', 'delayed_orders_pct'],
  },
];

// ─── Renderizado de markdown simple ──────────────────────────────────

function MarkdownText({ text }: { text: string }) {
  const lines = text.split('\n');

  return (
    <div className="space-y-2">
      {lines.map((line, i) => {
        // Cabecera en negrita: **Texto**
        if (/^\*\*(.+)\*\*$/.test(line.trim())) {
          return (
            <h3 key={i} className="text-base font-semibold text-foreground mt-5 first:mt-0">
              {line.trim().replace(/\*\*/g, '')}
            </h3>
          );
        }

        // Línea vacía
        if (!line.trim()) return <div key={i} className="h-1" />;

        // Ítem de lista numerada o con *
        if (/^\d+\.\s/.test(line) || /^\*\s/.test(line)) {
          const content = line.replace(/^\d+\.\s/, '').replace(/^\*\s/, '');
          const parts = content.split(/(\*\*[^*]+\*\*)/g);
          return (
            <p key={i} className="text-sm text-muted-foreground leading-relaxed pl-4 border-l-2 border-secondary/30">
              {parts.map((part, j) =>
                /^\*\*/.test(part)
                  ? <strong key={j} className="text-foreground font-medium">{part.replace(/\*\*/g, '')}</strong>
                  : part
              )}
            </p>
          );
        }

        // Texto normal con negritas inline
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <p key={i} className="text-sm text-muted-foreground leading-relaxed">
            {parts.map((part, j) =>
              /^\*\*/.test(part)
                ? <strong key={j} className="text-foreground font-medium">{part.replace(/\*\*/g, '')}</strong>
                : part
            )}
          </p>
        );
      })}
    </div>
  );
}

// ─── Página ───────────────────────────────────────────────────────────

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<SavedReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getReport(id)
      .then(setReport)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <PageLoading message="Cargando informe..." />;

  if (!report) return (
    <div className="text-center py-20">
      <p className="text-muted-foreground">Informe no encontrado.</p>
      <Link href="/app/reports">
        <Button variant="ghost" className="mt-4">Volver a informes</Button>
      </Link>
    </div>
  );

  const kpis = report.kpi_snapshot ? mapKpis(report.kpi_snapshot) : [];
  const kpiMap = Object.fromEntries(kpis.map(k => [k.id, k]));

  return (
    <div className="space-y-8 max-w-5xl">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-start gap-3">
        <Link href="/app/reports">
          <Button variant="ghost" size="icon" className="mt-0.5 shrink-0">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-2xl font-bold text-foreground">
              {report.dashboard_name}
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            {report.date_from && report.date_to ? (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {report.date_from} → {report.date_to}
              </span>
            ) : (
              <span>Todos los datos disponibles</span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              Guardado el{' '}
              {new Date(report.created_at).toLocaleDateString('es-ES', {
                day: '2-digit', month: 'long', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
              })}
            </span>
            <span className="flex items-center gap-1 text-success">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Snapshot guardado
            </span>
          </div>
        </div>
      </div>

      {/* ── KPIs agrupados ─────────────────────────────────────── */}
      {kpis.length > 0 && (
        <div className="space-y-6">
          {KPI_GROUPS.map(group => {
            const groupKpis = group.keys
              .map(k => kpiMap[k])
              .filter(Boolean) as KPI[];

            if (groupKpis.length === 0) return null;

            const Icon = group.icon;
            return (
              <div key={group.title}>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                    {group.title}
                  </h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                  {groupKpis.map(kpi => (
                    <KpiCard key={kpi.id} kpi={kpi} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Análisis de IA ─────────────────────────────────────── */}
      {report.insights && (
        <div className="bg-background border rounded-xl overflow-hidden">
          {/* Cabecera */}
          <div className="flex items-center gap-2 px-6 py-4 border-b bg-secondary/5">
            <Sparkles className="h-4 w-4 text-secondary" />
            <h2 className="font-semibold text-foreground">Análisis de IA</h2>
            <span className="ml-auto text-xs text-muted-foreground">
              Generado al guardar el informe
            </span>
          </div>

          {/* Contenido del análisis */}
          <div className="px-6 py-6">
            <MarkdownText text={report.insights} />
          </div>

          {/* Disclaimer */}
          <div className="px-6 py-3 border-t bg-muted/30">
            <p className="text-xs text-muted-foreground">
              Este análisis fue generado automáticamente a partir de métricas agregadas.
              No contiene datos personales de clientes. Contrástalo con tu propio criterio.
            </p>
          </div>
        </div>
      )}

      {/* ── Sin análisis de IA ─────────────────────────────────── */}
      {!report.insights && (
        <div className="bg-muted/30 border border-dashed rounded-xl px-6 py-8 text-center">
          <Sparkles className="h-8 w-8 mx-auto text-muted-foreground mb-2 opacity-50" />
          <p className="text-sm text-muted-foreground">
            Este informe no tiene análisis de IA guardado.
          </p>
        </div>
      )}

      {/* ── Sin KPIs ───────────────────────────────────────────── */}
      {kpis.length === 0 && !report.insights && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Este informe no tiene datos guardados.</p>
        </div>
      )}
    </div>
  );
}