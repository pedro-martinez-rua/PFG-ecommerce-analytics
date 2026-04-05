import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { BackendImport, ImportDiagnosis, ImportPreviewResponse, MappingSuggestionResponse } from '@/lib/types';
import { EmptyState, PageLoading } from '@/components/shared';
import {
  getImports,
  deleteImport,
  getImportPreview,
  getImportImpact,
  getImportDiagnosis,
  getImportMappingSuggestion,
  applyImportMapping,
} from '@/lib/api';
import {
  Upload, FileText, Calendar, Trash2,
  CheckCircle2, AlertCircle, Clock,
  ChevronDown, ChevronUp, Eye, Table2, Info, Wand2,
} from 'lucide-react';

const CANONICAL_OPTIONS = [
  '', 'external_id', 'order_date', 'total_amount', 'net_amount', 'discount_amount', 'status', 'channel',
  'shipping_country', 'currency', 'customer_external_id', 'customer_email', 'customer_name',
  'product_external_id', 'product_name', 'sku', 'category', 'brand', 'quantity', 'unit_price', 'unit_cost', 'line_total',
];

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return <span className="flex items-center gap-1 text-xs text-success font-medium"><CheckCircle2 className="h-3 w-3" /> Completado</span>;
  if (status === 'needs_review') return <span className="flex items-center gap-1 text-xs text-warning font-medium"><AlertCircle className="h-3 w-3" /> Revisar columnas</span>;
  if (status === 'failed') return <span className="flex items-center gap-1 text-xs text-destructive font-medium"><AlertCircle className="h-3 w-3" /> Fallido</span>;
  if (status === 'completed_with_errors') return <span className="flex items-center gap-1 text-xs text-warning font-medium"><AlertCircle className="h-3 w-3" /> Con errores</span>;
  return <span className="flex items-center gap-1 text-xs text-muted-foreground"><Clock className="h-3 w-3" /> Procesando</span>;
}

function PreviewTable({ preview }: { preview: ImportPreviewResponse | null }) {
  if (!preview || preview.rows.length === 0) {
    return <div className="flex items-center gap-2 py-6 px-5 text-sm text-muted-foreground"><Table2 className="h-4 w-4" /> No hay datos para previsualizar en este import.</div>;
  }
  return (
    <div>
      <div className="flex items-center gap-2 px-5 py-3 border-b">
        <Table2 className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground">Primeras {preview.rows.length} filas · {preview.columns.length} columnas · vista {preview.mode}</span>
      </div>
      {!!preview.warnings?.length && (
        <div className="px-5 py-3 border-b bg-muted/30 text-xs text-muted-foreground">
          {preview.warnings.map((warning) => <div key={warning}>• {warning}</div>)}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/50">
              {preview.columns.map((col) => <th key={col} className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">{col}</th>)}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                {preview.columns.map((col) => (
                  <td key={col} className="px-3 py-2 text-foreground whitespace-nowrap max-w-[220px] truncate" title={String(row[col] ?? '')}>
                    {row[col] === null || row[col] === undefined ? <span className="text-muted-foreground italic">—</span> : String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MappingDialog({
  open,
  onOpenChange,
  imp,
  onApplied,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  imp: BackendImport | null;
  onApplied: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suggestion, setSuggestion] = useState<MappingSuggestionResponse | null>(null);
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open || !imp) return;
    setLoading(true);
    setError('');
    getImportMappingSuggestion(imp.id)
      .then((data) => {
        setSuggestion(data);
        const next: Record<string, string> = {};
        data.suggestions.forEach((item) => {
          next[item.source_column] = item.canonical_field || '';
        });
        setAssignments(next);
      })
      .catch((err) => setError(err.message || 'No se pudo cargar la propuesta de mapping.'))
      .finally(() => setLoading(false));
  }, [open, imp]);

  const requiredMissing = suggestion?.required_fields_missing ?? [];
  const currentlyMapped = useMemo(() => new Set(Object.values(assignments).filter(Boolean)), [assignments]);
  const stillMissing = requiredMissing.filter((field) => !currentlyMapped.has(field));

  const handleSave = async () => {
    if (!imp || !suggestion) return;
    setSaving(true);
    setError('');
    try {
      await applyImportMapping(imp.id, {
        sheet_name: suggestion.sheet_name,
        upload_type: suggestion.upload_type,
        assignments: Object.entries(assignments).map(([source_column, canonical_field]) => ({ source_column, canonical_field: canonical_field || null })),
      });
      onApplied();
      onOpenChange(false);
    } catch (err: any) {
      setError(err?.message || 'No se pudo aplicar el mapping.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Revisar columnas</DialogTitle>
          <DialogDescription>Confirma o corrige la asignación de columnas antes de reprocesar el import.</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="py-10 text-sm text-muted-foreground">Cargando propuesta de mapping...</div>
        ) : error ? (
          <div className="py-6 text-sm text-destructive">{error}</div>
        ) : suggestion ? (
          <div className="space-y-4">
            <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground space-y-1">
              <div><strong className="text-foreground">Tipo detectado:</strong> {suggestion.upload_type} · confianza {Math.round(suggestion.confidence * 100)}%</div>
              {!!suggestion.profiler_warnings.length && suggestion.profiler_warnings.map((warning) => <div key={warning}>• {warning}</div>)}
              {!!stillMissing.length && <div className="text-warning">Campos obligatorios aún sin asignar: {stillMissing.join(', ')}</div>}
            </div>

            <div className="max-h-[420px] overflow-auto border rounded-md">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left">Columna original</th>
                    <th className="px-3 py-2 text-left">Campo destino</th>
                    <th className="px-3 py-2 text-left">Método</th>
                    <th className="px-3 py-2 text-left">Confianza</th>
                    <th className="px-3 py-2 text-left">Tipo inferido</th>
                  </tr>
                </thead>
                <tbody>
                  {suggestion.suggestions.map((item) => (
                    <tr key={item.source_column} className="border-t">
                      <td className="px-3 py-2 font-medium">{item.source_column}</td>
                      <td className="px-3 py-2">
                        <select className="w-full rounded border bg-background px-2 py-1" value={assignments[item.source_column] ?? ''} onChange={(e) => setAssignments((prev) => ({ ...prev, [item.source_column]: e.target.value }))}>
                          {CANONICAL_OPTIONS.map((option) => <option key={option || 'empty'} value={option}>{option || 'Ignorar columna'}</option>)}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">{item.method}</td>
                      <td className="px-3 py-2 text-muted-foreground">{Math.round(item.confidence * 100)}%</td>
                      <td className="px-3 py-2 text-muted-foreground">{item.inferred_type || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || loading || !!stillMissing.length}>{saving ? 'Aplicando...' : 'Aplicar y reprocesar'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ImportCard({ imp, onDelete, onRefresh }: { imp: BackendImport; onDelete: () => void; onRefresh: () => void }) {
  const [showPreview, setShowPreview] = useState(false);
  const [previewMode, setPreviewMode] = useState<'raw' | 'normalized'>('raw');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [diagnosis, setDiagnosis] = useState<ImportDiagnosis | null>(null);
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [mappingOpen, setMappingOpen] = useState(false);

  const loadDiagnosis = async () => {
    setDiagnosisLoading(true);
    try {
      setDiagnosis(await getImportDiagnosis(imp.id));
    } catch {
      setDiagnosis(null);
    } finally {
      setDiagnosisLoading(false);
    }
  };

  const handleTogglePreview = async (mode: 'raw' | 'normalized' = previewMode) => {
    const openingSame = showPreview && previewMode === mode;
    if (openingSame) {
      setShowPreview(false);
      return;
    }
    setPreviewMode(mode);
    setShowPreview(true);
    setPreviewLoading(true);
    setPreviewError('');
    try {
      const data = await getImportPreview(imp.id, mode);
      setPreview(data);
      if (!diagnosis && !diagnosisLoading) loadDiagnosis();
    } catch {
      setPreviewError('No se pudo cargar la previsualización.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = async () => {
    let impact;
    try { impact = await getImportImpact(imp.id); } catch { impact = null; }
    let message = `¿Eliminar "${imp.filename}"?\n\nSe eliminarán todos los datos asociados.`;
    if (impact?.has_impact) {
      const toDelete = impact.affected.filter(d => d.will_be_deleted);
      const incomplete = impact.affected.filter(d => !d.will_be_deleted);
      if (toDelete.length > 0) message += `\n\nDASHBOARDS QUE SE ELIMINARÁN:\n${toDelete.map(d => `  • ${d.dashboard_name}`).join('\n')}`;
      if (incomplete.length > 0) message += `\n\nDASHBOARDS QUE QUEDARÁN INCOMPLETOS:\n${incomplete.map(d => `  • ${d.dashboard_name} (quedarán ${d.remaining} de ${d.total_imports} ficheros)`).join('\n')}`;
    }
    if (!confirm(message)) return;
    setDeleting(true);
    try { await deleteImport(imp.id); onDelete(); } catch { alert('Error al eliminar.'); setDeleting(false); }
  };

  const showSummaryBlock = !!imp.main_reason || !!imp.user_message || diagnosisLoading || !!diagnosis;

  return (
    <>
      <div className="bg-background border rounded-lg overflow-hidden">
        <div className="p-5">
          <div className="flex items-start gap-3">
            <div className="bg-muted rounded-lg p-2 mt-0.5"><FileText className="h-4 w-4 text-muted-foreground" /></div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <p className="font-semibold text-foreground truncate">{imp.filename}</p>
                <StatusBadge status={imp.status} />
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <span className="capitalize bg-muted px-2 py-0.5 rounded font-medium">{imp.detected_type || 'desconocido'}</span>
                <span><strong className="text-foreground">{imp.valid_rows.toLocaleString('es-ES')}</strong> filas válidas</span>
                {(imp.invalid_rows > 0 || imp.status === 'needs_review') && <span className="text-warning">{imp.invalid_rows.toLocaleString('es-ES')} inválidas</span>}
                {imp.data_date_from && imp.data_date_to && <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{imp.data_date_from} → {imp.data_date_to}</span>}
                <span>{new Date(imp.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
              </div>
              {showSummaryBlock && (
                <div className="mt-3 rounded-md border bg-muted/30 p-3 text-sm">
                  {imp.main_reason && <div className="font-medium text-foreground flex items-center gap-2"><Info className="h-4 w-4 text-muted-foreground" />{imp.main_reason}</div>}
                  {imp.user_message && <p className="mt-1 text-muted-foreground">{imp.user_message}</p>}
                  {diagnosisLoading && <p className="mt-2 text-xs text-muted-foreground">Analizando incidencias del archivo...</p>}
                  {diagnosis?.suggestions?.length ? <ul className="mt-2 space-y-1 text-xs text-muted-foreground">{diagnosis.suggestions.slice(0, 3).map((s) => <li key={s}>• {s}</li>)}</ul> : null}
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => handleTogglePreview('raw')}><Eye className="h-3.5 w-3.5" />{showPreview && previewMode === 'raw' ? 'Ocultar' : 'Preview raw'}{showPreview && previewMode === 'raw' ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}</Button>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => handleTogglePreview('normalized')}>Normalizada</Button>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => { setMappingOpen(true); loadDiagnosis(); }}><Wand2 className="h-3.5 w-3.5" /> Revisar columnas</Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={handleDelete} disabled={deleting} title="Eliminar import"><Trash2 className="h-4 w-4" /></Button>
            </div>
          </div>
        </div>
        {showPreview && (
          <div className="border-t bg-muted/30">
            {previewLoading ? <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">Cargando previsualización...</div> : previewError ? <div className="py-6 px-5 text-sm text-destructive">{previewError}</div> : <PreviewTable preview={preview} />}
          </div>
        )}
      </div>
      <MappingDialog open={mappingOpen} onOpenChange={setMappingOpen} imp={imp} onApplied={onRefresh} />
    </>
  );
}

export function ImportsPage() {
  const navigate = useNavigate();
  const [imports, setImports] = useState<BackendImport[]>([]);
  const [loading, setLoading] = useState(true);

  const loadImports = () => {
    setLoading(true);
    getImports().then(setImports).finally(() => setLoading(false));
  };

  useEffect(() => { loadImports(); }, []);

  if (loading) return <PageLoading message="Cargando imports..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-1">Imports</h1>
          <p className="text-muted-foreground">Gestiona los ficheros que has subido. Usa la preview raw para ver el archivo real y la revisión manual para corregir columnas.</p>
        </div>
        <Link href="/app/upload"><Button className="gap-2"><Upload className="h-4 w-4" />Subir datos</Button></Link>
      </div>
      {imports.length === 0 ? (
        <EmptyState icon={FileText} title="No tienes imports aún" description="Sube tu primer fichero CSV o Excel para empezar a analizar tus datos." action={{ label: 'Subir datos', onClick: () => navigate('/app/upload') }} />
      ) : (
        <div className="space-y-3">
          {imports.map((imp) => <ImportCard key={imp.id} imp={imp} onRefresh={loadImports} onDelete={() => setImports((prev) => prev.filter((i) => i.id !== imp.id))} />)}
        </div>
      )}
    </div>
  );
}
