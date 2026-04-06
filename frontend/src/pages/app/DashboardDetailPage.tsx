import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getSavedDashboard, createReport, getDashboardInsights, getAvailableRange } from '@/lib/api';
import { KPI, BackendKpiResponse, AvailableRange } from '@/lib/types';
import { KpiCard, ChartCard, PageLoading, AiInsightsPanel } from '@/components/shared';
import { ArrowLeft, Sparkles, Calendar, Save, CheckCircle2, Filter, AlertCircle } from 'lucide-react';

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

function formatDate(iso: string): string {
  try {
    return new Date(iso + 'T00:00:00').toLocaleDateString('es-ES', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function validateRange(from: string, to: string, available: AvailableRange): string | null {
  if (!available.has_data || !available.date_from || !available.date_to) {
    return 'No hay datos disponibles en esta cuenta.';
  }
  if (from > to) {
    return 'La fecha de inicio debe ser anterior a la fecha de fin.';
  }
  if (to < available.date_from || from > available.date_to) {
    return `El rango seleccionado no contiene datos. Los datos disponibles van del ${formatDate(available.date_from)} al ${formatDate(available.date_to)}.`;
  }
  return null;
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

  const [availableRange, setAvailableRange] = useState<AvailableRange | null>(null);

  const [filterFrom, setFilterFrom] = useState('');
  const [filterTo, setFilterTo]     = useState('');
  const [activeFrom, setActiveFrom] = useState('');
  const [activeTo, setActiveTo]     = useState('');
  const [dateError, setDateError]   = useState<string | null>(null);

  const filterIsActive   = activeFrom !== '' && activeTo !== '';
  const filterHasChanges = filterFrom !== activeFrom || filterTo !== activeTo;

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getSavedDashboard(id),
      getAvailableRange(),
    ]).then(([res, range]) => {
      setData(res);
      setKpis(mapKpis(res as unknown as BackendKpiResponse));
      setAvailableRange(range);
      if (res.date_from && res.date_to) {
        setFilterFrom(res.date_from);
        setFilterTo(res.date_to);
        setActiveFrom(res.date_from);
        setActiveTo(res.date_to);
      } else if (range.date_from && range.date_to) {
        setFilterFrom(range.date_from);
        setFilterTo(range.date_to);
      }
    }).finally(() => setLoading(false));
  }, [id]);

  const handleFromChange = (val: string) => { setFilterFrom(val); setDateError(null); };
  const handleToChange   = (val: string) => { setFilterTo(val);   setDateError(null); };

  const handleApplyFilter = async () => {
    if (!id || !filterFrom || !filterTo) return;

    if (availableRange) {
      const error = validateRange(filterFrom, filterTo, availableRange);
      if (error) { setDateError(error); return; }
    }

    setLoading(true);
    setDateError(null);
    setInsightsText('');
    setShowInsights(false);

    try {
      const res = await getSavedDashboard(id, filterFrom, filterTo);

      const orderCount = (res as any)?.kpis?.order_count?.value;
      if (orderCount === 0 || orderCount === null) {
        const rangeMsg = availableRange?.date_from && availableRange?.date_to
          ? ` Los datos disponibles van del ${formatDate(availableRange.date_from)} al ${formatDate(availableRange.date_to)}.`
          : '';
        setDateError(`No hay pedidos entre ${formatDate(filterFrom)} y ${formatDate(filterTo)}.${rangeMsg}`);
        setLoading(false);
        return;
      }

      setData((prev: any) => ({ ...prev, ...res, date_from: filterFrom, date_to: filterTo }));
      setKpis(mapKpis(res as unknown as BackendKpiResponse));
      setActiveFrom(filterFrom);
      setActiveTo(filterTo);
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilter = async () => {
    if (!id) return;
    setLoading(true);
    setDateError(null);
    setInsightsText('');
    setShowInsights(false);
    try {
      const res = await getSavedDashboard(id);
      setData(res);
      setKpis(mapKpis(res as unknown as BackendKpiResponse));
      const from = res.date_from ?? '';
      const to   = res.date_to   ?? '';
      setFilterFrom(from); setFilterTo(to);
      setActiveFrom(from); setActiveTo(to);
    } finally {
      setLoading(false);
    }
  };

  const handleShowInsights = async () => {
    if (!id) return;
    setShowInsights(true);
    if (insightsText) return;
    setInsightsLoading(true);
    try {
      const text = await getDashboardInsights(id, activeFrom || undefined, activeTo || undefined);
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
      await createReport(id, activeFrom || undefined, activeTo || undefined);
      setSaved(true);
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
              {filterIsActive ? (
                <span className="flex items-center gap-1 text-secondary font-medium">
                  <Calendar className="h-3.5 w-3.5" />
                  {formatDate(activeFrom)} → {formatDate(activeTo)}
                  {(activeFrom !== data.date_from || activeTo !== data.date_to) && (
                    <span className="ml-1 text-xs bg-secondary/10 text-secondary px-1.5 py-0.5 rounded">
                      filtro activo
                    </span>
                  )}
                </span>
              ) : (
                <span>Todos los datos disponibles</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleShowInsights} className="gap-2">
            <Sparkles className="h-4 w-4" />
            Ver análisis IA
          </Button>
          {saved ? (
            <Button variant="outline" className="gap-2 text-success border-success" disabled>
              <CheckCircle2 className="h-4 w-4" />
              Informe guardado
            </Button>
          ) : (
            <Button onClick={handleSaveReport} disabled={saving} className="gap-2">
              <Save className="h-4 w-4" />
              {saving ? 'Guardando...' : 'Guardar informe'}
            </Button>
          )}
        </div>
      </div>

      {/* Filtro de fechas + error */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-end gap-3 bg-muted/40 border rounded-lg px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Filter className="h-4 w-4" />
            <span className="font-medium">Filtrar por rango</span>
          </div>

          {availableRange?.has_data && availableRange.date_from && availableRange.date_to && (
            <span className="text-xs text-muted-foreground">
              Disponible: {formatDate(availableRange.date_from)} – {formatDate(availableRange.date_to)}
            </span>
          )}

          <div className="flex items-center gap-2 flex-1">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Desde</label>
              <input
                type="date"
                value={filterFrom}
                min={availableRange?.date_from ?? undefined}
                max={availableRange?.date_to ?? undefined}
                onChange={e => handleFromChange(e.target.value)}
                className="text-sm border rounded-md px-2 py-1.5 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Hasta</label>
              <input
                type="date"
                value={filterTo}
                min={filterFrom || availableRange?.date_from || undefined}
                max={availableRange?.date_to ?? undefined}
                onChange={e => handleToChange(e.target.value)}
                className="text-sm border rounded-md px-2 py-1.5 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="flex items-end gap-2 pb-0.5">
              <Button
                size="sm"
                onClick={handleApplyFilter}
                disabled={!filterFrom || !filterTo || !filterHasChanges}
              >
                Aplicar
              </Button>
              {filterIsActive && (activeFrom !== data.date_from || activeTo !== data.date_to) && (
                <Button size="sm" variant="ghost" onClick={handleResetFilter} className="text-muted-foreground">
                  Resetear
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Aviso de error con rango disponible clicable */}
        {dateError && (
          <div className="flex items-start gap-2 bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3">
            <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
            <div className="text-sm text-destructive">
              <p>{dateError}</p>
              {availableRange?.date_from && availableRange?.date_to && (
                <p className="mt-1 text-destructive/80">
                  Rango disponible:{' '}
                  <button
                    className="underline font-medium hover:no-underline"
                    onClick={() => {
                      setFilterFrom(availableRange.date_from!);
                      setFilterTo(availableRange.date_to!);
                      setDateError(null);
                    }}
                  >
                    {formatDate(availableRange.date_from)} – {formatDate(availableRange.date_to)}
                  </button>
                  {' '}(clic para seleccionarlo)
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Banner informe guardado */}
      {saved && (
        <div className="flex items-center justify-between bg-success/10 border border-success/20 rounded-lg px-4 py-3">
          <p className="text-sm text-success font-medium">
            ✓ Informe guardado {filterIsActive ? `(${formatDate(activeFrom)} → ${formatDate(activeTo)})` : ''} con análisis de IA incluido
          </p>
          <Button size="sm" variant="outline" onClick={() => navigate('/app/reports')}>
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
          <ChartCard title="Revenue en el tiempo" subtitle="Evolución mensual"
            data={data.charts.revenue_over_time} valuePrefix="€" />
          <ChartCard title="Pedidos en el tiempo" subtitle="Volumen de pedidos"
            data={data.charts.orders_over_time} />
          {data.charts.revenue_by_channel?.length > 0 && (
            <ChartCard title="Revenue por canal" data={data.charts.revenue_by_channel}
              type="bar" valuePrefix="€" />
          )}
          {data.charts.top_products_revenue?.length > 0 && (
            <ChartCard title="Top productos" subtitle="Por revenue generado"
              data={data.charts.top_products_revenue} type="bar" valuePrefix="€" />
          )}
          {data.charts.revenue_by_category?.length > 0 && (
            <ChartCard title="Revenue por categoría" data={data.charts.revenue_by_category}
              type="bar" valuePrefix="€" />
          )}
          {data.charts.revenue_by_country?.length > 0 && (
            <ChartCard title="Top países" data={data.charts.revenue_by_country}
              type="bar" valuePrefix="€" />
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