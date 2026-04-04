import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import {
  BarChart3,
  Upload,
  Zap,
  Shield,
  LineChart,
  FileSpreadsheet,
  ArrowRight,
  Sparkles,
  Users,
  TrendingUp,
  Clock,
} from 'lucide-react';

export function HomePage() {
  const { t } = useTranslation();

  const features = [
    { icon: Upload, key: 'upload' },
    { icon: Zap, key: 'dashboards' },
    { icon: Sparkles, key: 'ai' },
    { icon: Shield, key: 'security' },
    { icon: LineChart, key: 'realtime' },
    { icon: FileSpreadsheet, key: 'export' },
  ];

  const benefits = [
    { icon: TrendingUp, key: 'decisions' },
    { icon: Clock, key: 'time' },
    { icon: Users, key: 'teams' },
  ];

  const howItWorks = ['step1', 'step2', 'step3'];

  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="py-20 lg:py-28">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-secondary/10 text-secondary px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Sparkles className="h-4 w-4" />
              {t('home.hero.badge')}
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground mb-6">
              {t('home.hero.title')}
              <br />
              <span className="text-secondary">{t('home.hero.highlight')}</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              {t('home.hero.description')}
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="gap-2 min-w-[160px]">
                  {t('home.hero.ctaPrimary')}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="min-w-[160px]">
                  {t('home.hero.ctaSecondary')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="py-16 bg-card border-y">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl md:text-3xl font-semibold text-foreground mb-4">
              {t('home.problem.title')}
            </h2>
            <p className="text-muted-foreground text-lg">
              {t('home.problem.description')}
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-semibold text-foreground mb-4">
              {t('home.howItWorks.title')}
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {t('home.howItWorks.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {howItWorks.map((step, index) => (
              <div key={step} className="text-center">
                <div className="text-4xl font-bold text-blue-900 text-secondary/20 mb-4">
                  {`0${index + 1}`}
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {t(`home.howItWorks.steps.${step}.title`)}
                </h3>
                <p className="text-muted-foreground text-sm">
                  {t(`home.howItWorks.steps.${step}.description`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-card border-y">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-semibold text-foreground mb-4">
              {t('home.benefits.title')}
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {t('home.benefits.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {benefits.map(({ icon: Icon, key }) => (
              <div key={key} className="bg-background rounded-lg border p-6">
                <div className="bg-secondary/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {t(`home.benefits.items.${key}.title`)}
                </h3>
                <p className="text-muted-foreground text-sm">
                  {t(`home.benefits.items.${key}.description`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-semibold text-foreground mb-4">
              {t('home.features.title')}
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {t('home.features.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(({ icon: Icon, key }) => (
              <div key={key} className="p-6 rounded-lg border bg-background">
                <div className="bg-muted w-10 h-10 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="h-5 w-5 text-secondary text-muted-foreground" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">
                  {t(`home.features.items.${key}.title`)}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t(`home.features.items.${key}.description`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="container">
          <div className="bg-primary rounded-2xl p-8 md:p-12 text-center">
            <h2 className="text-2xl md:text-3xl font-semibold text-primary-foreground mb-4">
              {t('home.cta.title')}
            </h2>
            <p className="text-primary-foreground/80 mb-8 max-w-xl mx-auto">
              {t('home.cta.description')}
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" variant="secondary" className="gap-2 min-w-[160px]">
                  {t('home.cta.primary')}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/contact">
                <Button
                  size="lg"
                  variant="outline"
                  className="
                    min-w-[160px]
                    border-primary-foreground/20
                    text-blue-900
                    hover:text-blue-900
                    hover:bg-blue-50
                  "
                >
                  {t('home.cta.secondary')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
