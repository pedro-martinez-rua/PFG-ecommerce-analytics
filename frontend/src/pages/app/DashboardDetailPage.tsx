import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getSavedDashboard, createReport } from '@/lib/api';
import { KPI, BackendKpiResponse } from '@/lib/types';
import { KpiCard, ChartCard, PageLoading, AiInsightsPanel } from '@/components/shared';
import { ArrowLeft, Sparkles, Calendar, Save, CheckCircle2 } from 'lucide-react';

function mapKpis(response: BackendKpiResponse): KPI[] {
  const entries = [
    { key: 'total_revenue',        name: 'Revenue Total',      format: 'currency'    as const },
    { key: 'order_count',          name: 'Pedidos',            format: 'number'      as const },
    { key: 'avg_order_value',      name: 'Valor Medio Pedido', format: 'currency'    as const },
    { key: 'gross_margin_pct',     name: 'Margen Bruto',       format: 'percentage'  as const },
    { key: 'repeat_purchase_rate', name: 'Tasa Recompra',      format: 'percentage'  as const },
    { key: 'return_rate',          name: 'Devoluciones',       format: 'percentage'  as const },
    { key: 'unique_customers',     name: 'Clientes Únicos',    format: 'number'      as const },
    { key: 'avg_customer_ltv',     name: 'LTV Medio',          format: 'currency'    as const },
    { key: 'total_discounts',      name: 'Descuentos',         format: 'currency'    as const },
    { key: 'delayed_orders_pct',   name: 'Pedidos Retrasados', format: 'percentage'  as const },
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
  const navigate = useNavigate();

  const [data, setData]                 = useState<any>(null);
  const [kpis, setKpis]                 = useState<KPI[]>([]);
  const [loading, setLoading]           = useState(true);
  const [insightsText, setInsightsText] = useState('');
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [saving, setSaving]             = useState(false);
  const [saved, setSaved]               = useState(false);

  useEffect(() => {
    if (!id) return;
    getSavedDashboard(id)
      .then(res => {
        setData(res);
        setKpis(mapKpis(res as unknown as BackendKpiResponse));
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleShowInsights = async () => {
    setShowInsights(true);
    if (insightsText) return;
    setInsightsLoading(true);
    try {
      // Importar inline para no circular
      const { getInsightsText } = await import('@/lib/api');
      const text = await getInsightsText(
        data?.date_from && data?.date_to ? 'custom' : 'all',
        data?.date_from || undefined,
        data?.date_to   || undefined
      );
      setInsightsText(text);
    } catch {
      setInsightsText('No se pudieron cargar los insights.');
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleSaveReport = async () => {
    if (!id || saving || saved) return;
    setSaving(true);
    try {
      await createReport(id);
      setSaved(true);
      // Mostrar confirmación 3s y ofrecer ir a informes
      setTimeout(() => setSaved(false), 4000);
    } catch {
      alert('Error al guardar el informe. Inténtalo de nuevo.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoading message="Cargando dashboard..." />;

  if (!data) return (
    <div className="text-center py-20">
      <p className="text-muted-foreground">Dashboard no encontrado.</p>
      <Link href="/app/dashboards">
        <Button variant="ghost" className="mt-4">Volver</Button>
      </Link>
    </div>
  );

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
            <h1 className="text-2xl font-bold text-foreground">{data.name}</h1>
            <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
              {data.date_from && data.date_to ? (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {data.date_from} → {data.date_to}
                </span>
              ) : (
                <span>Todos los datos disponibles</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleShowInsights}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4" />
            Ver análisis IA
          </Button>

          {saved ? (
            <Button variant="outline" className="gap-2 text-success border-success" disabled>
              <CheckCircle2 className="h-4 w-4" />
              Informe guardado
            </Button>
          ) : (
            <Button
              onClick={handleSaveReport}
              disabled={saving}
              className="gap-2"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Guardando...' : 'Guardar informe'}
            </Button>
          )}
        </div>
      </div>

      {/* Banner informe guardado */}
      {saved && (
        <div className="flex items-center justify-between bg-success/10 border border-success/20 rounded-lg px-4 py-3">
          <p className="text-sm text-success font-medium">
            ✓ Informe guardado con análisis de IA incluido
          </p>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate('/app/reports')}
          >
            Ver informes
          </Button>
        </div>
      )}

      {/* KPI Cards */}
      {kpis.length > 0 ? (
        <section>
          <h2 className="text-lg font-semibold mb-4">Métricas</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {kpis.map(kpi => <KpiCard key={kpi.id} kpi={kpi} />)}
          </div>
        </section>
      ) : (
        <div className="bg-muted/50 border rounded-lg p-6 text-center">
          <p className="text-muted-foreground text-sm">
            No hay datos de pedidos en el rango seleccionado.
          </p>
        </div>
      )}

      {/* Gráficas */}
      {data.charts && (
        <section className="grid lg:grid-cols-2 gap-6">
          <ChartCard
            title="Revenue en el tiempo"
            subtitle="Evolución mensual"
            data={data.charts.revenue_over_time}
            valuePrefix="€"
          />
          <ChartCard
            title="Pedidos en el tiempo"
            subtitle="Volumen de pedidos"
            data={data.charts.orders_over_time}
          />
          {data.charts.revenue_by_channel?.length > 0 && (
            <ChartCard
              title="Revenue por canal"
              data={data.charts.revenue_by_channel}
              type="bar"
              valuePrefix="€"
            />
          )}
          {data.charts.top_products_revenue?.length > 0 && (
            <ChartCard
              title="Top productos"
              subtitle="Por revenue generado"
              data={data.charts.top_products_revenue}
              type="bar"
              valuePrefix="€"
            />
          )}
          {data.charts.revenue_by_category?.length > 0 && (
            <ChartCard
              title="Revenue por categoría"
              data={data.charts.revenue_by_category}
              type="bar"
              valuePrefix="€"
            />
          )}
          {data.charts.revenue_by_country?.length > 0 && (
            <ChartCard
              title="Top países"
              data={data.charts.revenue_by_country}
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