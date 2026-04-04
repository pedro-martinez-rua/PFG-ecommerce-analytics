// Multi-tenant types
export type UserRole = 'admin' | 'collaborator';

export interface Tenant {
  id: string;
  name: string;
  plan: 'free' | 'starter' | 'professional' | 'enterprise';
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  tenantId: string;
  createdAt: string;
}

export interface Session {
  user: User;
  tenant: Tenant;
  token: string;
  expiresAt: string;
}

// Dashboard & Analytics types
export interface KPI {
  id: string;
  name: string;
  value: number;
  previousValue: number;
  change: number;
  changeType: 'positive' | 'negative' | 'neutral';
  format: 'currency' | 'number' | 'percentage';
  tenantId: string;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  tenantId: string;
  datasetId: string;
  createdAt: string;
  updatedAt: string;
  kpis: KPI[];
  isDefault?: boolean;
}

export interface Dataset {
  id: string;
  name: string;
  filename: string;
  fileType: 'csv' | 'xlsx' | 'json';
  rowCount: number;
  columnCount: number;
  uploadedAt: string;
  status: 'processing' | 'ready' | 'error';
  tenantId: string;
}

export interface Report {
  id: string;
  name: string;
  dashboardId: string;
  dashboardName: string;
  createdAt: string;
  kpiSummary: string;
  tenantId: string;
}

export interface Insight {
  id: string;
  dashboardId: string;
  title: string;
  content: string;
  type: 'opportunity' | 'warning' | 'trend' | 'recommendation';
  createdAt: string;
}

export interface Tutorial {
  slug: string;
  title: string;
  description: string;
  category: string;
  readTime: string;
  content: string;
}

export interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
}

// Form types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterPayload {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  companyName: string;
  acceptTerms: boolean;
}

export interface ContactFormData {
  name: string;
  email: string;
  company?: string;
  message: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

// Route types for custom router
export interface Route {
  path: string;
  component: React.ComponentType<any>;
  layout?: 'marketing' | 'auth' | 'app';
  protected?: boolean;
  roles?: UserRole[];
}

export interface RouteParams {
  [key: string]: string;
}

// Tipos del backend

export interface BackendKpiValue {
  value: number | null;
  vs_previous: number | null;
  growth_pct: number | null;
  availability: 'real' | 'estimated' | 'missing';
  reason: string | null;
}

export interface BackendNewVsReturning {
  value: { new: number; returning: number } | null;
  availability: 'real' | 'estimated' | 'missing';
  reason: string | null;
}

export interface DataCoverage {
  has_cogs: boolean;
  has_channels: boolean;
  has_countries: boolean;
  has_returns: boolean;
  has_discounts: boolean;
  has_delivery: boolean;
  has_refunds: boolean;
  has_customers: boolean;
  has_products: boolean;
  has_categories: boolean;
  order_count: number;
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface BackendKpiResponse {
  period: string;
  date_from: string;
  date_to: string;
  data_coverage: DataCoverage;
  kpis: {
    total_revenue: BackendKpiValue;
    order_count: BackendKpiValue;
    avg_order_value: BackendKpiValue;
    net_revenue: BackendKpiValue;
    total_discounts: BackendKpiValue;
    discount_rate: BackendKpiValue;
    gross_margin: BackendKpiValue;
    gross_margin_pct: BackendKpiValue;
    total_refunds: BackendKpiValue;
    refund_rate: BackendKpiValue;
    unique_customers: BackendKpiValue;
    new_vs_returning: BackendNewVsReturning;
    repeat_purchase_rate: BackendKpiValue;
    avg_customer_ltv: BackendKpiValue;
    return_rate: BackendKpiValue;
    returned_orders: BackendKpiValue;
    avg_delivery_days: BackendKpiValue;
    delayed_orders_pct: BackendKpiValue;
  };
  charts: {
    revenue_over_time: ChartPoint[];
    orders_over_time: ChartPoint[];
    revenue_by_channel: ChartPoint[];
    revenue_by_country: ChartPoint[];
    orders_by_status: ChartPoint[];
    top_products_revenue: ChartPoint[];
    top_products_units: ChartPoint[];
    revenue_by_category: ChartPoint[];
    product_margin: ChartPoint[];
    new_vs_returning: { new: number; returning: number };
  };
}

export interface BackendImport {
  id: string;
  filename: string;
  file_format: string;
  status: string;
  detected_type: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  file_size_bytes: number;
  created_at: string;
  completed_at: string | null;
  data_date_from: string | null;
  data_date_to: string | null;
  orders_loaded: number;
  lines_loaded: number;
}

export interface AvailableRange {
  has_data: boolean;
  date_from: string | null;
  date_to: string | null;
  total_orders: number;
  months_with_data: number;
}

export type PeriodOption = 'last_30' | 'last_90' | 'ytd' | 'last_year' | 'all' | 'custom';