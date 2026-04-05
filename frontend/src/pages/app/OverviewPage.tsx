import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import {
  getImports, getSavedDashboards, getReports, getAvailableRange
} from '@/lib/api';
import { BackendImport, SavedDashboard, SavedReport, AvailableRange } from '@/lib/types';
import {
  Upload, LayoutDashboard, FileText, ArrowRight,
  CheckCircle2, Calendar, BarChart3, Sparkles,
  ChevronRight, Clock, Database, AlertCircle,
  TrendingUp, BookOpen,
} from 'lucide-react';

// ─── Helpers ──────────────────────────────────────────────────────────

function StatusDot({ status }: { status: string }) {
  if (status === 'completed') return (
    <span className="flex items-center gap-1 text-xs text-success">
      <CheckCircle2 className="h-3 w-3" />Completado
    </span>
  );
  if (status === 'failed') return (
    <span className="flex items-center gap-1 text-xs text-destructive">
      <AlertCircle className="h-3 w-3" />Fallido
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      <Clock className="h-3 w-3" />Procesando
    </span>
  );
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es-ES', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

// ─── Sección genérica con título + "Ver todos" ────────────────────────

function Section({
  title,
  icon: Icon,
  count,
  href,
  children,
  emptyTitle,
  emptyDesc,
  emptyAction,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  count: number;
  href: string;
  children: React.ReactNode;
  emptyTitle: string;
  emptyDesc: string;
  emptyAction?: { label: string; href: string };
}) {
  return (
    <div className="bg-background border rounded-xl overflow-hidden">
      {/* Header de sección */}
      <div className="flex items-center justify-between px-5 py-4 border-b">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-secondary" />
          <h2 className="font-semibold text-foreground">{title}</h2>
          {count > 0 && (
            <span className="bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-full">
              {count}
            </span>
          )}
        </div>
        {count > 0 && (
          <Link href={href} className="flex items-center gap-1 text-xs text-secondary hover:text-secondary">
            Ver todos <ArrowRight className="h-3 w-3" />
          </Link>
        )}
      </div>

      {/* Contenido */}
      {count === 0 ? (
        <div className="px-5 py-8 text-center">
          <p className="text-sm font-medium text-foreground mb-1">{emptyTitle}</p>
          <p className="text-xs text-muted-foreground mb-3">{emptyDesc}</p>
          {emptyAction && (
            <Link href={emptyAction.href}>
              <Button size="sm" variant="outline">{emptyAction.label}</Button>
            </Link>
          )}
        </div>
      ) : (
        children
      )}
    </div>
  );
}

// ─── Cómo funciona ────────────────────────────────────────────────────

const STEPS = [
  {
    step: '1',
    icon: Upload,
    title: 'Sube tus datos',
    desc: 'Importa tu CSV o Excel con pedidos, clientes o productos. El sistema los procesa automáticamente.',
    href: '/app/upload',
    action: 'Subir datos',
  },
  {
    step: '2',
    icon: LayoutDashboard,
    title: 'Crea un dashboard',
    desc: 'Selecciona los ficheros que quieres analizar, dales un nombre y genera tu dashboard con KPIs y gráficas.',
    href: '/app/dashboards',
    action: 'Ir a dashboards',
  },
  {
    step: '3',
    icon: Sparkles,
    title: 'Obtén análisis de IA',
    desc: 'Desde el dashboard, activa el análisis de IA para recibir recomendaciones concretas sobre tu negocio.',
    href: '/app/dashboards',
    action: 'Ver dashboards',
  },
  {
    step: '4',
    icon: FileText,
    title: 'Guarda informes',
    desc: 'Guarda snapshots de tus dashboards con el análisis de IA incluido. Consúltalos cuando quieras.',
    href: '/app/reports',
    action: 'Ver informes',
  },
];

// ─── Página principal ─────────────────────────────────────────────────

export function OverviewPage() {
  const { user, tenant } = useAuth();
  const navigate = useNavigate();

  const [imports, setImports]       = useState<BackendImport[]>([]);
  const [dashboards, setDashboards] = useState<SavedDashboard[]>([]);
  const [reports, setReports]       = useState<SavedReport[]>([]);
  const [range, setRange]           = useState<AvailableRange | null>(null);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    Promise.all([
      getImports(),
      getSavedDashboards(),
      getReports(),
      getAvailableRange(),
    ]).then(([imp, dash, rep, rng]) => {
      setImports(imp);
      setDashboards(dash);
      setReports(rep);
      setRange(rng);
    }).finally(() => setLoading(false));
  }, []);

  const firstName = user?.fullName?.split(' ')[0] || '';
  const hasAnyData = imports.length > 0 || dashboards.length > 0 || reports.length > 0;

  // Últimos 3 de cada tipo para mostrar en preview
  const recentImports    = imports.slice(0, 3);
  const recentDashboards = dashboards.slice(0, 3);
  const recentReports    = reports.slice(0, 3);

  return (
    <div className="space-y-8">

      {/* ── Bienvenida ───────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">
            {firstName ? `Hola, ${firstName}` : 'Bienvenido'}
          </h1>
          <p className="text-muted-foreground">
            {tenant?.name && <span className="font-medium">{tenant.name}</span>}
            {range?.has_data && (
              <span className="ml-2 text-sm">
                · Datos disponibles desde{' '}
                <span className="font-medium">{range.date_from}</span>
                {' '}hasta{' '}
                <span className="font-medium">{range.date_to}</span>
                {' '}({range.total_orders.toLocaleString('es-ES')} pedidos)
              </span>
            )}
          </p>
        </div>

        {/* Acción principal según estado */}
        {!loading && (
          imports.length === 0 ? (
            <Link href="/app/upload">
              <Button className="gap-2">
                <Upload className="h-4 w-4" />
                Subir primeros datos
              </Button>
            </Link>
          ) : dashboards.length === 0 ? (
            <Link href="/app/dashboards">
              <Button className="gap-2">
                <LayoutDashboard className="h-4 w-4" />
                Crear primer dashboard
              </Button>
            </Link>
          ) : (
            <Link href="/app/dashboards">
              <Button variant="outline" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                Ver dashboards
              </Button>
            </Link>
          )
        )}
      </div>

      {/* ── Cómo funciona (solo si no hay datos aún) ─────────────── */}
      {!loading && !hasAnyData && (
        <div className="bg-gradient-to-br from-secondary/5 to-muted/50 border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BookOpen className="h-4 w-4 text-secondary" />
            <h2 className="font-semibold">¿Cómo funciona CommerceIQ?</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {STEPS.map(s => {
              const Icon = s.icon;
              return (
                <div key={s.step} className="bg-background rounded-lg p-4 border">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-secondary text-white text-xs font-bold">
                      {s.step}
                    </span>
                    <Icon className="h-4 w-4 text-secondary" />
                  </div>
                  <p className="font-medium text-sm mb-1">{s.title}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-3">{s.desc}</p>
                  <Link href={s.href}>
                    <Button size="sm" variant="outline" className="w-full text-xs">
                      {s.action}
                    </Button>
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Resumen numérico rápido (solo si hay datos) ───────────── */}
      {!loading && hasAnyData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: 'Imports',
              value: imports.length,
              icon: Database,
              href: '/app/imports',
              sub: `${imports.filter(i => i.status === 'completed').length} completados`,
            },
            {
              label: 'Dashboards',
              value: dashboards.length,
              icon: LayoutDashboard,
              href: '/app/dashboards',
              sub: dashboards[0]?.name || '—',
            },
            {
              label: 'Informes',
              value: reports.length,
              icon: FileText,
              href: '/app/reports',
              sub: reports[0] ? formatDate(reports[0].created_at) : '—',
            },
            {
              label: 'Pedidos analizados',
              value: range?.total_orders?.toLocaleString('es-ES') ?? '—',
              icon: TrendingUp,
              href: '/app/dashboards',
              sub: range?.has_data ? `${range.months_with_data} meses de datos` : 'Sin datos de pedidos',
            },
          ].map(card => {
            const Icon = card.icon;
            return (
              <Link key={card.label} href={card.href} className="block">
                <div className="bg-background border rounded-xl p-4 hover:shadow-card transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-muted-foreground">{card.label}</p>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <p className="text-2xl font-bold text-foreground">{card.value}</p>
                  <p className="text-xs text-muted-foreground mt-1 truncate">{card.sub}</p>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* ── 3 columnas: Imports · Dashboards · Informes ───────────── */}
      {!loading && (
        <div className="grid lg:grid-cols-3 gap-5">

          {/* Imports recientes */}
          <Section
            title="Imports"
            icon={Database}
            count={imports.length}
            href="/app/imports"
            emptyTitle="Sin imports"
            emptyDesc="Sube tu primer CSV o Excel para empezar."
            emptyAction={{ label: 'Subir datos', href: '/app/upload' }}
          >
            <div className="divide-y">
              {recentImports.map(imp => (
                <Link
                  key={imp.id}
                  href="/app/imports"
                  className="flex items-center gap-3 px-5 py-3 hover:bg-muted/30 transition-colors"
                >
                  <div className="bg-muted rounded p-1.5">
                    <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{imp.filename}</p>
                    <div className="flex items-center gap-2">
                      <StatusDot status={imp.status} />
                      <span className="text-xs text-muted-foreground">
                        {imp.valid_rows.toLocaleString('es-ES')} filas
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </Link>
              ))}
              {imports.length > 3 && (
                <div className="px-5 py-2 text-xs text-muted-foreground text-center">
                  +{imports.length - 3} imports más
                </div>
              )}
            </div>
          </Section>

          {/* Dashboards recientes */}
          <Section
            title="Dashboards"
            icon={LayoutDashboard}
            count={dashboards.length}
            href="/app/dashboards"
            emptyTitle="Sin dashboards"
            emptyDesc="Crea un dashboard combinando tus imports."
            emptyAction={{ label: 'Crear dashboard', href: '/app/dashboards' }}
          >
            <div className="divide-y">
              {recentDashboards.map(d => (
                <Link
                  key={d.id}
                  href={`/app/dashboards/${d.id}`}
                  className="flex items-center gap-3 px-5 py-3 hover:bg-muted/30 transition-colors"
                >
                  <div className="bg-muted rounded p-1.5">
                    <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{d.name}</p>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      {d.date_from && d.date_to ? (
                        <>
                          <Calendar className="h-3 w-3" />
                          {d.date_from} → {d.date_to}
                        </>
                      ) : (
                        <span>Todos los datos</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </Link>
              ))}
              {dashboards.length > 3 && (
                <div className="px-5 py-2 text-xs text-muted-foreground text-center">
                  +{dashboards.length - 3} dashboards más
                </div>
              )}
            </div>
          </Section>

          {/* Informes recientes */}
          <Section
            title="Informes guardados"
            icon={FileText}
            count={reports.length}
            href="/app/reports"
            emptyTitle="Sin informes"
            emptyDesc="Guarda un informe desde cualquier dashboard."
            emptyAction={{ label: 'Ver dashboards', href: '/app/dashboards' }}
          >
            <div className="divide-y">
              {recentReports.map(r => (
                <Link
                  key={r.id}
                  href="/app/reports"
                  className="flex items-center gap-3 px-5 py-3 hover:bg-muted/30 transition-colors"
                >
                  <div className="bg-muted rounded p-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-secondary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{r.dashboard_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(r.created_at)}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </Link>
              ))}
              {reports.length > 3 && (
                <div className="px-5 py-2 text-xs text-muted-foreground text-center">
                  +{reports.length - 3} informes más
                </div>
              )}
            </div>
          </Section>
        </div>
      )}

      {/* ── Accesos rápidos (siempre visibles si hay datos) ───────── */}
      {!loading && hasAnyData && (
        <div className="bg-gradient-to-br from-secondary/5 to-muted/50 border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-secondary" />
            <h2 className="font-semibold">Acciones rápidas</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {STEPS.map(s => {
              const Icon = s.icon;
              return (
                <Link key={s.step} href={s.href}>
                  <div className="flex items-center gap-3 bg-background rounded-lg p-3 border hover:shadow-card transition-shadow cursor-pointer">
                    <div className="bg-secondary/10 rounded-lg p-2">
                      <Icon className="h-4 w-4 text-secondary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{s.title}</p>
                      <p className="text-xs text-muted-foreground">{s.action}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground ml-auto" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Loading skeleton ──────────────────────────────────────── */}
      {loading && (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Array(4).fill(0).map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded-xl" />
            ))}
          </div>
          <div className="grid lg:grid-cols-3 gap-5">
            {Array(3).fill(0).map((_, i) => (
              <div key={i} className="h-48 bg-muted rounded-xl" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}