import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { getImports, deleteImport } from '@/lib/api';
import { BackendImport } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import {
  Upload, FileText, Calendar, Trash2,
  ChevronRight, CheckCircle2, AlertCircle,
  Clock, BarChart3, CheckSquare, Square
} from 'lucide-react';

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return (
    <span className="flex items-center gap-1 text-xs text-success">
      <CheckCircle2 className="h-3 w-3" /> Completado
    </span>
  );
  if (status === 'completed_with_errors') return (
    <span className="flex items-center gap-1 text-xs text-warning">
      <AlertCircle className="h-3 w-3" /> Con errores
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

export function DashboardsPage() {
  const navigate = useNavigate();

  const [imports, setImports]       = useState<BackendImport[]>([]);
  const [selected, setSelected]     = useState<Set<string>>(new Set());
  const [loading, setLoading]       = useState(true);
  const [deleting, setDeleting]     = useState<string | null>(null);
  const [selectMode, setSelectMode] = useState(false);

  useEffect(() => {
    getImports()
      .then(setImports)
      .finally(() => setLoading(false));
  }, []);

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === imports.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(imports.map(i => i.id)));
    }
  };

  const handleAnalyze = () => {
    // Calcular el rango de fechas combinado de los imports seleccionados
    const selectedImports = imports.filter(i => selected.has(i.id));
    const withDates = selectedImports.filter(i => i.data_date_from && i.data_date_to);

    if (withDates.length === 0) {
      // Sin fechas → analizar todo
      navigate('/app?period=all');
      return;
    }

    const dateFrom = withDates
      .map(i => i.data_date_from!)
      .sort()[0]; // fecha más antigua

    const dateTo = withDates
      .map(i => i.data_date_to!)
      .sort()
      .reverse()[0]; // fecha más reciente

    navigate(`/app?period=custom&date_from=${dateFrom}&date_to=${dateTo}`);
  };

  const handleDelete = async (importId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('¿Eliminar este import y todos sus datos?')) return;
    setDeleting(importId);
    try {
      await deleteImport(importId);
      setImports(prev => prev.filter(i => i.id !== importId));
      setSelected(prev => { const n = new Set(prev); n.delete(importId); return n; });
    } catch {
      alert('Error al eliminar. Inténtalo de nuevo.');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <PageLoading message="Cargando imports..." />;

  const allSelected = selected.size === imports.length && imports.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Imports</h1>
          <p className="text-muted-foreground">
            Selecciona uno o varios ficheros para analizarlos juntos.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectMode && imports.length > 0 && (
            <Button variant="outline" size="sm" onClick={toggleAll}>
              {allSelected ? 'Deseleccionar todo' : 'Seleccionar todo'}
            </Button>
          )}
          <Button
            variant={selectMode ? 'outline' : 'ghost'}
            size="sm"
            onClick={() => { setSelectMode(!selectMode); setSelected(new Set()); }}
          >
            {selectMode ? 'Cancelar' : 'Seleccionar'}
          </Button>
          <Link href="/app/upload">
            <Button className="gap-2">
              <Upload className="h-4 w-4" />
              Subir datos
            </Button>
          </Link>
        </div>
      </div>

      {/* Banner de selección activa */}
      {selectMode && selected.size > 0 && (
        <div className="flex items-center justify-between bg-secondary/10 border border-secondary/20 rounded-lg px-4 py-3">
          <p className="text-sm font-medium">
            {selected.size} {selected.size === 1 ? 'fichero seleccionado' : 'ficheros seleccionados'}
          </p>
          <Button onClick={handleAnalyze} className="gap-2" size="sm">
            <BarChart3 className="h-4 w-4" />
            Analizar selección
          </Button>
        </div>
      )}

      {imports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No tienes imports aún"
          description="Sube tu primer fichero CSV o Excel para empezar a analizar tus datos."
          action={{ label: 'Subir datos', onClick: () => navigate('/app/upload') }}
        />
      ) : (
        <div className="grid gap-3">
          {imports.map((imp) => {
            const isSelected = selected.has(imp.id);
            return (
              <div
                key={imp.id}
                className={`relative bg-background rounded-lg border p-5 transition-all ${
                  selectMode
                    ? 'cursor-pointer ' + (isSelected ? 'border-secondary ring-1 ring-secondary' : 'hover:border-muted-foreground')
                    : 'group hover:shadow-card'
                }`}
                onClick={selectMode ? () => toggleSelect(imp.id) : undefined}
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox en modo selección */}
                  {selectMode && (
                    <div className="mt-0.5 text-secondary">
                      {isSelected
                        ? <CheckSquare className="h-5 w-5" />
                        : <Square className="h-5 w-5 text-muted-foreground" />
                      }
                    </div>
                  )}

                  <div className="bg-muted rounded-lg p-2 mt-0.5">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {selectMode ? (
                        <h3 className="font-semibold text-foreground truncate">{imp.filename}</h3>
                      ) : (
                        <Link href={`/app/dashboards/${imp.id}`} className="flex-1">
                          <h3 className="font-semibold text-foreground group-hover:text-secondary transition-colors truncate">
                            {imp.filename}
                          </h3>
                        </Link>
                      )}
                      <StatusBadge status={imp.status} />
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                      <span className="capitalize bg-muted px-2 py-0.5 rounded">
                        {imp.detected_type || 'desconocido'}
                      </span>
                      <span>{imp.valid_rows.toLocaleString('es-ES')} filas</span>
                      {imp.data_date_from && imp.data_date_to && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {imp.data_date_from} → {imp.data_date_to}
                        </span>
                      )}
                      <span>
                        {new Date(imp.created_at).toLocaleDateString('es-ES', {
                          day: '2-digit', month: 'short', year: 'numeric'
                        })}
                      </span>
                    </div>
                  </div>

                  {!selectMode && (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => handleDelete(imp.id, e)}
                        disabled={deleting === imp.id}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-secondary transition-colors" />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}