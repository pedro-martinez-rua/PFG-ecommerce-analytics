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

// ─── Mapa canónico → etiqueta legible + descripción ──────────────────────────
const CANONICAL_FIELD_MAP: Record<string, { label: string; description: string }> = {
  // Pedido
  external_id:          { label: 'ID del pedido',               description: 'Identificador único del pedido (order_id, nº factura…)' },
  order_date:           { label: 'Fecha del pedido',            description: 'Fecha en que se realizó el pedido' },
  total_amount:         { label: 'Importe total',               description: 'Precio total antes de descuentos o devoluciones' },
  net_amount:           { label: 'Importe neto',                description: 'Importe tras aplicar descuentos' },
  discount_amount:      { label: 'Descuento aplicado',          description: 'Importe del descuento o cupón usado en el pedido' },
  shipping_cost:        { label: 'Gastos de envío',             description: 'Coste del envío cobrado al cliente' },
  refund_amount:        { label: 'Importe reembolsado',         description: 'Dinero devuelto al cliente por devoluciones' },
  cogs_amount:          { label: 'Coste del producto (COGS)',   description: 'Coste de fabricación o compra del producto vendido' },
  status:               { label: 'Estado del pedido',           description: 'Estado actual: completado, cancelado, devuelto…' },
  channel:              { label: 'Canal de venta',              description: 'Origen del pedido: web, marketplace, tienda física…' },
  payment_method:       { label: 'Método de pago',              description: 'Forma de pago: tarjeta, transferencia, PayPal…' },
  currency:             { label: 'Moneda',                      description: 'Código ISO de moneda (EUR, USD, GBP…)' },
  is_returned:          { label: 'Pedido devuelto',             description: 'Indica si el pedido fue devuelto (sí / no / true / false)' },
  delivery_days:        { label: 'Días de entrega',             description: 'Número de días desde el pedido hasta la entrega al cliente' },
  shipping_country:     { label: 'País de envío',               description: 'País de destino del pedido' },
  shipping_region:      { label: 'Región / Comunidad autónoma', description: 'Región, estado o comunidad autónoma de destino' },
  // Cliente
  customer_external_id: { label: 'ID del cliente',              description: 'Identificador único del cliente en tu sistema' },
  customer_email:       { label: 'Email del cliente',           description: 'Dirección de email del comprador' },
  customer_name:        { label: 'Nombre del cliente',          description: 'Nombre completo del comprador' },
  // Producto / línea
  product_external_id:  { label: 'ID del producto',             description: 'Identificador único del producto en tu catálogo' },
  product_name:         { label: 'Nombre del producto',         description: 'Nombre o descripción del artículo vendido' },
  sku:                  { label: 'SKU / Referencia',            description: 'Código interno del producto (SKU, barcode, EAN…)' },
  category:             { label: 'Categoría',                   description: 'Categoría o familia a la que pertenece el producto' },
  brand:                { label: 'Marca',                       description: 'Marca o fabricante del producto' },
  quantity:             { label: 'Cantidad vendida',            description: 'Número de unidades del producto en esta línea de pedido' },
  unit_price:           { label: 'Precio unitario',             description: 'Precio de venta de una unidad del producto' },
  unit_cost:            { label: 'Coste unitario',              description: 'Coste de compra o fabricación de una unidad' },
  line_total:           { label: 'Total de la línea',           description: 'Importe total de esta línea (precio × cantidad)' },
  // Marketing / sesión
  utm_source:           { label: 'Fuente de tráfico (UTM)',     description: 'Parámetro utm_source de la campaña de marketing' },
  utm_campaign:         { label: 'Campaña (UTM)',               description: 'Nombre de la campaña de marketing que originó el pedido' },
  device_type:          { label: 'Tipo de dispositivo',         description: 'Dispositivo del comprador: móvil, escritorio, tablet' },
  session_id:           { label: 'ID de sesión web',            description: 'Identificador de la sesión de navegación del usuario' },
};

// Grupos para <optgroup> — mejoran la navegabilidad del selector
const OPTION_GROUPS: { label: string; keys: string[] }[] = [
  {
    label: 'Datos del pedido',
    keys: [
      'external_id', 'order_date', 'total_amount', 'net_amount', 'discount_amount',
      'shipping_cost', 'refund_amount', 'cogs_amount', 'status', 'channel',
      'payment_method', 'currency', 'is_returned', 'delivery_days',
      'shipping_country', 'shipping_region',
    ],
  },
  {
    label: 'Datos del cliente',
    keys: ['customer_external_id', 'customer_email', 'customer_name'],
  },
  {
    label: 'Datos del producto / línea',
    keys: ['product_external_id', 'product_name', 'sku', 'category', 'brand', 'quantity', 'unit_price', 'unit_cost', 'line_total'],
  },
  {
    label: 'Marketing y sesión',
    keys: ['utm_source', 'utm_campaign', 'device_type', 'session_id'],
  },
];

function fieldLabel(key: string): string {
  return CANONICAL_FIELD_MAP[key]?.label ?? key;
}

function fieldDescription(key: string): string {
  return CANONICAL_FIELD_MAP[key]?.description ?? '';
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const cls = pct >= 90 ? 'text-success' : pct >= 70 ? 'text-warning' : 'text-destructive';
  return <span className={`text-xs font-semibold tabular-nums ${cls}`}>{pct}%</span>;
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed')            return <span className="flex items-center gap-1 text-xs text-success font-medium"><CheckCircle2 className="h-3 w-3" /> Completado</span>;
  if (status === 'needs_review')         return <span className="flex items-center gap-1 text-xs text-warning font-medium"><AlertCircle className="h-3 w-3" /> Revisar columnas</span>;
  if (status === 'failed')               return <span className="flex items-center gap-1 text-xs text-destructive font-medium"><AlertCircle className="h-3 w-3" /> Fallido</span>;
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
          {preview.warnings.map((w) => <div key={w}>• {w}</div>)}
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
  open, onOpenChange, imp, onApplied,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  imp: BackendImport | null;
  onApplied: () => void;
}) {
  const [loading, setLoading]           = useState(false);
  const [saving, setSaving]             = useState(false);
  const [suggestion, setSuggestion]     = useState<MappingSuggestionResponse | null>(null);
  const [assignments, setAssignments]   = useState<Record<string, string>>({});
  const [error, setError]               = useState('');

  useEffect(() => {
    if (!open || !imp) return;
    setLoading(true);
    setError('');
    getImportMappingSuggestion(imp.id)
      .then((data) => {
        setSuggestion(data);
        const next: Record<string, string> = {};
        data.suggestions.forEach((item) => { next[item.source_column] = item.canonical_field || ''; });
        setAssignments(next);
      })
      .catch((err) => setError(err.message || 'No se pudo cargar la propuesta de mapping.'))
      .finally(() => setLoading(false));
  }, [open, imp]);

  const requiredMissing = suggestion?.required_fields_missing ?? [];
  const currentlyMapped = useMemo(() => new Set(Object.values(assignments).filter(Boolean)), [assignments]);
  const stillMissing    = requiredMissing.filter((f) => !currentlyMapped.has(f));

  const handleSave = async () => {
    if (!imp || !suggestion) return;
    setSaving(true);
    setError('');
    try {
      await applyImportMapping(imp.id, {
        sheet_name:  suggestion.sheet_name,
        upload_type: suggestion.upload_type,
        assignments: Object.entries(assignments).map(([source_column, canonical_field]) => ({
          source_column,
          canonical_field: canonical_field || null,
        })),
      });
      onApplied();
      onOpenChange(false);
    } catch (err: any) {
      setError(err?.message || 'No se pudo aplicar el mapping.');
    } finally {
      setSaving(false);
    }
  };

  const TYPE_LABELS: Record<string, string> = {
    orders: 'Pedidos', order_lines: 'Líneas de pedido',
    customers: 'Clientes', products: 'Productos', mixed: 'Mixto',
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Revisar asignación de columnas</DialogTitle>
          <DialogDescription>
            Comprueba y corrige a qué campo del sistema corresponde cada columna de tu archivo.
            Los campos marcados como obligatorios deben estar asignados para poder procesar los datos correctamente.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="py-10 text-center text-sm text-muted-foreground">Analizando columnas del archivo...</div>
        ) : error ? (
          <div className="py-6 text-sm text-destructive">{error}</div>
        ) : suggestion ? (
          <div className="space-y-4">

            {/* Resumen de detección */}
            <div className="flex flex-wrap gap-4 rounded-lg border bg-muted/30 px-4 py-3 text-sm">
              <div>
                <span className="text-muted-foreground">Tipo detectado: </span>
                <span className="font-semibold text-foreground">{TYPE_LABELS[suggestion.upload_type] ?? suggestion.upload_type}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Confianza de detección: </span>
                <span className="font-semibold text-foreground">{Math.round(suggestion.confidence * 100)}%</span>
              </div>
              {!!suggestion.profiler_warnings.length && (
                <div className="w-full text-xs text-warning space-y-0.5">
                  {suggestion.profiler_warnings.map((w) => <div key={w}>⚠ {w}</div>)}
                </div>
              )}
              {!!stillMissing.length && (
                <div className="w-full text-xs text-destructive font-medium">
                  Campos obligatorios sin asignar: {stillMissing.map((f) => fieldLabel(f)).join(', ')}
                </div>
              )}
            </div>

            {/* Tabla de asignación */}
            <div className="max-h-[400px] overflow-auto rounded-lg border">
              <table className="w-full text-sm border-collapse">
                <thead className="bg-muted/60 sticky top-0 z-10 border-b">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide w-[32%]">
                      Columna en tu archivo
                    </th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Campo del sistema
                    </th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide w-20">
                      Confianza
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {suggestion.suggestions.map((item) => {
                    const selected   = assignments[item.source_column] ?? '';
                    const isMissing  = stillMissing.includes(item.source_column);
                    const isIgnored  = selected === '';

                    return (
                      <tr
                        key={item.source_column}
                        className={`border-t transition-colors ${isMissing ? 'bg-destructive/5' : 'hover:bg-muted/20'}`}
                      >
                        {/* Columna original */}
                        <td className="px-4 py-3 align-top">
                          <div className="flex flex-col gap-0.5">
                            <span className="font-medium text-foreground">{item.source_column}</span>
                            {item.inferred_type && (
                              <span className="text-xs text-muted-foreground">{item.inferred_type}</span>
                            )}
                          </div>
                        </td>

                        {/* Selector */}
                        <td className="px-4 py-3 align-top">
                          <div className="flex flex-col gap-1.5">
                            <select
                              value={selected}
                              onChange={(e) => setAssignments((prev) => ({ ...prev, [item.source_column]: e.target.value }))}
                              className={`w-full rounded-md border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors ${
                                isMissing
                                  ? 'border-destructive text-foreground'
                                  : isIgnored
                                    ? 'border-border text-muted-foreground'
                                    : 'border-input text-foreground'
                              }`}
                            >
                              <option value="">— Ignorar esta columna —</option>
                              {OPTION_GROUPS.map((group) => (
                                <optgroup key={group.label} label={group.label}>
                                  {group.keys.map((key) => (
                                    <option key={key} value={key}>{fieldLabel(key)}</option>
                                  ))}
                                </optgroup>
                              ))}
                            </select>

                            {/* Descripción del campo seleccionado */}
                            {selected && fieldDescription(selected) && (
                              <p className="text-xs text-muted-foreground leading-snug">
                                {fieldDescription(selected)}
                              </p>
                            )}

                            {/* Error si es obligatorio y no está asignado */}
                            {isMissing && (
                              <p className="text-xs text-destructive font-medium">
                                Campo obligatorio — debe estar asignado
                              </p>
                            )}
                          </div>
                        </td>

                        {/* Confianza */}
                        <td className="px-4 py-3 align-top">
                          <ConfidenceBadge value={item.confidence} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <p className="text-xs text-muted-foreground">
              Las filas en <span className="text-destructive font-medium">rojo</span> son campos obligatorios que el sistema necesita para procesar los datos.
              Las columnas asignadas como &ldquo;Ignorar&rdquo; no se importarán.
            </p>
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={handleSave} disabled={saving || loading || !!stillMissing.length}>
            {saving ? 'Aplicando...' : 'Aplicar y reprocesar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ImportCard({ imp, onDelete, onRefresh }: { imp: BackendImport; onDelete: () => void; onRefresh: () => void }) {
  const [showPreview, setShowPreview]           = useState(false);
  const [previewMode, setPreviewMode]           = useState<'raw' | 'normalized'>('raw');
  const [preview, setPreview]                   = useState<ImportPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading]     = useState(false);
  const [previewError, setPreviewError]         = useState('');
  const [deleting, setDeleting]                 = useState(false);
  const [diagnosis, setDiagnosis]               = useState<ImportDiagnosis | null>(null);
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [mappingOpen, setMappingOpen]           = useState(false);

  const loadDiagnosis = async () => {
    setDiagnosisLoading(true);
    try { setDiagnosis(await getImportDiagnosis(imp.id)); }
    catch { setDiagnosis(null); }
    finally { setDiagnosisLoading(false); }
  };

  const handleTogglePreview = async (mode: 'raw' | 'normalized' = previewMode) => {
    if (showPreview && previewMode === mode) { setShowPreview(false); return; }
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
      const toDelete   = impact.affected.filter(d => d.will_be_deleted);
      const incomplete = impact.affected.filter(d => !d.will_be_deleted);
      if (toDelete.length)   message += `\n\nDASHBOARDS QUE SE ELIMINARÁN:\n${toDelete.map(d => `  • ${d.dashboard_name}`).join('\n')}`;
      if (incomplete.length) message += `\n\nDASHBOARDS QUE QUEDARÁN INCOMPLETOS:\n${incomplete.map(d => `  • ${d.dashboard_name} (quedarán ${d.remaining} de ${d.total_imports} ficheros)`).join('\n')}`;
    }
    if (!confirm(message)) return;
    setDeleting(true);
    try { await deleteImport(imp.id); onDelete(); }
    catch { alert('Error al eliminar.'); setDeleting(false); }
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
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => handleTogglePreview('raw')}>
                <Eye className="h-3.5 w-3.5" />
                {showPreview && previewMode === 'raw' ? 'Ocultar' : 'Preview raw'}
                {showPreview && previewMode === 'raw' ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </Button>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => handleTogglePreview('normalized')}>Normalizada</Button>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs" onClick={() => { setMappingOpen(true); loadDiagnosis(); }}>
                <Wand2 className="h-3.5 w-3.5" /> Revisar columnas
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={handleDelete} disabled={deleting} title="Eliminar import">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        {showPreview && (
          <div className="border-t bg-muted/30">
            {previewLoading
              ? <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">Cargando previsualización...</div>
              : previewError
                ? <div className="py-6 px-5 text-sm text-destructive">{previewError}</div>
                : <PreviewTable preview={preview} />}
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
        <EmptyState
          icon={FileText}
          title="No tienes imports aún"
          description="Sube tu primer fichero CSV o Excel para empezar a analizar tus datos."
          action={{ label: 'Subir datos', onClick: () => navigate('/app/upload') }}
        />
      ) : (
        <div className="space-y-3">
          {imports.map((imp) => (
            <ImportCard
              key={imp.id}
              imp={imp}
              onRefresh={loadImports}
              onDelete={() => setImports((prev) => prev.filter((i) => i.id !== imp.id))}
            />
          ))}
        </div>
      )}
    </div>
  );
}