import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  User,
  Building2,
  Shield,
  CreditCard,
  Users,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

import { authService } from '@/lib/auth'

export function ProfilePage() {
  const { t } = useTranslation();

  const { user, tenant, isAdmin } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [fullName, setFullName] = useState(user?.fullName || '')
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null)

  const handleSave = async () => {
    setProfileError(null)
    setProfileSuccess(null)

    const session = authService.getSession()
    const token = session?.token

    if (!token) {
      setProfileError('Sesión no válida. Inicia sesión de nuevo')
      return
    }

    const trimmedName = fullName.trim()

    if (!trimmedName) {
      setProfileError('El nombre completo es obligatorio')
      return
    }

    if (trimmedName.length < 2) {
      setProfileError('El nombre completo debe tener al menos 2 caracteres')
      return
    }

    setSaving(true)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: trimmedName,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        let errorMessage = 'No se pudo actualizar el perfil'

        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMessage = data.detail.map((err: any) => err.msg).join(' · ')
        }

        throw new Error(errorMessage)
      }

      profileError && setProfileError(null)
      setProfileSuccess('Perfil actualizado correctamente')
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        setProfileSuccess(null)
      }, 3000)

    } catch (error: any) {
      setProfileError(error.message || 'No se pudo actualizar el perfil')
    } finally {
      setSaving(false)
    }
  }

  const roleLabel =
    user?.role === 'admin'
      ? t('profile.roles.admin')
      : t('profile.roles.collaborator');

  const planLabel = tenant?.plan
    ? t(`profile.company.plans.${tenant.plan}`, {
        defaultValue: tenant.plan.charAt(0).toUpperCase() + tenant.plan.slice(1),
      })
    : t('profile.company.plans.free');

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmNewPassword, setConfirmNewPassword] = useState('')

  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)

  const handleChangePassword = async () => {
    setPasswordError(null)
    setPasswordSuccess(null)

    const session = authService.getSession()
    const token = session?.token

    if (!token) {
      setPasswordError('Sesión no válida. Inicia sesión de nuevo')
      return
    }

    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setPasswordError('Todos los campos son obligatorios')
      return
    }

    if (newPassword !== confirmNewPassword) {
      setPasswordError('Las contraseñas no coinciden')
      return
    }

    if (currentPassword === newPassword) {
      setPasswordError('La nueva contraseña no puede ser igual a la actual')
      return
    }

    // 👇 MÉTELO AQUÍ
    if (newPassword.length < 8) {
      setPasswordError('La nueva contraseña debe tener al menos 8 caracteres')
      return
    }

    if (!/[A-Z]/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos una mayúscula')
      return
    }

    if (!/[a-z]/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos una minúscula')
      return
    }

    if (!/\d/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos un número')
      return
    }

    setPasswordLoading(true)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/me/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmNewPassword,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        let errorMessage = 'No se pudo actualizar la contraseña'

        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMessage = data.detail.map((err: any) => err.msg).join(' · ')
        }

        throw new Error(errorMessage)
      }

      setPasswordSuccess('Contraseña actualizada correctamente')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmNewPassword('')
    } catch (error: any) {
      setPasswordError(error.message || 'No se pudo actualizar la contraseña')
    } finally {
      setPasswordLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-1">
          {t('profile.title')}
        </h1>
        <p className="text-muted-foreground">{t('profile.subtitle')}</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
          <TabsTrigger value="profile" className="gap-2">
            <User className="h-4 w-4" />
            <span className="hidden sm:inline">{t('profile.tabs.profile')}</span>
          </TabsTrigger>

          <TabsTrigger value="company" className="gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">{t('profile.tabs.company')}</span>
          </TabsTrigger>

          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">{t('profile.tabs.security')}</span>
          </TabsTrigger>

          <TabsTrigger value="billing" className="gap-2" disabled={!isAdmin}>
            <CreditCard className="h-4 w-4" />
            <span className="hidden sm:inline">{t('profile.tabs.billing')}</span>
          </TabsTrigger>

          <TabsTrigger value="members" className="gap-2" disabled={!isAdmin}>
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">{t('profile.tabs.members')}</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="bg-background rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              {t('profile.profileSection.title')}
            </h2>

            <div className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName">{t('profile.fields.fullName')}</Label>
                  <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)}/>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">{t('profile.fields.email')}</Label>
                  <Input id="email" type="email" defaultValue={user?.email} disabled />
                  <p className="text-xs text-muted-foreground">
                    {t('profile.profileSection.emailLocked')}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>{t('profile.fields.role')}</Label>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1.5 rounded-md text-sm font-medium ${
                      user?.role === 'admin'
                        ? 'bg-secondary/10 text-secondary'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {roleLabel}
                  </span>
                </div>
              </div>

              <div className="pt-4 flex items-center gap-3">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? t('profile.actions.saving') : t('profile.actions.saveChanges')}
                </Button>

                {saved && (
                  <span className="flex items-center gap-1 text-sm text-success">
                    <CheckCircle2 className="h-4 w-4" />
                    {t('profile.actions.saved')}
                  </span>
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Company Tab */}
        <TabsContent value="company" className="space-y-6">
          <div className="bg-background rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              {t('profile.companySection.title')}
            </h2>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="companyName">{t('profile.fields.companyName')}</Label>
                <Input id="companyName" defaultValue={tenant?.name} />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t('profile.companySection.currentPlan')}</Label>
                  <div className="px-3 py-2 rounded-md bg-muted text-sm">
                    {planLabel}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>{t('profile.companySection.dataRetention')}</Label>
                  <div className="px-3 py-2 rounded-md bg-muted text-sm">
                    {t('profile.companySection.retentionValue', { days: 90 })}
                  </div>
                </div>
              </div>

              <div className="pt-4">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? t('profile.actions.saving') : t('profile.actions.saveChanges')}
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <div className="bg-background rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              {t('profile.securitySection.changePassword')}
            </h2>

            <div className="space-y-4 max-w-md">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">
                  {t('profile.securitySection.currentPassword')}
                </Label>
                <Input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">
                  {t('profile.securitySection.newPassword')}
                </Label>
                <Input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmNewPassword">
                  {t('profile.securitySection.confirmNewPassword')}
                </Label>
                <Input
                  id="confirmNewPassword"
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>

              {passwordError && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {passwordError}
                </div>
              )}

              {passwordSuccess && (
                <div className="rounded-lg border border-success/20 bg-success/10 px-3 py-2 text-sm text-success">
                  {passwordSuccess}
                </div>
              )}

              <div className="pt-4">
                <Button onClick={handleChangePassword} disabled={passwordLoading}>
                  {passwordLoading
                    ? 'Actualizando...'
                    : t('profile.securitySection.updatePassword')}
                </Button>
              </div>
            </div>
          </div>

          <div className="bg-background rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              {t('profile.securitySection.activeSessions')}
            </h2>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
                <div>
                  <p className="font-medium text-foreground text-sm">
                    {t('profile.securitySection.currentSession')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t('profile.securitySection.lastActive', {
                      value: t('profile.securitySection.justNow'),
                    })}
                  </p>
                </div>
                <span className="text-xs bg-success/10 text-success px-2 py-1 rounded">
                  {t('profile.securitySection.active')}
                </span>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-6">
          {isAdmin ? (
            <div className="bg-background rounded-lg border p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                {t('profile.billingSection.title')}
              </h2>

              <div className="bg-muted/50 rounded-lg p-6 text-center">
                <AlertCircle className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  {t('profile.billingSection.comingSoon')}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {t('profile.billingSection.description')}
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-background rounded-lg border p-6">
              <p className="text-muted-foreground">
                {t('profile.billingSection.adminOnly')}
              </p>
            </div>
          )}
        </TabsContent>

        {/* Members Tab */}
        <TabsContent value="members" className="space-y-6">
          {isAdmin ? (
            <div className="bg-background rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-foreground">
                  {t('profile.membersSection.title')}
                </h2>
                <Button size="sm">{t('profile.membersSection.invite')}</Button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg border">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                      {user?.fullName?.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{user?.fullName}</p>
                      <p className="text-sm text-muted-foreground">{user?.email}</p>
                    </div>
                  </div>
                  <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded">
                    {t('profile.roles.admin')}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-background rounded-lg border p-6">
              <p className="text-muted-foreground">
                {t('profile.membersSection.adminOnly')}
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
