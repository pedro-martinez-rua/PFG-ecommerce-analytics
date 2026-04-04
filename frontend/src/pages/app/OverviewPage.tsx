import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';


import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import {
  getKpiResponse, getInsightsText,
  getDashboards, getAvailableRange
} from '@/lib/api';
import { KPI, BackendKpiResponse, AvailableRange, PeriodOption } from '@/lib/types';
import { KpiCard, ChartCard, AiInsightsPanel } from '@/components/shared';
import {
  ArrowRight, Upload, Sparkles, Clock,
  FolderKanban, TrendingUp, Lightbulb,
  Calendar,
} from 'lucide-react';

// Selector de periodo
const PERIOD_OPTIONS: { value: PeriodOption; label: string }[] = [
  { value: 'last_30',   label: 'Últimos 30 días' },
  { value: 'last_90',   label: 'Últimos 90 días' },
  { value: 'ytd',       label: 'Este año' },
  { value: 'last_year', label: 'Año anterior' },
  { value: 'all',       label: 'Todos los datos' },
];

// Mapea BackendKpiResponse → KPI[] para KpiCard
function mapToKpiCards(response: BackendKpiResponse): KPI[] {
  const entries: Array<{ key: string; name: string; format: KPI['format']; invert?: boolean }> = [
    { key: 'total_revenue',        name: 'Revenue Total',       format: 'currency' },
    { key: 'order_count',          name: 'Pedidos',             format: 'number' },
    { key: 'avg_order_value',      name: 'Valor Medio Pedido',  format: 'currency' },
    { key: 'gross_margin_pct',     name: 'Margen Bruto',        format: 'percentage' },
    { key: 'repeat_purchase_rate', name: 'Tasa Recompra',       format: 'percentage' },
    { key: 'return_rate',          name: 'Tasa Devoluciones',   format: 'percentage', invert: true },
  ];

  return entries
    .map(({ key, name, format, invert }) => {
      const d = (response.kpis as Record<string, any>)[key];
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

export function OverviewPage() {
  const { t } = useTranslation();
  const { user, tenant } = useAuth();

  const [period, setPeriod]           = useState<PeriodOption>('all');
  const [kpiResponse, setKpiResponse] = useState<BackendKpiResponse | null>(null);
  const [kpis, setKpis]               = useState<KPI[]>([]);
  const [dashboards, setDashboards]   = useState<any[]>([]);
  const [availableRange, setAvailableRange] = useState<AvailableRange | null>(null);
  const [insightsText, setInsightsText] = useState<string>('');
  const [loading, setLoading]         = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [searchParams] = useSearchParams();
  const initialPeriod = (searchParams.get('period') as PeriodOption) || 'all';
  const urlDateFrom = searchParams.get('date_from') || undefined;
  const urlDateTo   = searchParams.get('date_to')   || undefined;

  // Cargar datos cuando cambia el periodo
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [kpiRes, dashboardData, range] = await Promise.all([
          getKpiResponse(
            period,
            period === 'custom' ? urlDateFrom : undefined,
            period === 'custom' ? urlDateTo   : undefined
          ),
          getDashboards(),
          getAvailableRange(),
        ]);
        setKpiResponse(kpiRes);
        setKpis(mapToKpiCards(kpiRes));
        setDashboards(dashboardData);
        setAvailableRange(range);
      } catch (e) {
        console.error('Error cargando datos:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [period]);

  const handleLoadInsights = async () => {
    setShowInsights(true);
    if (insightsText) return; // ya cargados
    setInsightsLoading(true);
    try {
      const text = await getInsightsText(period);
      setInsightsText(text);
    } catch {
      setInsightsText('No se pudieron cargar los insights. Inténtalo de nuevo.');
    } finally {
      setInsightsLoading(false);
    }
  };

  const recentImport = dashboards[0];
  const firstName    = user?.fullName?.split(' ')[0] || '';

  const nextActions = [
    {
      icon: Upload,
      title: 'Subir datos',
      description: 'Añade un nuevo CSV o Excel con tus ventas',
      href: '/app/upload',
    },
    {
      icon: FolderKanban,
      title: 'Ver imports',
      description: 'Gestiona los ficheros que has subido',
      href: '/app/dashboards',
    },
    {
      icon: Sparkles,
      title: 'Análisis IA',
      description: 'Obtén recomendaciones personalizadas',
      action: handleLoadInsights,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header + selector de periodo */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {t('overview.welcome.title', { name: firstName })}
          </h1>
          <p className="text-muted-foreground">
            {tenant?.name || ''}
            {availableRange?.has_data && (
              <span className="ml-2 text-xs text-muted-foreground">
                · Datos desde {availableRange.date_from} hasta {availableRange.date_to}
              </span>
            )}
          </p>
        </div>

        {/* Selector de periodo */}
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <select
            value={period}
            onChange={(e) => {
              setPeriod(e.target.value as PeriodOption);
              setInsightsText(''); // resetear insights al cambiar periodo
            }}
            className="text-sm border rounded-md px-3 py-1.5 bg-background text-foreground"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Aviso si no hay datos */}
      {!loading && availableRange && !availableRange.has_data && (
        <div className="bg-muted/50 border rounded-lg p-6 text-center">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <p className="font-medium">No tienes datos cargados aún</p>
          <p className="text-sm text-muted-foreground mb-4">
            Sube tu primer CSV o Excel para empezar a ver tus KPIs
          </p>
          <Link href="/app/upload">
            <Button size="sm">Subir datos</Button>
          </Link>
        </div>
      )}

      {/* KPI Cards */}
      {(loading || kpis.length > 0) && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Métricas clave</h2>
            <Button variant="ghost" size="sm" onClick={handleLoadInsights} className="gap-1">
              <Sparkles className="h-4 w-4" />
              Analizar con IA
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading
              ? Array(6).fill(0).map((_, i) => <KpiCard key={i} kpi={{} as KPI} loading />)
              : kpis.map((kpi) => <KpiCard key={kpi.id} kpi={kpi} />)}
          </div>
        </section>
      )}

      {/* Gráficas */}
      {(loading || kpiResponse) && (
        <section className="grid lg:grid-cols-2 gap-6">
          <ChartCard
            title="Revenue en el tiempo"
            subtitle={`Evolución por ${(kpiResponse?.charts?.revenue_over_time?.length || 0) > 90 ? 'mes' : 'día'}`}
            loading={loading}
            data={kpiResponse?.charts?.revenue_over_time}
          />
          <ChartCard
            title="Pedidos en el tiempo"
            subtitle="Evolución del volumen de pedidos"
            loading={loading}
            data={kpiResponse?.charts?.orders_over_time}
          />
        </section>
      )}

      {/* Layout inferior */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">

          {/* Import reciente */}
          {recentImport && !loading && (
            <section className="bg-background rounded-lg border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-lg font-semibold">Último import</h2>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">{recentImport.name}</p>
                  <p className="text-sm text-muted-foreground">{recentImport.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(recentImport.updatedAt).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <Link href="/app/dashboards">
                  <Button size="sm">Ver imports</Button>
                </Link>
              </div>
            </section>
          )}

          {/* Preview insights */}
          <section className="bg-background rounded-lg border p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-secondary" />
                <h2 className="text-lg font-semibold">Análisis IA</h2>
              </div>
              <Button variant="ghost" size="sm" onClick={handleLoadInsights}>
                {insightsText ? 'Ver análisis completo' : 'Generar análisis'}
              </Button>
            </div>

            {insightsText ? (
              <p className="text-sm text-muted-foreground line-clamp-3">
                {insightsText.replace(/\*\*/g, '').split('\n')[0]}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Pulsa "Generar análisis" para obtener recomendaciones personalizadas basadas en tus datos.
              </p>
            )}
          </section>
        </div>

        {/* Próximos pasos */}
        <section className="bg-background rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-success" />
            <h2 className="text-lg font-semibold">Acciones</h2>
          </div>
          <div className="space-y-3">
            {nextActions.map((action, index) => {
              const Icon = action.icon;
              const content = (
                <div className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer">
                  <div className="bg-muted rounded-lg p-2">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground text-sm">{action.title}</p>
                    <p className="text-xs text-muted-foreground">{action.description}</p>
                  </div>
                </div>
              );
              if (action.href) return <Link key={index} href={action.href}>{content}</Link>;
              return <div key={index} onClick={action.action}>{content}</div>;
            })}
          </div>
        </section>
      </div>

      {/* Panel lateral de insights */}
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