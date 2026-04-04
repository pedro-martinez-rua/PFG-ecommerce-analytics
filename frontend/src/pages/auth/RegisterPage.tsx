import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/hooks/useAuth';

type LocationState = {
  from?: { pathname?: string };
};

export function RegisterPage() {
  const { t } = useTranslation();

  const { register, loading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const fromPath = (location.state as LocationState | null)?.from?.pathname || '/app';

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    companyName: '',
    acceptTerms: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errors: Record<string, string> = {};

    if (!formData.fullName.trim()) {
      errors.fullName = t('register.validation.fullNameRequired');
    } else if (formData.fullName.trim().length < 2) {
      errors.fullName = t('register.validation.fullNameInvalid');
    }

    if (!formData.email.trim()) {
      errors.email = t('register.validation.emailRequired');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = t('register.validation.emailInvalid');
    }

    if (!formData.password) {
      errors.password = t('register.validation.passwordRequired');
    } else if (formData.password.length < 8) {
      errors.password = t('register.validation.passwordMin', { min: 8 });
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      errors.password = t('register.validation.passwordComplexity');
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = t('register.validation.confirmPasswordRequired');
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = t('register.validation.passwordsNoMatch');
    }

    if (!formData.companyName.trim()) {
      errors.companyName = t('register.validation.companyRequired');
    }

    if (!formData.acceptTerms) {
      errors.acceptTerms = t('register.validation.termsRequired');
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) return;

    const result = await register(formData);
    if (result.success) {
      navigate(fromPath, { replace: true });
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">
          {t('register.title')}
        </h1>
        <p className="text-muted-foreground">
          {t('register.subtitle')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-3 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="fullName">{t('register.form.fullName.label')}</Label>
          <Input
            id="fullName"
            placeholder={t('register.form.fullName.placeholder')}
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            className={validationErrors.fullName ? 'border-destructive' : ''}
            autoComplete="name"
          />
          {validationErrors.fullName && (
            <p className="text-sm text-destructive">{validationErrors.fullName}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">{t('register.form.email.label')}</Label>
          <Input
            id="email"
            type="email"
            placeholder={t('register.form.email.placeholder')}
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
          <Label htmlFor="companyName">{t('register.form.company.label')}</Label>
          <Input
            id="companyName"
            placeholder={t('register.form.company.placeholder')}
            value={formData.companyName}
            onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
            className={validationErrors.companyName ? 'border-destructive' : ''}
            autoComplete="organization"
          />
          {validationErrors.companyName && (
            <p className="text-sm text-destructive">{validationErrors.companyName}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">{t('register.form.password.label')}</Label>
          <Input
            id="password"
            type="password"
            placeholder={t('register.form.password.placeholder')}
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className={validationErrors.password ? 'border-destructive' : ''}
            autoComplete="new-password"
          />
          {validationErrors.password && (
            <p className="text-sm text-destructive">{validationErrors.password}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword">{t('register.form.confirmPassword.label')}</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder={t('register.form.confirmPassword.placeholder')}
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            className={validationErrors.confirmPassword ? 'border-destructive' : ''}
            autoComplete="new-password"
          />
          {validationErrors.confirmPassword && (
            <p className="text-sm text-destructive">{validationErrors.confirmPassword}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <Checkbox
              id="acceptTerms"
              checked={formData.acceptTerms}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, acceptTerms: checked === true })
              }
              className="mt-1"
            />
            <Label
              htmlFor="acceptTerms"
              className="text-sm text-muted-foreground font-normal leading-relaxed"
            >
              {t('register.form.terms.prefix')}{' '}
              <a href="#" className="text-secondary hover:text-secondary-hover">
                {t('register.form.terms.termsOfService')}
              </a>{' '}
              {t('register.form.terms.middle')}{' '}
              <a href="#" className="text-secondary hover:text-secondary-hover">
                {t('register.form.terms.privacyPolicy')}
              </a>
            </Label>
          </div>

          {validationErrors.acceptTerms && (
            <p className="text-sm text-destructive">{validationErrors.acceptTerms}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? t('register.actions.creating') : t('register.actions.create')}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {t('register.footer.haveAccount')}{' '}
        <Link href="/login" className="text-secondary hover:text-secondary-hover font-medium">
          {t('register.footer.signIn')}
        </Link>
      </p>
    </div>
  );
}
