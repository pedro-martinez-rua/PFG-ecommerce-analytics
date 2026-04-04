import {
  KPI, Dataset,
  BackendKpiResponse, BackendImport, AvailableRange,
  PeriodOption
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Cliente HTTP base ────────────────────────────────────────────────

function getToken(): string | null {
  try {
    const stored = localStorage.getItem('analytics_session');
    if (!stored) return null;
    return JSON.parse(stored)?.token || null;
  } catch {
    return null;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {};

  if (!isFormData) headers['Content-Type'] = 'application/json';
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string> || {}) },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

// ─── Mapping backend KPIs → frontend KPI type ────────────────────────

const KPI_CONFIG: Record<string, {
  name: string;
  format: KPI['format'];
  invertChange?: boolean; // para métricas donde menos es mejor
}> = {
  total_revenue:        { name: 'Revenue Total',          format: 'currency' },
  order_count:          { name: 'Pedidos',                format: 'number' },
  avg_order_value:      { name: 'Valor Medio Pedido',     format: 'currency' },
  net_revenue:          { name: 'Revenue Neto',           format: 'currency' },
  gross_margin_pct:     { name: 'Margen Bruto',           format: 'percentage' },
  total_discounts:      { name: 'Descuentos',             format: 'currency' },
  discount_rate:        { name: 'Tasa Descuento',         format: 'percentage', invertChange: true },
  total_refunds:        { name: 'Reembolsos',             format: 'currency',   invertChange: true },
  refund_rate:          { name: 'Tasa Reembolsos',        format: 'percentage', invertChange: true },
  unique_customers:     { name: 'Clientes Únicos',        format: 'number' },
  repeat_purchase_rate: { name: 'Tasa Recompra',          format: 'percentage' },
  avg_customer_ltv:     { name: 'LTV Medio',              format: 'currency' },
  return_rate:          { name: 'Tasa Devoluciones',      format: 'percentage', invertChange: true },
  returned_orders:      { name: 'Pedidos Devueltos',      format: 'number',     invertChange: true },
  avg_delivery_days:    { name: 'Días Entrega Medio',     format: 'number',     invertChange: true },
  delayed_orders_pct:   { name: 'Pedidos Retrasados',     format: 'percentage', invertChange: true },
};

function mapKpis(response: BackendKpiResponse): KPI[] {
  const result: KPI[] = [];
  const tenantId = '';

  // KPIs prioritarios que siempre van primero si tienen datos
  const priority = [
    'total_revenue', 'order_count', 'avg_order_value',
    'gross_margin_pct', 'repeat_purchase_rate', 'return_rate'
  ];

  for (const key of priority) {
    const config = KPI_CONFIG[key];
    if (!config) continue;
    const kpiData = (response.kpis as Record<string, any>)[key];
    if (!kpiData || kpiData.availability === 'missing' || kpiData.value === null) continue;

    const change = kpiData.growth_pct ?? 0;
    const isPositive = config.invertChange ? change < 0 : change > 0;
    const isNegative = config.invertChange ? change > 0 : change < 0;

    result.push({
      id:            key,
      name:          config.name,
      value:         kpiData.value,
      previousValue: kpiData.vs_previous ?? kpiData.value,
      change:        Math.abs(change),
      changeType:    change === 0 ? 'neutral' : isPositive ? 'positive' : 'negative',
      format:        config.format,
      tenantId,
    });
  }

  // Resto de KPIs disponibles
  for (const [key, config] of Object.entries(KPI_CONFIG)) {
    if (priority.includes(key)) continue;
    const kpiData = (response.kpis as Record<string, any>)[key];
    if (!kpiData || kpiData.availability === 'missing' || kpiData.value === null) continue;

    const change = kpiData.growth_pct ?? 0;
    const isPositive = config.invertChange ? change < 0 : change > 0;

    result.push({
      id:            key,
      name:          config.name,
      value:         kpiData.value,
      previousValue: kpiData.vs_previous ?? kpiData.value,
      change:        Math.abs(change),
      changeType:    change === 0 ? 'neutral' : isPositive ? 'positive' : 'negative',
      format:        config.format,
      tenantId,
    });
  }

  return result;
}

// ─── Funciones públicas ───────────────────────────────────────────────

// KPIs
export async function getKpis(
  period: PeriodOption = 'last_30',
  dateFrom?: string,
  dateTo?: string
): Promise<KPI[]> {
  let path = `/api/kpis/?period=${period}`;
  if (period === 'custom' && dateFrom && dateTo) {
    path = `/api/kpis/?period=custom&date_from=${dateFrom}&date_to=${dateTo}`;
  }
  const response = await apiFetch<BackendKpiResponse>(path);
  return mapKpis(response);
}

// KPI response completa (para gráficas)
export async function getKpiResponse(
  period: PeriodOption = 'last_30',
  dateFrom?: string,
  dateTo?: string
): Promise<BackendKpiResponse> {
  let path = `/api/kpis/?period=${period}`;
  if (period === 'custom' && dateFrom && dateTo) {
    path = `/api/kpis/?period=custom&date_from=${dateFrom}&date_to=${dateTo}`;
  }
  return apiFetch<BackendKpiResponse>(path);
}

// Insights de Groq
export async function getInsightsText(
  period: PeriodOption = 'last_30',
  dateFrom?: string,
  dateTo?: string
): Promise<string> {
  let path = `/api/kpis/insights?period=${period}`;
  if (period === 'custom' && dateFrom && dateTo) {
    path = `/api/kpis/insights?period=custom&date_from=${dateFrom}&date_to=${dateTo}`;
  }
  const res = await apiFetch<{ insights: string }>(path);
  return res.insights;
}

// Imports
export async function getImports(): Promise<BackendImport[]> {
  return apiFetch<BackendImport[]>('/api/imports/');
}

export async function getAvailableRange(): Promise<AvailableRange> {
  return apiFetch<AvailableRange>('/api/imports/available-range');
}

export async function deleteImport(importId: string): Promise<void> {
  await apiFetch(`/api/imports/${importId}`, { method: 'DELETE' });
}

// Upload de fichero
export async function uploadDataset(file: File): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);

  const result = await apiFetch<{
    import_id: string;
    filename: string;
    status: string;
    total_rows: number;
    valid_rows: number;
    detected_type: string;
  }>('/api/imports/', {
    method: 'POST',
    body: formData,
  });

  return {
    id:          result.import_id,
    name:        result.filename.replace(/\.[^/.]+$/, ''),
    filename:    result.filename,
    fileType:    file.name.endsWith('.csv') ? 'csv' : 'xlsx',
    rowCount:    result.total_rows,
    columnCount: 0,
    uploadedAt:  new Date().toISOString(),
    status:      result.status === 'completed' ? 'ready' : result.status === 'failed' ? 'error' : 'processing',
    tenantId:    '',
  };
}

// ─── Legacy stubs (para no romper importaciones existentes) ──────────

export async function getDashboards() {
  const imports = await getImports();
  // Mapear imports a "dashboards" para compatibilidad con OverviewPage
  return imports.map(imp => ({
    id:          imp.id,
    name:        imp.filename,
    description: `${imp.valid_rows} filas · ${imp.detected_type}`,
    tenantId:    '',
    datasetId:   imp.id,
    createdAt:   imp.created_at,
    updatedAt:   imp.created_at,
    kpis:        [],
  }));
}

export async function getDashboard(id: string) {
  const dashboards = await getDashboards();
  return dashboards.find(d => d.id === id) || null;
}

// getInsights mantiene compatibilidad — devuelve array vacío
// El insight real viene de getInsightsText()
export async function getInsights(_dashboardId: string) {
  return [];
}

// Stubs para páginas que aún usan mock
export async function getReports()  { return []; }
export async function getTutorials() { return []; }
export async function getTutorial(_slug: string) { return null; }
export async function getFaqs() { return []; }
export async function submitContactForm(_data: any) { return { success: true }; }