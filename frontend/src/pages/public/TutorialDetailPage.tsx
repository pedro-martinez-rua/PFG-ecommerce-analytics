import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { getTutorial } from '@/lib/api';
import { Tutorial } from '@/lib/types';
import { PageLoading, EmptyState } from '@/components/shared';
import { ArrowLeft, Clock, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function TutorialDetailPage() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();

  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadTutorial = async () => {
      if (!slug) {
        if (mounted) {
          setTutorial(null);
          setLoading(false);
        }
        return;
      }

      try {
        const data = await getTutorial(slug);
        if (mounted) setTutorial(data);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    setLoading(true);
    loadTutorial();

    return () => {
      mounted = false;
    };
  }, [slug]);

  if (loading) {
    return <PageLoading message={t('tutorialDetail.loading')} />;
  }

  if (!tutorial) {
    return (
      <div className="py-16">
        <div className="container max-w-3xl">
          <EmptyState
            icon={BookOpen}
            title={t('tutorialDetail.notFound.title')}
            description={t('tutorialDetail.notFound.description')}
            action={{
              label: t('tutorialDetail.notFound.action'),
              onClick: () => {},
            }}
          />

          <div className="mt-6 flex justify-center">
            <Link href="/tutorials">
              <Button variant="secondary">
                {t('tutorialDetail.notFound.action')}
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-16">
      <div className="container max-w-3xl">
        <Link href="/tutorials">
          <Button variant="ghost" size="sm" className="gap-2 mb-6">
            <ArrowLeft className="h-4 w-4" />
            {t('tutorialDetail.back')}
          </Button>
        </Link>

        <article>
          <header className="mb-8">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <span className="bg-secondary/10 text-secondary px-2 py-0.5 rounded text-xs font-medium">
                {t(`tutorials.categories.${tutorial.category}`, tutorial.category)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {t('tutorials.readTime', { time: tutorial.readTime })}
              </span>
            </div>

            <h1 className="text-3xl font-bold text-foreground mb-4">
              {tutorial.title}
            </h1>
            <p className="text-lg text-muted-foreground">
              {tutorial.description}
            </p>
          </header>

          <div className="prose prose-slate max-w-none">
            {tutorial.content.split('\n').map((line, index) => {
              if (line.startsWith('# ')) {
                return (
                  <h1 key={index} className="text-2xl font-bold mt-8 mb-4">
                    {line.slice(2)}
                  </h1>
                );
              }
              if (line.startsWith('## ')) {
                return (
                  <h2 key={index} className="text-xl font-semibold mt-6 mb-3">
                    {line.slice(3)}
                  </h2>
                );
              }
              if (line.startsWith('### ')) {
                return (
                  <h3 key={index} className="text-lg font-medium mt-4 mb-2">
                    {line.slice(4)}
                  </h3>
                );
              }
              if (line.startsWith('- ') || line.match(/^\d\. /)) {
                return (
                  <li key={index} className="text-muted-foreground ml-4">
                    {line.replace(/^(- |\d\. )/, '')}
                  </li>
                );
              }
              if (line.trim() === '') {
                return <br key={index} />;
              }
              return (
                <p key={index} className="text-muted-foreground mb-2">
                  {line}
                </p>
              );
            })}
          </div>
        </article>

        <div className="mt-12 pt-8 border-t">
          <p className="text-sm text-muted-foreground mb-4">
            {t('tutorialDetail.feedback.question')}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              {t('tutorialDetail.feedback.positive')}
            </Button>
            <Button variant="outline" size="sm">
              {t('tutorialDetail.feedback.negative')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
