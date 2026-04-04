import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { getFaqs } from '@/lib/api';
import { FAQ } from '@/lib/types';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { PageLoading } from '@/components/shared';

export function FaqPage() {
  const { t } = useTranslation();

  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFaqs = async () => {
      try {
        const data = await getFaqs();
        setFaqs(data);
      } finally {
        setLoading(false);
      }
    };
    loadFaqs();
  }, []);

  // Group FAQs by category
  const groupedFaqs = faqs.reduce((acc, faq) => {
    if (!acc[faq.category]) {
      acc[faq.category] = [];
    }
    acc[faq.category].push(faq);
    return acc;
  }, {} as Record<string, FAQ[]>);

  if (loading) {
    return <PageLoading message={t('faq.loading')} />;
  }

  return (
    <div className="py-16">
      <div className="container max-w-3xl">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            {t('faq.title')}
          </h1>
          <p className="text-muted-foreground text-lg">
            {t('faq.subtitle')}
          </p>
        </div>

        <div className="space-y-8">
          {Object.entries(groupedFaqs).map(([category, categoryFaqs]) => (
            <div key={category}>
              <h2 className="text-lg font-semibold text-foreground mb-4">
                {t(`faq.categories.${category}`, category)}
              </h2>

              <Accordion type="single" collapsible className="space-y-2">
                {categoryFaqs.map((faq) => (
                  <AccordionItem
                    key={faq.id}
                    value={faq.id}
                    className="border rounded-lg px-4"
                  >
                    <AccordionTrigger className="text-left hover:no-underline py-4">
                      <span className="font-medium text-foreground">
                        {faq.question}
                      </span>
                    </AccordionTrigger>
                    <AccordionContent className="pb-4 text-muted-foreground">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-muted-foreground mb-4">
            {t('faq.footer.text')}
          </p>
          <a
            href="#/contact"
            className="text-secondary hover:text-secondary-hover font-medium"
          >
            {t('faq.footer.link')} →
          </a>
        </div>
      </div>
    </div>
  );
}
