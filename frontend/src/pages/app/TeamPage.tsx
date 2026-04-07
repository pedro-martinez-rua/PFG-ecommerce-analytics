import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getTeamReports } from '@/lib/api';
import { TeamReport } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import {
  Users, FileText, Calendar, Sparkles,
  ChevronRight, Clock, User2
} from 'lucide-react';

const KPI_PILLS: Record<string, { label: string; format: 'currency' | 'number' | 'percentage' }> = {
  total_revenue:        { label: 'Revenue',   format: 'currency' },
  order_count:          { label: 'Pedidos',   format: 'number' },
  avg_order_value:      { label: 'AOV',       format: 'currency' },
  gross_margin_pct:     { label: 'Margen',    format: 'percentage' },
  repeat_purchase_rate: { label: 'Recompra',  format: 'percentage' },
};

function formatVal(value: number, format: string): string {
  if (format === 'currency') {
    return value >= 1_000_000
      ? `€${(value / 1_000_000).toFixed(1)}M`
      : value >= 1000
        ? `€${(value / 1000).toFixed(1)}k`
        : `€${value.toFixed(2)}`;
  }
  if (format === 'percentage') return `${value.toFixed(1)}%`;
  return value.toLocaleString('es-ES');
}

function TeamReportCard({ report }: { report: TeamReport }) {
  const kpiPills = Object.entries(KPI_PILLS)
    .map(([key, cfg]) => {
      const d = report.kpi_snapshot?.[key];
      if (!d || d.availability === 'missing' || d.value === null) return null;
      return { key, label: cfg.label, value: formatVal(d.value, cfg.format) };
    })
    .filter(Boolean) as { key: string; label: string; value: string }[];

  const creatorLabel = report.created_by_name || report.created_by_email || 'Miembro del equipo';

  return (
    <Link
      href={`/app/team/reports/${report.id}`}
      className="block bg-background border rounded-xl hover:shadow-card transition-shadow group"
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="bg-primary/10 rounded-lg p-2 mt-0.5 shrink-0">
              <FileText className="h-4 w-4 text-primary" />
            </div>

            <div className="flex-1 min-w-0">
              <p className="font-semibold text-foreground group-hover:text-secondary transition-colors truncate">
                {report.dashboard_name}
              </p>

              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mt-1">
                <span className="flex items-center gap-1">
                  <User2 className="h-3 w-3" />
                  {creatorLabel}
                </span>

                {report.date_from && report.date_to ? (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {report.date_from} → {report.date_to}
                  </span>
                ) : (
                  <span>Todos los datos</span>
                )}

                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(report.created_at).toLocaleDateString('es-ES', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>

                {report.insights && (
                  <span className="flex items-center gap-1 text-secondary">
                    <Sparkles className="h-3 w-3" />
                    Con análisis IA
                  </span>
                )}
              </div>
            </div>
          </div>

          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-secondary transition-colors shrink-0 mt-0.5" />
        </div>

        {kpiPills.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pl-11">
            {kpiPills.map(k => (
              <div key={k.key} className="bg-muted rounded-md px-2.5 py-1 text-xs">
                <span className="text-muted-foreground">{k.label}: </span>
                <span className="font-semibold text-foreground">{k.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

export function TeamPage() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const isAdmin = session?.user.role === 'admin';

  const [reports, setReports] = useState<TeamReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    getTeamReports()
      .then(setReports)
      .catch((err) => {
        setReports([]);
        setError(err instanceof Error ? err.message : 'Error al cargar informes del equipo');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading message="Cargando informes del equipo..." />;

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">{error}</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate('/app')}>
          Volver al resumen
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1 flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" />
            Equipo
          </h1>
          <p className="text-muted-foreground">
            Informes compartidos por los miembros de tu equipo.
          </p>
        </div>

        {isAdmin && (
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => navigate('/app/profile?tab=members')}
          >
            <Users className="h-4 w-4" />
            Gestionar equipo
          </Button>
        )}
      </div>

      {reports.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No hay informes compartidos aún"
          description='Los informes se compartirán aquí cuando alguien del equipo active la opción "Compartir con equipo" en un informe guardado.'
          action={{
            label: 'Ir a mis informes',
            onClick: () => navigate('/app/reports'),
          }}
        />
      ) : (
        <div className="space-y-3">
          {reports.map(report => (
            <TeamReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  );
}