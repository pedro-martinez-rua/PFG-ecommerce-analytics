import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/hooks/useAuth';
import { Crown, UserCheck } from 'lucide-react';

type LocationState = { from?: { pathname?: string } };

const ROLE_OPTIONS = [
  {
    value: 'admin' as const,
    icon: Crown,
    title: 'Administrador',
    description: 'Crea la cuenta de tu empresa y gestiona el equipo.',
  },
  {
    value: 'analyst' as const,
    icon: UserCheck,
    title: 'Analista',
    description: 'Únete a una empresa existente introduciendo su nombre exacto.',
  },
];

export function RegisterPage() {
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
    role: 'admin' as 'admin' | 'analyst',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!formData.fullName.trim() || formData.fullName.trim().length < 2)
      e.fullName = 'El nombre debe tener al menos 2 caracteres.';
    if (!formData.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      e.email = 'Introduce un email válido.';
    if (!formData.companyName.trim())
      e.companyName = 'El nombre de la empresa es obligatorio.';
    if (!formData.password || formData.password.length < 8)
      e.password = 'La contraseña debe tener al menos 8 caracteres.';
    else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password))
      e.password = 'Debe incluir mayúsculas, minúsculas y números.';
    if (formData.password !== formData.confirmPassword)
      e.confirmPassword = 'Las contraseñas no coinciden.';
    if (!formData.acceptTerms)
      e.acceptTerms = 'Debes aceptar los términos para continuar.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!validate()) return;
    const result = await register(formData);
    if (result.success) navigate(fromPath, { replace: true });
  };

  const field = (id: string) => ({
    className: errors[id] ? 'border-destructive' : '',
  });

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">Crea tu cuenta</h1>
        <p className="text-muted-foreground">Empieza a analizar los datos de tu tienda en minutos</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-3 text-sm">
            {error}
          </div>
        )}

        {/* Role selector */}
        <div className="space-y-2">
          <Label>¿Cuál es tu rol?</Label>
          <div className="grid grid-cols-2 gap-3">
            {ROLE_OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const active = formData.role === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, role: opt.value })}
                  className={`flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition-all ${
                    active
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border hover:border-muted-foreground/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${active ? 'text-primary' : 'text-muted-foreground'}`} />
                    <span className={`text-sm font-semibold ${active ? 'text-primary' : 'text-foreground'}`}>
                      {opt.title}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-snug">{opt.description}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Full name */}
        <div className="space-y-1.5">
          <Label htmlFor="fullName">Nombre completo</Label>
          <Input
            id="fullName"
            placeholder="Juan Pérez"
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            autoComplete="name"
            {...field('fullName')}
          />
          {errors.fullName && <p className="text-xs text-destructive">{errors.fullName}</p>}
        </div>

        {/* Email */}
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="tu@ejemplo.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            autoComplete="email"
            {...field('email')}
          />
          {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
        </div>

        {/* Company name */}
        <div className="space-y-1.5">
          <Label htmlFor="companyName">
            Nombre de la empresa
          </Label>
          <Input
            id="companyName"
            placeholder={formData.role === 'admin' ? 'Tu tienda' : 'Nombre exacto de tu empresa'}
            value={formData.companyName}
            onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
            autoComplete="organization"
            {...field('companyName')}
          />
          {formData.role === 'analyst' && (
            <p className="text-xs text-muted-foreground">
              Debe coincidir exactamente con el nombre que registró el administrador.
            </p>
          )}
          {errors.companyName && <p className="text-xs text-destructive">{errors.companyName}</p>}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <Label htmlFor="password">Contraseña</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            autoComplete="new-password"
            {...field('password')}
          />
          {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
        </div>

        {/* Confirm password */}
        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirmar contraseña</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="••••••••"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            autoComplete="new-password"
            {...field('confirmPassword')}
          />
          {errors.confirmPassword && <p className="text-xs text-destructive">{errors.confirmPassword}</p>}
        </div>

        {/* Terms */}
        <div className="space-y-1">
          <div className="flex items-start gap-2">
            <Checkbox
              id="acceptTerms"
              checked={formData.acceptTerms}
              onCheckedChange={(v) => setFormData({ ...formData, acceptTerms: v === true })}
              className="mt-1"
            />
            <Label htmlFor="acceptTerms" className="text-sm text-muted-foreground font-normal leading-relaxed">
              Acepto los{' '}
              <a href="/terms" className="text-secondary hover:underline">Términos del servicio</a>
              {' '}y la{' '}
              <a href="/privacy" className="text-secondary hover:underline">Política de privacidad</a>
            </Label>
          </div>
          {errors.acceptTerms && <p className="text-xs text-destructive">{errors.acceptTerms}</p>}
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Creando cuenta...' : 'Crear cuenta'}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        ¿Ya tienes una cuenta?{' '}
        <Link href="/login" className="text-secondary hover:underline font-medium">
          Iniciar sesión
        </Link>
      </p>
    </div>
  );
}