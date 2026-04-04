import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { getTutorials } from '@/lib/api';
import { Tutorial } from '@/lib/types';
import { PageLoading } from '@/components/shared';
import { BookOpen, Clock, ArrowRight } from 'lucide-react';

export function TutorialsPage() {
  const { t } = useTranslation();

  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTutorials = async () => {
      try {
        const data = await getTutorials();
        setTutorials(data);
      } finally {
        setLoading(false);
      }
    };
    loadTutorials();
  }, []);

  // Group tutorials by category
  const groupedTutorials = tutorials.reduce((acc, tutorial) => {
    if (!acc[tutorial.category]) {
      acc[tutorial.category] = [];
    }
    acc[tutorial.category].push(tutorial);
    return acc;
  }, {} as Record<string, Tutorial[]>);

  if (loading) {
    return <PageLoading message={t('tutorials.loading')} />;
  }

  return (
    <div className="py-16">
      <div className="container max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            {t('tutorials.title')}
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            {t('tutorials.subtitle')}
          </p>
        </div>

        <div className="space-y-12">
          {Object.entries(groupedTutorials).map(([category, categoryTutorials]) => (
            <div key={category}>
              <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-secondary" />
                {t(`tutorials.categories.${category}`, category)}
              </h2>

              <div className="grid gap-4">
                {categoryTutorials.map((tutorial) => (
                  <Link
                    key={tutorial.slug}
                    href={`/tutorials/${tutorial.slug}`}
                    className="group block bg-background rounded-lg border p-5 hover:shadow-card transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-medium text-foreground group-hover:text-secondary transition-colors mb-1">
                          {tutorial.title}
                        </h3>
                        <p className="text-sm text-muted-foreground mb-2">
                          {tutorial.description}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {t('tutorials.readTime', { time: tutorial.readTime })}
                        </div>
                      </div>
                      <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-secondary transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
