import { Insight } from '@/lib/types';
import { X, Lightbulb, AlertTriangle, TrendingUp, Target, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AiInsightsPanelProps {
  insights?: Insight[];
  rawText?: string;     
  loading?: boolean;
  onClose: () => void;
}

export function AiInsightsPanel({ insights = [], rawText, loading, onClose }: AiInsightsPanelProps) {
  const getInsightIcon = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':  return Lightbulb;
      case 'warning':      return AlertTriangle;
      case 'trend':        return TrendingUp;
      case 'recommendation': return Target;
      default:             return Lightbulb;
    }
  };

  const getInsightColor = (type: Insight['type']) => {
    switch (type) {
      case 'opportunity':    return 'bg-success/10 text-success';
      case 'warning':        return 'bg-warning/10 text-warning';
      case 'trend':          return 'bg-secondary/10 text-secondary';
      case 'recommendation': return 'bg-muted text-foreground';
      default:               return 'bg-muted text-muted-foreground';
    }
  };

  // Renderiza el texto markdown de Groq con formato básico
  const renderMarkdownText = (text: string) => {
    return text.split('\n').map((line, i) => {
      // Cabeceras en negrita: **Texto**
      if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <h3 key={i} className="font-semibold text-foreground mt-4 mb-2 first:mt-0">
            {line.replace(/\*\*/g, '')}
          </h3>
        );
      }
      // Ítems de lista
      if (line.startsWith('* ') || line.match(/^\d+\. /)) {
        const content = line.replace(/^\* /, '').replace(/^\d+\. /, '');
        const parts = content.split(/(\*\*[^*]+\*\*)/g);
        return (
          <p key={i} className="mb-2 border-l border-border pl-4 text-sm leading-relaxed text-muted-foreground">
            {parts.map((part, j) =>
              part.startsWith('**') ? (
                <strong key={j} className="text-foreground font-medium">
                  {part.replace(/\*\*/g, '')}
                </strong>
              ) : part
            )}
          </p>
        );
      }
      // Líneas vacías
      if (line.trim() === '') return <div key={i} className="h-1" />;
      // Texto normal — detectar **negritas** inline
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return (
        <p key={i} className="text-sm text-muted-foreground mb-1 leading-relaxed">
          {parts.map((part, j) =>
            part.startsWith('**') ? (
              <strong key={j} className="text-foreground font-medium">
                {part.replace(/\*\*/g, '')}
              </strong>
            ) : part
          )}
        </p>
      );
    });
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg animate-slide-in-right border-l bg-card/95 shadow-2xl backdrop-blur-xl">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between border-b bg-muted/20 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary/10">
              <Sparkles className="h-5 w-5 text-secondary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Análisis IA</h2>
              <p className="text-sm text-muted-foreground">Interpretación automática de tus datos</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-5 py-4">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-5 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-20 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : rawText ? (
            // Modo texto Groq
            <div className="prose prose-sm max-w-none">
              {renderMarkdownText(rawText)}
            </div>
          ) : insights.length > 0 ? (
            // Modo Insight[] (compatibilidad)
            <div className="space-y-4">
              {insights.map((insight) => {
                const Icon = getInsightIcon(insight.type);
                const colorClasses = getInsightColor(insight.type);
                return (
                  <div key={insight.id} className="rounded-2xl border bg-background p-4 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className={`rounded-xl p-2 ${colorClasses}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-foreground mb-1">{insight.title}</h3>
                        <p className="text-sm text-muted-foreground leading-relaxed">{insight.content}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Lightbulb className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay análisis disponible.</p>
              <p className="text-sm text-muted-foreground">Sube datos para generar insights automáticos.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-4">
          <p className="text-xs text-muted-foreground text-center">
            Los insights generados por IA son orientativos. Contrástalo con tu propio criterio.
          </p>
        </div>
      </div>
    </div>
  );
}