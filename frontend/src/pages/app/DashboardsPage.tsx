import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getImports, getSavedDashboards, createDashboard, deleteSavedDashboard } from '@/lib/api';
import { BackendImport, SavedDashboard } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import {
  Upload, FileText, Calendar, Trash2, ChevronRight,
  CheckCircle2, AlertCircle, Clock, BarChart3,
  CheckSquare, Square, Plus, X, LayoutDashboard
} from 'lucide-react';

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return (
    <span className="flex items-center gap-1 text-xs text-success">
      <CheckCircle2 className="h-3 w-3" /> Completado
    </span>
  );
  if (status === 'failed') return (
    <span className="flex items-center gap-1 text-xs text-destructive">
      <AlertCircle className="h-3 w-3" /> Fallido
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      <Clock className="h-3 w-3" /> Procesando
    </span>
  );
}

type ViewMode = 'dashboards' | 'new';

export function DashboardsPage() {
  const navigate = useNavigate();

  // Estado principal
  const [view, setView]               = useState<ViewMode>('dashboards');
  const [dashboards, setDashboards]   = useState<SavedDashboard[]>([]);
  const [imports, setImports]         = useState<BackendImport[]>([]);
  const [loading, setLoading]         = useState(true);
  const [deleting, setDeleting]       = useState<string | null>(null);

  // Estado del flujo de creación
  const [selected, setSelected]       = useState<Set<string>>(new Set());
  const [dashboardName, setDashboardName] = useState('');
  const [creating, setCreating]       = useState(false);
  const [nameError, setNameError]     = useState('');

  // Helper para saber si un dashboard tiene datos
  const activeImportIds = new Set(imports.map(i => i.id));
  const isDashboardEmpty = (d: SavedDashboard) => {
    if (!d.import_ids || d.import_ids.length === 0) return false;
    return d.import_ids.every(id => !activeImportIds.has(id));
  };
  
  useEffect(() => {
    Promise.all([getSavedDashboards(), getImports()])
      .then(([d, i]) => { setDashboards(d); setImports(i); })
      .finally(() => setLoading(false));
  }, []);

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleCreate = async () => {
    if (!dashboardName.trim()) {
      setNameError('El nombre es obligatorio');
      return;
    }
    setNameError('');
    setCreating(true);

    try {
      // Calcular rango de fechas combinado de los imports seleccionados
      const selectedImports = imports.filter(i => selected.has(i.id));
      const withDates = selectedImports.filter(i => i.data_date_from && i.data_date_to);

      let dateFrom: string | undefined;
      let dateTo: string | undefined;

      if (withDates.length > 0) {
        dateFrom = withDates.map(i => i.data_date_from!).sort()[0];
        dateTo   = withDates.map(i => i.data_date_to!).sort().reverse()[0];
      }

      const created = await createDashboard({
        name: dashboardName.trim(),
        date_from: dateFrom,
        date_to:   dateTo,
        import_ids: Array.from(selected),
      });

      setDashboards(prev => [created, ...prev]);
      setView('dashboards');
      setSelected(new Set());
      setDashboardName('');

      // Navegar directamente al dashboard creado
      navigate(`/app/dashboards/${created.id}`);

    } catch {
      alert('Error al crear el dashboard. Inténtalo de nuevo.');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('¿Eliminar este dashboard?')) return;
    setDeleting(id);
    try {
      await deleteSavedDashboard(id);
      setDashboards(prev => prev.filter(d => d.id !== id));
    } catch {
      alert('Error al eliminar. Inténtalo de nuevo.');
    } finally {
      setDeleting(null);
    }
  };

  const handleCancelCreate = () => {
    setView('dashboards');
    setSelected(new Set());
    setDashboardName('');
    setNameError('');
  };

  if (loading) return <PageLoading message="Cargando dashboards..." />;

  // ── Vista: crear nuevo dashboard ──────────────────────────────────────
  if (view === 'new') {
    return (
      <div className="space-y-6 max-w-2xl">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleCancelCreate}>
            <X className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Nuevo dashboard</h1>
            <p className="text-muted-foreground text-sm">
              Selecciona los ficheros que quieres analizar y ponle un nombre.
            </p>
          </div>
        </div>

        {/* Nombre */}
        <div className="bg-background border rounded-lg p-5 space-y-3">
          <label className="text-sm font-medium">Nombre del dashboard</label>
          <Input
            placeholder="Ej: Ventas Q1 2024, Análisis anual..."
            value={dashboardName}
            onChange={e => { setDashboardName(e.target.value); setNameError(''); }}
            className={nameError ? 'border-destructive' : ''}
            autoFocus
          />
          {nameError && <p className="text-xs text-destructive">{nameError}</p>}
        </div>

        {/* Selección de imports */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              Selecciona los ficheros a incluir
              {selected.size > 0 && (
                <span className="ml-2 text-secondary">({selected.size} seleccionados)</span>
              )}
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelected(
                selected.size === imports.length
                  ? new Set()
                  : new Set(imports.map(i => i.id))
              )}
            >
              {selected.size === imports.length ? 'Deseleccionar todo' : 'Seleccionar todo'}
            </Button>
          </div>

          {imports.length === 0 ? (
            <div className="border rounded-lg p-6 text-center text-muted-foreground text-sm">
              No tienes ficheros subidos.{' '}
              <Link href="/app/upload" className="text-secondary underline">Sube uno primero.</Link>
            </div>
          ) : (
            <div className="space-y-2">
              {imports.map(imp => {
                const isSelected = selected.has(imp.id);
                return (
                  <div
                    key={imp.id}
                    onClick={() => toggleSelect(imp.id)}
                    className={`flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-secondary bg-secondary/5 ring-1 ring-secondary'
                        : 'hover:border-muted-foreground'
                    }`}
                  >
                    <div className="text-secondary">
                      {isSelected
                        ? <CheckSquare className="h-5 w-5" />
                        : <Square className="h-5 w-5 text-muted-foreground" />
                      }
                    </div>
                    <div className="bg-muted rounded p-1.5">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{imp.filename}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span className="capitalize bg-muted px-1.5 py-0.5 rounded">
                          {imp.detected_type}
                        </span>
                        <span>{imp.valid_rows.toLocaleString('es-ES')} filas</span>
                        {imp.data_date_from && imp.data_date_to && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {imp.data_date_from} → {imp.data_date_to}
                          </span>
                        )}
                      </div>
                    </div>
                    <StatusBadge status={imp.status} />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Botones */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            onClick={handleCreate}
            disabled={creating || !dashboardName.trim()}
            className="gap-2"
          >
            <BarChart3 className="h-4 w-4" />
            {creating ? 'Creando...' : 'Crear dashboard'}
          </Button>
          <Button variant="outline" onClick={handleCancelCreate}>
            Cancelar
          </Button>
        </div>
      </div>
    );
  }

  // ── Vista: lista de dashboards ────────────────────────────────────────
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Dashboards</h1>
          <p className="text-muted-foreground">
            Crea dashboards combinando distintos ficheros de datos.
          </p>
        </div>
        <Button onClick={() => setView('new')} className="gap-2">
          <Plus className="h-4 w-4" />
          Nuevo dashboard
        </Button>
      </div>

      {dashboards.length === 0 ? (
        <EmptyState
          icon={LayoutDashboard}
          title="No tienes dashboards aún"
          description="Crea tu primer dashboard seleccionando los ficheros que quieres analizar."
          action={{ label: 'Crear dashboard', onClick: () => setView('new') }}
        />
      ) : (
        <div className="grid gap-3">
          {dashboards.map(d => {
          const isEmpty = isDashboardEmpty(d);
          return (
            <div
              key={d.id}
              className={`bg-background rounded-lg border transition-shadow ${
                isEmpty ? 'opacity-60 border-dashed' : 'hover:shadow-card group'
              }`}
            >
              <div className="flex items-center justify-between gap-4 p-5">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`rounded-lg p-2 ${isEmpty ? 'bg-muted' : 'bg-muted'}`}>
                    <LayoutDashboard className={`h-4 w-4 ${isEmpty ? 'text-muted-foreground' : 'text-muted-foreground'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`font-semibold truncate ${isEmpty ? 'text-muted-foreground' : 'text-foreground group-hover:text-secondary transition-colors'}`}>
                        {d.name}
                      </p>
                      {isEmpty && (
                        <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded font-medium shrink-0">
                          Sin datos
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                      {isEmpty ? (
                        <span className="text-destructive">Los imports asociados han sido eliminados</span>
                      ) : d.date_from && d.date_to ? (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {d.date_from} → {d.date_to}
                        </span>
                      ) : (
                        <span>Todos los datos</span>
                      )}
                      <span>{new Date(d.created_at).toLocaleDateString('es-ES', {
                        day: '2-digit', month: 'short', year: 'numeric'
                      })}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={e => handleDelete(d.id, e)}
                    disabled={deleting === d.id}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>

                  {/* Solo navegar si tiene datos */}
                  {!isEmpty ? (
                    <Link href={`/app/dashboards/${d.id}`}>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-secondary transition-colors" />
                    </Link>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-destructive hover:text-destructive gap-1"
                      onClick={e => handleDelete(d.id, e)}
                      disabled={deleting === d.id}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Eliminar
                    </Button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}