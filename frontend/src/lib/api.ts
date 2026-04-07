import {
  KPI, Dataset,
  BackendKpiResponse, BackendImport, AvailableRange,
  PeriodOption, SavedDashboard, SavedReport, UploadImportResult, ImportDiagnosis,
  ImportPreviewResponse, MappingSuggestionResponse, MappingApplyResponse
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

  if (res.status === 204) return undefined as unknown as T;

  return res.json();
}

// ─── Mapping backend KPIs → frontend KPI type ────────────────────────

const KPI_CONFIG: Record<string, {
  name: string;
  format: KPI['format'];
  invertChange?: boolean;
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
export async function uploadDataset(file: File): Promise<UploadImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch<UploadImportResult & { suggestions?: string[] }>('/api/imports/', {
    method: 'POST',
    body: formData,
  });
}

// ─── Legacy stubs ────────────────────────────────────────────────────

export async function getDashboards() {
  const imports = await getImports();
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

export async function getInsights(_dashboardId: string) { return []; }
export async function getTutorials() { return []; }
export async function getTutorial(_slug: string) { return null; }
export async function getFaqs() { return []; }
export async function submitContactForm(_data: any) { return { success: true }; }

// ─── Dashboards guardados ─────────────────────────────────────────────

export async function createDashboard(data: {
  name: string;
  date_from?: string;
  date_to?: string;
  import_ids?: string[];
}): Promise<SavedDashboard> {
  return apiFetch<SavedDashboard>('/api/dashboards/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getSavedDashboards(): Promise<SavedDashboard[]> {
  return apiFetch<SavedDashboard[]>('/api/dashboards/');
}

// Acepta fechas opcionales para filtrar el rango sin modificar el dashboard guardado
export async function getSavedDashboard(
  id: string,
  dateFrom?: string,
  dateTo?: string
): Promise<SavedDashboard & BackendKpiResponse> {
  let path = `/api/dashboards/${id}`;
  if (dateFrom && dateTo) {
    path += `?date_from=${dateFrom}&date_to=${dateTo}`;
  }
  return apiFetch<SavedDashboard & BackendKpiResponse>(path);
}

// Acepta fechas opcionales para generar insights del rango filtrado
export async function getDashboardInsights(
  id: string,
  dateFrom?: string,
  dateTo?: string
): Promise<string> {
  let path = `/api/dashboards/${id}/insights`;
  if (dateFrom && dateTo) {
    path += `?date_from=${dateFrom}&date_to=${dateTo}`;
  }
  const res = await apiFetch<{ insights: string }>(path);
  return res.insights;
}

export async function deleteSavedDashboard(id: string): Promise<void> {
  await apiFetch(`/api/dashboards/${id}`, { method: 'DELETE' });
}

// ─── Informes guardados ───────────────────────────────────────────────

// Acepta fechas opcionales para guardar el informe con el rango filtrado activo
export async function createReport(
  dashboardId: string,
  dateFrom?: string,
  dateTo?: string
): Promise<SavedReport> {
  return apiFetch<SavedReport>('/api/reports/', {
    method: 'POST',
    body: JSON.stringify({
      dashboard_id: dashboardId,
      ...(dateFrom && dateTo ? { date_from: dateFrom, date_to: dateTo } : {}),
    }),
  });
}

export async function getReports(): Promise<SavedReport[]> {
  return apiFetch<SavedReport[]>('/api/reports/');
}

export async function getReport(id: string): Promise<SavedReport> {
  return apiFetch<SavedReport>(`/api/reports/${id}`);
}

export async function deleteReport(id: string): Promise<void> {
  await apiFetch(`/api/reports/${id}`, { method: 'DELETE' });
}

export async function getImportDiagnosis(importId: string): Promise<ImportDiagnosis> {
  return apiFetch<ImportDiagnosis>(`/api/imports/${importId}/diagnosis`);
}

export async function getImportPreview(importId: string, mode: "raw" | "normalized" = "raw"): Promise<ImportPreviewResponse> {
  return apiFetch(`/api/imports/${importId}/preview?mode=${mode}`);
}

export async function getImportMappingSuggestion(importId: string): Promise<MappingSuggestionResponse> {
  return apiFetch<MappingSuggestionResponse>(`/api/imports/${importId}/mapping-suggestion`);
}

export async function applyImportMapping(importId: string, payload: {
  sheet_name?: string;
  upload_type?: string;
  assignments: { source_column: string; canonical_field?: string | null }[];
}): Promise<MappingApplyResponse> {
  return apiFetch<MappingApplyResponse>(`/api/imports/${importId}/mapping`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getImportImpact(importId: string): Promise<{
  import_id: string;
  filename: string;
  has_impact: boolean;
  affected: {
    dashboard_id: string;
    dashboard_name: string;
    total_imports: number;
    remaining: number;
    will_be_deleted: boolean;
  }[];
}> {
  return apiFetch(`/api/imports/${importId}/impact`);
}
// ─── Team ──────────────────────────────────────────────────────────────

export interface InviteMemberPayload {
  email: string;
  full_name?: string;
  password: string;
  role: 'admin' | 'analyst';
}

import type { TeamMember, TeamReport } from './types';

export function getTeamMembers(): Promise<TeamMember[]> {
  return apiFetch('/api/team/members');
}

export function removeMember(memberId: string): Promise<void> {
  return apiFetch(`/api/team/members/${memberId}`, { method: 'DELETE' });
}

export function getTeamReports(): Promise<TeamReport[]> {
  return apiFetch('/api/team/reports');
}

export function shareReport(reportId: string, shared: boolean): Promise<SavedReport> {
  return apiFetch(`/api/reports/${reportId}/share`, {
    method: 'PATCH',
    body: JSON.stringify({ shared }),
  });
}

export function toggleTeamAccess(memberId: string, teamAccess: boolean): Promise<TeamMember> {
  return apiFetch(`/api/team/members/${memberId}/access`, {
    method: 'PATCH',
    body: JSON.stringify({ team_access: teamAccess }),
  });
}

export function getTeamReport(id: string): Promise<TeamReport> {
  return apiFetch(`/api/team/reports/${id}`);
}