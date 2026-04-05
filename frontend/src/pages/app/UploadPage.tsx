import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { uploadDataset } from '@/lib/api';
import { UploadImportResult } from '@/lib/types';
import {
  Upload,
  FileSpreadsheet,
  FileJson,
  File,
  CheckCircle2,
  AlertCircle,
  X,
  Info,
} from 'lucide-react';

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export function UploadPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [result, setResult] = useState<UploadImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const MAX_SIZE_MB = 50;
  const maxSizeBytes = MAX_SIZE_MB * 1024 * 1024;

  const validateFile = (file: File): string | null => {
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/json',
    ];

    const validExtensions = ['.csv', '.xlsx', '.xls', '.json'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
      return t('upload.validation.type');
    }

    if (file.size > maxSizeBytes) {
      return t('upload.validation.size', { max: MAX_SIZE_MB });
    }

    return null;
  };

  const handleFile = useCallback(
    async (selectedFile: File) => {
      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        return;
      }

      setFile(selectedFile);
      setError(null);
      setStatus('uploading');

      try {
        const uploadResult = await uploadDataset(selectedFile);
        setResult(uploadResult);
        setStatus('success');
      } catch (err) {
        const message = err instanceof Error ? err.message : t('upload.errors.uploadFailed');
        setError(message);
        setStatus('error');
      }
    },
    [t]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    },
    [handleFile]
  );

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setStatus('idle');
    setError(null);
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'json') return FileJson;
    if (ext === 'csv' || ext === 'xlsx' || ext === 'xls') return FileSpreadsheet;
    return File;
  };

  const completedOk = result?.status === 'completed';

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          {t('upload.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('upload.subtitle')}
        </p>
      </div>

      {status === 'success' && result && (
        <div className="bg-background rounded-lg border p-8 text-center">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${completedOk ? 'bg-success/10' : 'bg-warning/10'}`}>
            {completedOk ? (
              <CheckCircle2 className="h-8 w-8 text-success" />
            ) : (
              <AlertCircle className="h-8 w-8 text-warning" />
            )}
          </div>

          <h2 className="text-xl font-semibold text-foreground mb-2">
            {completedOk ? t('upload.success.title') : 'Archivo procesado con incidencias'}
          </h2>
          <p className="text-muted-foreground mb-6">
            {completedOk ? t('upload.success.subtitle') : (result.user_message || 'El fichero se ha cargado, pero algunas filas no han podido procesarse.')}
          </p>

          <div className="bg-muted rounded-lg p-4 mb-6 text-left">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Archivo</p>
                <p className="font-medium text-foreground">{result.filename}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Tipo detectado</p>
                <p className="font-medium text-foreground uppercase">{result.detected_type || 'unknown'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Filas totales</p>
                <p className="font-medium text-foreground">{result.total_rows.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Filas válidas</p>
                <p className="font-medium text-foreground">{result.valid_rows.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Filas inválidas</p>
                <p className="font-medium text-foreground">{result.invalid_rows.toLocaleString()}</p>
              </div>
              {result.main_reason && (
                <div>
                  <p className="text-muted-foreground">Motivo principal</p>
                  <p className="font-medium text-foreground">{result.main_reason}</p>
                </div>
              )}
            </div>
          </div>

          {(result.main_reason || result.suggestions.length > 0) && (
            <div className="mb-6 rounded-lg border bg-muted/40 p-4 text-left">
              {result.main_reason && (
                <div className="flex items-start gap-2 mb-3">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="font-medium text-foreground">{result.main_reason}</p>
                    {result.user_message && (
                      <p className="text-sm text-muted-foreground mt-1">{result.user_message}</p>
                    )}
                  </div>
                </div>
              )}
              {result.suggestions.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-foreground mb-2">Qué revisar</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {result.suggestions.slice(0, 3).map((suggestion) => (
                      <li key={suggestion}>• {suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 justify-center">
            <Button onClick={() => navigate('/app/imports')}>
              Ver imports
            </Button>
            <Button variant="outline" onClick={handleReset}>
              {t('upload.success.actions.uploadAnother')}
            </Button>
          </div>
        </div>
      )}

      {status !== 'success' && (
        <>
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-secondary bg-secondary/5'
                : 'border-border hover:border-muted-foreground/50'
            } ${status === 'uploading' ? 'opacity-50 pointer-events-none' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.json"
              onChange={handleInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={status === 'uploading'}
            />

            <div className="space-y-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-muted">
                <Upload className="h-6 w-6 text-muted-foreground" />
              </div>

              <div>
                <p className="text-lg font-medium text-foreground">
                  {status === 'uploading'
                    ? t('upload.dropzone.uploading')
                    : t('upload.dropzone.title')}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t('upload.dropzone.subtitle')}
                </p>
              </div>

              <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FileSpreadsheet className="h-3 w-3" />
                  {t('upload.formats.csv')}
                </span>
                <span className="flex items-center gap-1">
                  <FileSpreadsheet className="h-3 w-3" />
                  {t('upload.formats.excel')}
                </span>
                <span className="flex items-center gap-1">
                  <FileJson className="h-3 w-3" />
                  {t('upload.formats.json')}
                </span>
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-3 bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-destructive">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-destructive hover:text-destructive/80"
                aria-label={t('upload.errors.dismiss')}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {file && status === 'uploading' && (
            <div className="flex items-center gap-3 bg-muted rounded-lg p-4">
              {(() => {
                const Icon = getFileIcon(file.name);
                return <Icon className="h-8 w-8 text-muted-foreground" />;
              })()}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <div className="h-5 w-5 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          <div className="bg-muted/50 rounded-lg p-4">
            <h3 className="font-medium text-foreground mb-2">
              {t('upload.tips.title')}
            </h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• {t('upload.tips.items.headers')}</li>
              <li>• {t('upload.tips.items.dates')}</li>
              <li>• {t('upload.tips.items.numbers')}</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
