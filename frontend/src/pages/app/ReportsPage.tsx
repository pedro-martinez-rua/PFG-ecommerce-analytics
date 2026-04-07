import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getReports, deleteReport, shareReport } from '@/lib/api';
import { SavedReport } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import {
  FileText, Calendar, Trash2, Sparkles,
  TrendingUp, ChevronRight, Clock, Users, Share2
} from 'lucide-react';

const KPI_SUMMARY_KEYS: Record<string, { label: string; format: 'currency' | 'number' | 'percentage' }> = {
  total_revenue:        { label: 'Revenue',   format: 'currency' },
  order_count:          { label: 'Pedidos',   format: 'number' },
  avg_order_value:      { label: 'AOV',       format: 'currency' },
  gross_margin_pct:     { label: 'Margen',    format: 'percentage' },
  repeat_purchase_rate: { label: 'Recompra',  format: 'percentage' },
  unique_customers:     { label: 'Clientes',  format: 'number' },
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

function ReportCard({
  report,
  onDelete,
  onShareToggle,
}: {
  report: SavedReport;
  onDelete: () => void;
  onShareToggle: (shared: boolean) => void;
}) {
  const [deleting, setDeleting]     = useState(false);
  const [sharing, setSharing]       = useState(false);
  const shared = report.shared_with_team;

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('¿Eliminar este informe? Esta acción no se puede deshacer.')) return;
    setDeleting(true);
    try {
      await deleteReport(report.id);
      onDelete();
    } catch {
      alert('Error al eliminar. Inténtalo de nuevo.');
      setDeleting(false);
    }
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSharing(true);
    try {
      await shareReport(report.id, !shared);
      onShareToggle(!shared);
    } catch {
      alert('Error al cambiar el estado de compartición.');
    } finally {
      setSharing(false);
    }
  };

  const kpiPills = Object.entries(KPI_SUMMARY_KEYS)
    .map(([key, cfg]) => {
      const d = report.kpi_snapshot?.[key];
      if (!d || d.availability === 'missing' || d.value === null) return null;
      return { key, label: cfg.label, value: formatVal(d.value, cfg.format) };
    })
    .filter(Boolean) as { key: string; label: string; value: string }[];

  return (
    <Link
      href={`/app/reports/${report.id}`}
      className="block bg-background border rounded-xl hover:shadow-card transition-shadow group"
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="bg-secondary/10 rounded-lg p-2 mt-0.5 shrink-0">
              <FileText className="h-4 w-4 text-secondary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="font-semibold text-foreground group-hover:text-secondary transition-colors truncate">
                  {report.dashboard_name}
                </p>
                {shared && (
                  <span className="inline-flex items-center gap-1 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                    <Users className="h-3 w-3" />
                    Compartido
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mt-1">
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
                    day: '2-digit', month: 'short', year: 'numeric',
                    hour: '2-digit', minute: '2-digit',
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

          {/* Acciones */}
          <div className="flex items-center gap-1 shrink-0">
            {/* Compartir */}
            <Button
              variant="ghost"
              size="icon"
              className={`h-8 w-8 transition-all ${
                shared
                  ? 'text-primary opacity-100'
                  : 'text-muted-foreground opacity-0 group-hover:opacity-100'
              }`}
              onClick={handleShare}
              disabled={sharing}
              title={shared ? 'Dejar de compartir con el equipo' : 'Compartir con el equipo'}
            >
              <Share2 className="h-4 w-4" />
            </Button>
            {/* Eliminar */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleDelete}
              disabled={deleting}
              title="Eliminar informe"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-secondary transition-colors" />
          </div>
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

export function ReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getReports()
      .then(setReports)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading message="Cargando informes..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Informes guardados</h1>
          <p className="text-muted-foreground">
            Snapshots de tus dashboards con KPIs, gráficas y análisis de IA incluidos.
          </p>
        </div>
        <Button variant="outline" className="gap-2" onClick={() => navigate('/app/dashboards')}>
          <TrendingUp className="h-4 w-4" />
          Ir a dashboards
        </Button>
      </div>

      {reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No tienes informes aún"
          description='Abre un dashboard y pulsa "Guardar informe" para crear un snapshot con KPIs, gráficas y análisis de IA.'
          action={{ label: 'Ir a dashboards', onClick: () => navigate('/app/dashboards') }}
        />
      ) : (
        <div className="space-y-3">
          {reports.map(report => (
            <ReportCard
              key={report.id}
              report={report}
              onDelete={() => setReports(prev => prev.filter(r => r.id !== report.id))}
              onShareToggle={(shared) =>
                setReports(prev =>
                  prev.map(r => r.id === report.id ? { ...r, shared_with_team: shared } : r)
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}