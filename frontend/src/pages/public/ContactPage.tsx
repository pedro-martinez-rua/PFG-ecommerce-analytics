import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { submitContactForm } from '@/lib/api';
import { Mail, Clock, CheckCircle2 } from 'lucide-react';

export function ContactPage() {
  const { t } = useTranslation();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = t('contact.validation.nameRequired');
    }

    if (!formData.email.trim()) {
      newErrors.email = t('contact.validation.emailRequired');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('contact.validation.emailInvalid');
    }

    if (!formData.message.trim()) {
      newErrors.message = t('contact.validation.messageRequired');
    } else if (formData.message.trim().length < 10) {
      newErrors.message = t('contact.validation.messageMin', { min: 10 });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await submitContactForm(formData);
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="py-16">
        <div className="container max-w-lg">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-success/10 mb-6">
              <CheckCircle2 className="h-8 w-8 text-success" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-4">
              {t('contact.success.title')}
            </h1>
            <p className="text-muted-foreground mb-8">
              {t('contact.success.description')}
            </p>
            <Button onClick={() => setSubmitted(false)} variant="outline">
              {t('contact.success.cta')}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-16">
      <div className="container max-w-2xl">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            {t('contact.title')}
          </h1>
          <p className="text-muted-foreground text-lg">
            {t('contact.subtitle')}
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-8">
          {/* Contact Info */}
          <div className="md:col-span-2 space-y-6">
            <div className="flex items-start gap-3">
              <div className="bg-muted rounded-lg p-2">
                <Mail className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-foreground">
                  {t('contact.info.emailLabel')}
                </p>
                <p className="text-sm text-muted-foreground">support@insightflow.io</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="bg-muted rounded-lg p-2">
                <Clock className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-foreground">
                  {t('contact.info.hoursLabel')}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t('contact.info.hoursDays')}
                  <br />
                  {t('contact.info.hoursTime')}
                </p>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div className="md:col-span-3">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name">{t('contact.form.name.label')}</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={errors.name ? 'border-destructive' : ''}
                  placeholder={t('contact.form.name.placeholder')}
                />
                {errors.name && (
                  <p className="text-sm text-destructive mt-1">{errors.name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="email">{t('contact.form.email.label')}</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={errors.email ? 'border-destructive' : ''}
                  placeholder={t('contact.form.email.placeholder')}
                />
                {errors.email && (
                  <p className="text-sm text-destructive mt-1">{errors.email}</p>
                )}
              </div>

              <div>
                <Label htmlFor="company">{t('contact.form.company.label')}</Label>
                <Input
                  id="company"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  placeholder={t('contact.form.company.placeholder')}
                />
              </div>

              <div>
                <Label htmlFor="message">{t('contact.form.message.label')}</Label>
                <Textarea
                  id="message"
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className={`min-h-[120px] ${errors.message ? 'border-destructive' : ''}`}
                  placeholder={t('contact.form.message.placeholder')}
                />
                {errors.message && (
                  <p className="text-sm text-destructive mt-1">{errors.message}</p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? t('contact.form.submit.loading') : t('contact.form.submit.default')}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
