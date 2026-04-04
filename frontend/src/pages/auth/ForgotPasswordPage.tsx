import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { ArrowLeft, Mail } from 'lucide-react';

export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const { forgotPassword, loading } = useAuth();

  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const validate = () => {
    if (!email.trim()) {
      setError(t('forgotPassword.validation.emailRequired'));
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(t('forgotPassword.validation.emailInvalid'));
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    const result = await forgotPassword(email);
    if (result.success) {
      setSubmitted(true);
    }
  };

  const handleResend = async () => {
    await forgotPassword(email);
  };

  if (submitted) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-success/10 mb-4">
            <Mail className="h-6 w-6 text-success" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            {t('forgotPassword.success.title')}
          </h1>
          <p className="text-muted-foreground">
            {t('forgotPassword.success.description')}
            <br />
            <span className="font-medium text-foreground">{email}</span>
          </p>
        </div>

        <div className="space-y-3">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleResend}
            disabled={loading}
          >
            {loading
              ? t('forgotPassword.actions.sending')
              : t('forgotPassword.actions.resend')}
          </Button>

          <Link href="/login">
            <Button variant="ghost" className="w-full gap-2">
              <ArrowLeft className="h-4 w-4" />
              {t('forgotPassword.actions.backToLogin')}
            </Button>
          </Link>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          {t('forgotPassword.success.helper')}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">
          {t('forgotPassword.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('forgotPassword.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">{t('forgotPassword.form.email.label')}</Label>
          <Input
            id="email"
            type="email"
            placeholder={t('forgotPassword.form.email.placeholder')}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={error ? 'border-destructive' : ''}
            autoComplete="email"
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading
            ? t('forgotPassword.actions.sending')
            : t('forgotPassword.actions.sendLink')}
        </Button>
      </form>

      <Link href="/login">
        <Button variant="ghost" className="w-full gap-2">
          <ArrowLeft className="h-4 w-4" />
          {t('forgotPassword.actions.backToLogin')}
        </Button>
      </Link>
    </div>
  );
}
