import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getImports, getKpiResponse, getInsightsText } from '@/lib/api';
import { BackendKpiResponse, BackendImport, KPI } from '@/lib/types';
import { KpiCard, ChartCard, PageLoading, AiInsightsPanel } from '@/components/shared';
import { ArrowLeft, Sparkles, Calendar, FileText } from 'lucide-react';

function mapKpis(response: BackendKpiResponse): KPI[] {
  const entries = [
    { key: 'total_revenue',        name: 'Revenue Total',      format: 'currency' as const },
    { key: 'order_count',          name: 'Pedidos',            format: 'number' as const },
    { key: 'avg_order_value',      name: 'Valor Medio Pedido', format: 'currency' as const },
    { key: 'gross_margin_pct',     name: 'Margen Bruto',       format: 'percentage' as const },
    { key: 'repeat_purchase_rate', name: 'Tasa Recompra',      format: 'percentage' as const },
    { key: 'return_rate',          name: 'Devoluciones',       format: 'percentage' as const },
    { key: 'unique_customers',     name: 'Clientes Únicos',    format: 'number' as const },
    { key: 'avg_customer_ltv',     name: 'LTV Medio',          format: 'currency' as const },
    { key: 'avg_delivery_days',    name: 'Días Entrega',       format: 'number' as const },
    { key: 'total_discounts',      name: 'Descuentos',         format: 'currency' as const },
  ];

  return entries
    .map(({ key, name, format }) => {
      const d = (response.kpis as Record<string, any>)[key];
      if (!d || d.availability === 'missing' || d.value === null) return null;
      const change = d.growth_pct ?? 0;
      return {
        id: key, name, format, tenantId: '',
        value: d.value,
        previousValue: d.vs_previous ?? d.value,
        change: Math.abs(change),
        changeType: (change === 0 ? 'neutral' : change > 0 ? 'positive' : 'negative') as KPI['changeType'],
      };
    })
    .filter(Boolean) as KPI[];
}

export function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>();

  const [imp, setImp]                   = useState<BackendImport | null>(null);
  const [kpiResponse, setKpiResponse]   = useState<BackendKpiResponse | null>(null);
  const [kpis, setKpis]                 = useState<KPI[]>([]);
  const [loading, setLoading]           = useState(true);
  const [insightsText, setInsightsText] = useState('');
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const imports = await getImports();
        const found = imports.find(i => i.id === id) || null;
        setImp(found);

        if (found?.data_date_from && found?.data_date_to) {
          const kpiRes = await getKpiResponse('custom', found.data_date_from, found.data_date_to);
          setKpiResponse(kpiRes);
          setKpis(mapKpis(kpiRes));
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleInsights = async () => {
    setShowInsights(true);
    if (insightsText) return;
    setInsightsLoading(true);
    try {
      const text = await getInsightsText(
        'custom',
        imp?.data_date_from || undefined,
        imp?.data_date_to || undefined
      );
      setInsightsText(text);
    } catch {
      setInsightsText('No se pudieron cargar los insights.');
    } finally {
      setInsightsLoading(false);
    }
  };

  if (loading) return <PageLoading message="Cargando análisis..." />;

  if (!imp) return (
    <div className="text-center py-20">
      <p className="text-muted-foreground">Import no encontrado.</p>
      <Link href="/app/dashboards"><Button variant="ghost" className="mt-4">Volver</Button></Link>
    </div>
  );

  const hasDateRange = imp.data_date_from && imp.data_date_to;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Link href="/app/dashboards">
            <Button variant="ghost" size="icon" className="mt-0.5">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <h1 className="text-2xl font-bold text-foreground">{imp.filename}</h1>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="capitalize bg-muted px-2 py-0.5 rounded text-xs">
                {imp.detected_type}
              </span>
              <span>{imp.valid_rows.toLocaleString('es-ES')} filas</span>
              {hasDateRange && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {imp.data_date_from} → {imp.data_date_to}
                </span>
              )}
            </div>
          </div>
        </div>

        <Button onClick={handleInsights} className="gap-2" variant="outline">
          <Sparkles className="h-4 w-4" />
          Análisis IA
        </Button>
      </div>

      {/* Sin rango de fechas */}
      {!hasDateRange && (
        <div className="bg-muted/50 border rounded-lg p-6 text-center">
          <p className="text-muted-foreground">
            Este import no contiene datos de pedidos con fechas.
            No se pueden calcular KPIs para este fichero.
          </p>
        </div>
      )}

      {/* KPI Cards */}
      {kpis.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Métricas</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {kpis.map(kpi => <KpiCard key={kpi.id} kpi={kpi} />)}
          </div>
        </section>
      )}

      {/* Gráficas */}
      {kpiResponse && (
        <section className="grid lg:grid-cols-2 gap-6">
          <ChartCard
            title="Revenue en el tiempo"
            subtitle="Evolución mensual"
            data={kpiResponse.charts.revenue_over_time}
            valuePrefix="€"
          />
          <ChartCard
            title="Pedidos en el tiempo"
            subtitle="Volumen de pedidos"
            data={kpiResponse.charts.orders_over_time}
          />
          {kpiResponse.charts.revenue_by_channel.length > 0 && (
            <ChartCard
              title="Revenue por canal"
              subtitle="Distribución de ventas por canal"
              data={kpiResponse.charts.revenue_by_channel}
              type="bar"
              valuePrefix="€"
            />
          )}
          {kpiResponse.charts.top_products_revenue.length > 0 && (
            <ChartCard
              title="Top productos"
              subtitle="Por revenue generado"
              data={kpiResponse.charts.top_products_revenue}
              type="bar"
              valuePrefix="€"
            />
          )}
        </section>
      )}

      {showInsights && (
        <AiInsightsPanel
          rawText={insightsText}
          loading={insightsLoading}
          onClose={() => setShowInsights(false)}
        />
      )}
    </div>
  );
}