import { useTranslation } from 'react-i18next';

export function PrivacyPage() {
  const { t } = useTranslation();

  return (
    <div className="py-16">
      <div className="container max-w-3xl space-y-8">
        <header>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            {t('privacy.title')}
          </h1>
          <p className="text-muted-foreground">
            {t('privacy.subtitle')}
          </p>
        </header>

        <section className="space-y-6 text-muted-foreground">
          {Array.from({ length: 13 }).map((_, i) => (
            <div key={i}>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                {t(`privacy.sections.${i + 1}.title`)}
              </h2>
              <p>{t(`privacy.sections.${i + 1}.content`)}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
