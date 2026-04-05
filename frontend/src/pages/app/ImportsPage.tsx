import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { BackendImport, ImportDiagnosis } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import {
  getImports,
  deleteImport,
  getImportPreview,
  getImportImpact,
  getImportDiagnosis,
} from '@/lib/api';
import {
  Upload, FileText, Calendar, Trash2,
  CheckCircle2, AlertCircle, Clock,
  ChevronDown, ChevronUp, Eye, Table2, Info,
} from 'lucide-react';

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return (
    <span className="flex items-center gap-1 text-xs text-success font-medium">
      <CheckCircle2 className="h-3 w-3" /> Completado
    </span>
  );
  if (status === 'failed') return (
    <span className="flex items-center gap-1 text-xs text-destructive font-medium">
      <AlertCircle className="h-3 w-3" /> Fallido
    </span>
  );
  if (status === 'completed_with_errors') return (
    <span className="flex items-center gap-1 text-xs text-warning font-medium">
      <AlertCircle className="h-3 w-3" /> Con errores
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      <Clock className="h-3 w-3" /> Procesando
    </span>
  );
}

interface PreviewData {
  columns: string[];
  rows: Record<string, any>[];
}

function ImportCard({
  imp,
  onDelete,
}: {
  imp: BackendImport;
  onDelete: () => void;
}) {
  const [showPreview, setShowPreview] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [diagnosis, setDiagnosis] = useState<ImportDiagnosis | null>(null);
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);

  useEffect(() => {
    if (imp.status === 'completed' && imp.invalid_rows === 0 && imp.detected_type !== 'unknown') {
      return;
    }

    let cancelled = false;
    setDiagnosisLoading(true);
    getImportDiagnosis(imp.id)
      .then((data) => {
        if (!cancelled) setDiagnosis(data);
      })
      .catch(() => {
        if (!cancelled) setDiagnosis(null);
      })
      .finally(() => {
        if (!cancelled) setDiagnosisLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [imp.id, imp.status, imp.invalid_rows, imp.detected_type]);

  const handleTogglePreview = async () => {
    if (showPreview) {
      setShowPreview(false);
      return;
    }
    setShowPreview(true);
    if (preview) return;

    setPreviewLoading(true);
    setPreviewError('');
    try {
      const data = await getImportPreview(imp.id);
      setPreview(data);
    } catch {
      setPreviewError('No se pudo cargar la previsualización.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = async () => {
    let impact;
    try {
      impact = await getImportImpact(imp.id);
    } catch {
      impact = null;
    }

    let message = `¿Eliminar "${imp.filename}"?\n\nSe eliminarán todos los datos asociados.`;

    if (impact?.has_impact) {
      const toDelete = impact.affected.filter(d => d.will_be_deleted);
      const incomplete = impact.affected.filter(d => !d.will_be_deleted);

      if (toDelete.length > 0) {
        message += `\n\nDASHBOARDS QUE SE ELIMINARÁN (quedarán sin datos):\n`;
        message += toDelete.map(d => `  • ${d.dashboard_name}`).join('\n');
      }
      if (incomplete.length > 0) {
        message += `\n\nDASHBOARDS QUE QUEDARÁN INCOMPLETOS:\n`;
        message += incomplete.map(d =>
          `  • ${d.dashboard_name} (quedarán ${d.remaining} de ${d.total_imports} ficheros)`
        ).join('\n');
      }
      message += '\n\nLos informes guardados NO se eliminarán.';
    }

    if (!confirm(message)) return;

    setDeleting(true);
    try {
      await deleteImport(imp.id);
      onDelete();
    } catch {
      alert('Error al eliminar. Inténtalo de nuevo.');
      setDeleting(false);
    }
  };

  const showDiagnosisBlock = diagnosisLoading || !!diagnosis?.main_reason || !!diagnosis?.top_errors?.length || !!diagnosis?.top_warnings?.length;

  return (
    <div className="bg-background border rounded-lg overflow-hidden">
      <div className="p-5">
        <div className="flex items-start gap-3">
          <div className="bg-muted rounded-lg p-2 mt-0.5">
            <FileText className="h-4 w-4 text-muted-foreground" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <p className="font-semibold text-foreground truncate">{imp.filename}</p>
              <StatusBadge status={imp.status} />
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="capitalize bg-muted px-2 py-0.5 rounded font-medium">
                {imp.detected_type || 'desconocido'}
              </span>
              <span>
                <strong className="text-foreground">{imp.valid_rows.toLocaleString('es-ES')}</strong> filas válidas
              </span>
              {imp.invalid_rows > 0 && (
                <span className="text-warning">
                  {imp.invalid_rows.toLocaleString('es-ES')} inválidas
                </span>
              )}
              {imp.data_date_from && imp.data_date_to && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {imp.data_date_from} → {imp.data_date_to}
                </span>
              )}
              <span>
                {new Date(imp.created_at).toLocaleDateString('es-ES', {
                  day: '2-digit', month: 'short', year: 'numeric',
                })}
              </span>
            </div>

            {showDiagnosisBlock && (
              <div className="mt-3 rounded-md border bg-muted/30 p-3 text-sm">
                {diagnosisLoading ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <div className="animate-spin h-4 w-4 border-2 border-secondary border-t-transparent rounded-full" />
                    Analizando incidencias del archivo...
                  </div>
                ) : diagnosis ? (
                  <div className="space-y-3">
                    {(diagnosis.main_reason || diagnosis.user_message) && (
                      <div>
                        <div className="flex items-center gap-2 font-medium text-foreground">
                          <Info className="h-4 w-4 text-muted-foreground" />
                          {diagnosis.main_reason || 'Diagnóstico'}
                        </div>
                        {diagnosis.user_message && (
                          <p className="mt-1 text-muted-foreground">{diagnosis.user_message}</p>
                        )}
                      </div>
                    )}

                    {diagnosis.top_errors.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                          Motivos principales
                        </p>
                        <div className="space-y-1.5">
                          {diagnosis.top_errors.slice(0, 3).map((item) => (
                            <div key={`${item.code}-${item.title}`} className="text-sm text-foreground">
                              <span className="font-medium">{item.title}</span>
                              {typeof item.count === 'number' ? ` · ${item.count.toLocaleString('es-ES')}` : ''}
                              {item.description ? ` — ${item.description}` : ''}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {diagnosis.top_warnings.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                          Advertencias
                        </p>
                        <div className="space-y-1.5">
                          {diagnosis.top_warnings.slice(0, 2).map((item) => (
                            <div key={`${item.code}-${item.title}`} className="text-sm text-muted-foreground">
                              <span className="font-medium text-foreground">{item.title}</span>
                              {typeof item.count === 'number' ? ` · ${item.count.toLocaleString('es-ES')}` : ''}
                              {item.description ? ` — ${item.description}` : ''}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {diagnosis.suggestions.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                          Qué revisar
                        </p>
                        <ul className="space-y-1 text-sm text-muted-foreground">
                          {diagnosis.suggestions.slice(0, 3).map((suggestion) => (
                            <li key={suggestion}>• {suggestion}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs"
              onClick={handleTogglePreview}
            >
              <Eye className="h-3.5 w-3.5" />
              {showPreview ? 'Ocultar' : 'Previsualizar'}
              {showPreview
                ? <ChevronUp className="h-3.5 w-3.5" />
                : <ChevronDown className="h-3.5 w-3.5" />
              }
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
              onClick={handleDelete}
              disabled={deleting}
              title="Eliminar import"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {showPreview && (
        <div className="border-t bg-muted/30">
          {previewLoading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-secondary border-t-transparent rounded-full" />
              Cargando previsualización...
            </div>
          ) : previewError ? (
            <div className="flex items-center gap-2 py-6 px-5 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {previewError}
            </div>
          ) : preview && preview.rows.length > 0 ? (
            <div>
              <div className="flex items-center gap-2 px-5 py-3 border-b">
                <Table2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground">
                  Primeras {preview.rows.length} filas · {preview.columns.length} columnas
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      {preview.columns.map(col => (
                        <th
                          key={col}
                          className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                        {preview.columns.map(col => (
                          <td
                            key={col}
                            className="px-3 py-2 text-foreground whitespace-nowrap max-w-[200px] truncate"
                            title={String(row[col] ?? '')}
                          >
                            {row[col] === null || row[col] === undefined
                              ? <span className="text-muted-foreground italic">—</span>
                              : String(row[col])
                            }
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 py-6 px-5 text-sm text-muted-foreground">
              <Table2 className="h-4 w-4" />
              No hay datos para previsualizar en este import.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ImportsPage() {
  const navigate = useNavigate();
  const [imports, setImports] = useState<BackendImport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getImports()
      .then(setImports)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading message="Cargando imports..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Imports</h1>
          <p className="text-muted-foreground">
            Gestiona los ficheros que has subido. Pulsa "Previsualizar" para ver las primeras 10 filas.
          </p>
        </div>
        <Link href="/app/upload">
          <Button className="gap-2">
            <Upload className="h-4 w-4" />
            Subir datos
          </Button>
        </Link>
      </div>

      {imports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No tienes imports aún"
          description="Sube tu primer fichero CSV o Excel para empezar a analizar tus datos."
          action={{ label: 'Subir datos', onClick: () => navigate('/app/upload') }}
        />
      ) : (
        <div className="space-y-3">
          {imports.map(imp => (
            <ImportCard
              key={imp.id}
              imp={imp}
              onDelete={() => setImports(prev => prev.filter(i => i.id !== imp.id))}
            />
          ))}
        </div>
      )}
    </div>
  );
}
