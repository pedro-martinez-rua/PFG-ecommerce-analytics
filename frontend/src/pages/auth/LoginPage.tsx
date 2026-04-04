import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';

type LocationState = {
  from?: { pathname?: string };
};

export function LoginPage() {
  const { t } = useTranslation();

  const { login, loading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const fromPath = (location.state as LocationState | null)?.from?.pathname || '/app';

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errors: Record<string, string> = {};

    if (!formData.email.trim()) {
      errors.email = t('login.validation.emailRequired');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = t('login.validation.emailInvalid');
    }

    if (!formData.password) {
      errors.password = t('login.validation.passwordRequired');
    } else if (formData.password.length < 6) {
      errors.password = t('login.validation.passwordMin', { min: 6 });
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) return;

    const result = await login(formData);
    if (result.success) {
      navigate(fromPath, { replace: true });
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">
          {t('login.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('login.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-3 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="email">{t('login.form.email.label')}</Label>
          <Input
            id="email"
            type="email"
            placeholder={t('login.form.email.placeholder')}
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className={validationErrors.email ? 'border-destructive' : ''}
            autoComplete="email"
          />
          {validationErrors.email && (
            <p className="text-sm text-destructive">{validationErrors.email}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">{t('login.form.password.label')}</Label>
            <Link href="/forgot-password" className="text-sm text-secondary hover:text-secondary-hover">
              {t('login.form.password.forgot')}
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            placeholder={t('login.form.password.placeholder')}
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className={validationErrors.password ? 'border-destructive' : ''}
            autoComplete="current-password"
          />
          {validationErrors.password && (
            <p className="text-sm text-destructive">{validationErrors.password}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? t('login.actions.signingIn') : t('login.actions.signIn')}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {t('login.footer.noAccount')}{' '}
        <Link href="/register" className="text-secondary hover:text-secondary-hover font-medium">
          {t('login.footer.createOne')}
        </Link>
      </p>

      <div className="text-center text-xs text-muted-foreground border-t pt-4">
        <p>{t('login.demo.title')}</p>
        <p>{t('login.demo.credentials')}</p>
      </div>
    </div>
  );
}
