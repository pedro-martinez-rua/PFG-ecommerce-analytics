import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/lib/auth';
import { getTeamMembers, toggleTeamAccess, removeMember } from '@/lib/api';
import type { TeamMember } from '@/lib/types';
import {
  User,
  Building2,
  Shield,
  CreditCard,
  Users,
  CheckCircle2,
  AlertCircle,
  Trash2,
} from 'lucide-react';

type TabKey = 'profile' | 'company' | 'security' | 'billing' | 'members';

const TAB_LABELS: Record<TabKey, string> = {
  profile: 'Perfil',
  company: 'Empresa',
  security: 'Seguridad',
  billing: 'Facturación',
  members: 'Miembros',
};

function TabButton({
  active,
  onClick,
  icon: Icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition-colors border',
        active
          ? 'bg-background text-foreground border-border shadow-sm'
          : 'bg-transparent text-muted-foreground border-transparent hover:text-foreground hover:bg-muted/50',
      ].join(' ')}
    >
      <Icon className="h-4 w-4" />
      {children}
    </button>
  );
}

function SectionCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-background border rounded-2xl p-6 space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

function Field({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">{label}</label>
      {children}
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

export function ProfilePage() {
  const { user, tenant, isAdmin, updateMe } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const requestedTab = (searchParams.get('tab') || 'profile') as TabKey;
  const safeTab: TabKey =
    requestedTab === 'members' && !isAdmin ? 'profile' : requestedTab;

  const [activeTab, setActiveTab] = useState<TabKey>(safeTab);

  useEffect(() => {
    if (requestedTab !== safeTab) {
      const next = new URLSearchParams(searchParams);
      if (safeTab === 'profile') next.delete('tab');
      else next.set('tab', safeTab);
      setSearchParams(next, { replace: true });
    }
    setActiveTab(safeTab);
  }, [requestedTab, safeTab, searchParams, setSearchParams]);

  const changeTab = (tab: TabKey) => {
    const next = new URLSearchParams(searchParams);
    if (tab === 'profile') next.delete('tab');
    else next.set('tab', tab);
    setSearchParams(next, { replace: true });
    setActiveTab(tab);
  };

  // ── Perfil ────────────────────────────────────────────────────────
  const [fullName, setFullName] = useState(user?.fullName || '');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  useEffect(() => {
    setFullName(user?.fullName || '');
  }, [user?.fullName]);

  const handleSaveProfile = async () => {
    setProfileError(null);
    setProfileSaved(false);
    setSavingProfile(true);

    const cleaned = fullName.trim();
    if (!cleaned) {
      setSavingProfile(false);
      setProfileError('El nombre no puede estar vacío.');
      return;
    }

    const result = await updateMe({ full_name: cleaned });

    setSavingProfile(false);

    if (!result.success) {
      setProfileError(result.error || 'No se pudo actualizar el perfil');
      return;
    }

    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 3000);
  };

  // ── Seguridad ─────────────────────────────────────────────────────
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);

  const handleChangePassword = async () => {
    setPasswordError(null);
    setPasswordSuccess(null);

    const token = authService.getSession()?.token;

    if (!token) {
      setPasswordError('Sesión no válida. Inicia sesión de nuevo.');
      return;
    }

    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setPasswordError('Todos los campos son obligatorios.');
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setPasswordError('Las contraseñas no coinciden.');
      return;
    }

    if (currentPassword === newPassword) {
      setPasswordError('La nueva contraseña no puede ser igual a la actual.');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('La nueva contraseña debe tener al menos 8 caracteres.');
      return;
    }

    if (!/[A-Z]/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos una mayúscula.');
      return;
    }

    if (!/[a-z]/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos una minúscula.');
      return;
    }

    if (!/\d/.test(newPassword)) {
      setPasswordError('La nueva contraseña debe incluir al menos un número.');
      return;
    }

    setPasswordLoading(true);

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
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        let errorMessage = 'No se pudo actualizar la contraseña';

        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errorMessage = data.detail.map((err: any) => err.msg).join(' · ');
        }

        throw new Error(errorMessage);
      }

      setPasswordSuccess('Contraseña actualizada correctamente.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (error: any) {
      setPasswordError(error.message || 'No se pudo actualizar la contraseña');
    } finally {
      setPasswordLoading(false);
    }
  };

  // ── Miembros ───────────────────────────────────────────────────────
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);
  const [busyMemberId, setBusyMemberId] = useState<string | null>(null);

  const loadMembers = async () => {
    if (!isAdmin) return;

    setMembersLoading(true);
    setMembersError(null);

    try {
      const data = await getTeamMembers();
      setMembers(data);
    } catch (error: any) {
      setMembersError(error.message || 'No se pudieron cargar los miembros.');
    } finally {
      setMembersLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'members' && isAdmin) {
      loadMembers();
    }
  }, [activeTab, isAdmin]);

  const handleToggleMemberAccess = async (member: TeamMember) => {
    setBusyMemberId(member.id);
    setMembersError(null);

    try {
      const updated = await toggleTeamAccess(member.id, !member.team_access);
      setMembers((prev) =>
        prev.map((m) => (m.id === member.id ? updated : m))
      );
    } catch (error: any) {
      setMembersError(error.message || 'No se pudo actualizar el acceso.');
    } finally {
      setBusyMemberId(null);
    }
  };

  const handleRemoveMember = async (member: TeamMember) => {
    const confirmed = window.confirm(
      `¿Seguro que quieres desactivar a ${member.full_name || member.email}?`
    );
    if (!confirmed) return;

    setBusyMemberId(member.id);
    setMembersError(null);

    try {
      await removeMember(member.id);
      setMembers((prev) => prev.filter((m) => m.id !== member.id));
    } catch (error: any) {
      setMembersError(error.message || 'No se pudo eliminar el miembro.');
    } finally {
      setBusyMemberId(null);
    }
  };

  const visibleTabs = useMemo(() => {
    const base: TabKey[] = ['profile', 'company', 'security', 'billing'];
    if (isAdmin) base.push('members');
    return base;
  }, [isAdmin]);

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Perfil y ajustes</h1>
        <p className="text-muted-foreground mt-1">
          Gestiona la configuración y preferencias de tu cuenta.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 rounded-2xl border bg-muted/30 p-2 w-fit">
        {visibleTabs.includes('profile') && (
          <TabButton
            active={activeTab === 'profile'}
            onClick={() => changeTab('profile')}
            icon={User}
          >
            {TAB_LABELS.profile}
          </TabButton>
        )}

        {visibleTabs.includes('company') && (
          <TabButton
            active={activeTab === 'company'}
            onClick={() => changeTab('company')}
            icon={Building2}
          >
            {TAB_LABELS.company}
          </TabButton>
        )}

        {visibleTabs.includes('security') && (
          <TabButton
            active={activeTab === 'security'}
            onClick={() => changeTab('security')}
            icon={Shield}
          >
            {TAB_LABELS.security}
          </TabButton>
        )}

        {visibleTabs.includes('billing') && (
          <TabButton
            active={activeTab === 'billing'}
            onClick={() => changeTab('billing')}
            icon={CreditCard}
          >
            {TAB_LABELS.billing}
          </TabButton>
        )}

        {visibleTabs.includes('members') && (
          <TabButton
            active={activeTab === 'members'}
            onClick={() => changeTab('members')}
            icon={Users}
          >
            {TAB_LABELS.members}
          </TabButton>
        )}
      </div>

      {activeTab === 'profile' && (
        <SectionCard
          title="Información personal"
          description="Actualiza tu nombre visible dentro de la aplicación."
        >
          <div className="grid md:grid-cols-2 gap-5">
            <Field label="Nombre completo">
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Tu nombre"
              />
            </Field>

            <Field label="Correo electrónico" description="Este dato no se puede editar desde aquí.">
              <Input value={user?.email || ''} disabled />
            </Field>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button onClick={handleSaveProfile} disabled={savingProfile}>
              {savingProfile ? 'Guardando...' : 'Guardar cambios'}
            </Button>

            {profileSaved && (
              <span className="inline-flex items-center gap-1 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" />
                Guardado
              </span>
            )}

            {profileError && (
              <span className="inline-flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {profileError}
              </span>
            )}
          </div>
        </SectionCard>
      )}

      {activeTab === 'company' && (
        <SectionCard
          title="Empresa"
          description="Información organizativa asociada a tu tenant."
        >
          <div className="grid md:grid-cols-2 gap-5">
            <Field label="Nombre de la empresa">
              <Input value={tenant?.name || ''} disabled />
            </Field>

            <Field label="Rol en la empresa">
              <Input value={user?.role || ''} disabled />
            </Field>
          </div>

          <div className="text-sm text-muted-foreground">
            Los analistas se registran con el nombre exacto de la empresa para unirse al tenant correcto.
          </div>
        </SectionCard>
      )}

      {activeTab === 'security' && (
        <SectionCard
          title="Seguridad"
          description="Actualiza tu contraseña de acceso."
        >
          <div className="grid md:grid-cols-3 gap-5">
            <Field label="Contraseña actual">
              <Input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </Field>

            <Field label="Nueva contraseña">
              <Input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </Field>

            <Field label="Confirmar nueva contraseña">
              <Input
                id="confirmNewPassword"
                type="password"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
              />
            </Field>
          </div>

          <div className="text-xs text-muted-foreground">
            La contraseña debe tener al menos 8 caracteres e incluir mayúsculas, minúsculas y números.
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button onClick={handleChangePassword} disabled={passwordLoading}>
              {passwordLoading ? 'Actualizando...' : 'Actualizar contraseña'}
            </Button>

            {passwordSuccess && (
              <span className="inline-flex items-center gap-1 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" />
                {passwordSuccess}
              </span>
            )}

            {passwordError && (
              <span className="inline-flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {passwordError}
              </span>
            )}
          </div>
        </SectionCard>
      )}

      {activeTab === 'billing' && (
        <SectionCard
          title="Facturación"
          description="Resumen informativo del plan actual."
        >
          <div className="grid md:grid-cols-2 gap-5">
            <Field label="Plan actual">
              <Input value="Plan profesional" disabled />
            </Field>

            <Field label="Estado">
              <Input value="Activo" disabled />
            </Field>
          </div>

          <p className="text-sm text-muted-foreground">
            La gestión avanzada de facturación puede añadirse más adelante.
          </p>
        </SectionCard>
      )}

      {activeTab === 'members' && isAdmin && (
        <SectionCard
          title="Miembros del equipo"
          description="Aquí puedes ver quién se ha unido al tenant y decidir quién tiene acceso a la pantalla de Equipo."
        >
          {membersLoading ? (
            <div className="text-sm text-muted-foreground">Cargando miembros...</div>
          ) : membersError ? (
            <div className="inline-flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {membersError}
            </div>
          ) : members.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No hay miembros registrados todavía.
            </div>
          ) : (
            <div className="space-y-3">
              {members.map((member) => {
                const isCurrentUser = member.id === user?.id;
                const isBusy = busyMemberId === member.id;

                return (
                  <div
                    key={member.id}
                    className="border rounded-xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {member.full_name || 'Sin nombre'}
                      </p>
                      <p className="text-sm text-muted-foreground truncate">
                        {member.email}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-2 text-xs">
                        <span className="px-2 py-1 rounded-full bg-muted text-muted-foreground">
                          {member.role}
                        </span>
                        <span className="px-2 py-1 rounded-full bg-muted text-muted-foreground">
                          {member.team_access ? 'Acceso a Team' : 'Sin acceso a Team'}
                        </span>
                        {!member.is_active && (
                          <span className="px-2 py-1 rounded-full bg-red-50 text-red-600">
                            Inactivo
                          </span>
                        )}
                        {isCurrentUser && (
                          <span className="px-2 py-1 rounded-full bg-blue-50 text-blue-600">
                            Tú
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        variant={member.team_access ? 'outline' : 'default'}
                        disabled={isBusy || isCurrentUser}
                        onClick={() => handleToggleMemberAccess(member)}
                      >
                        {member.team_access ? 'Quitar acceso' : 'Dar acceso'}
                      </Button>

                      <Button
                        variant="outline"
                        disabled={isBusy || isCurrentUser}
                        onClick={() => handleRemoveMember(member)}
                        className="gap-2"
                      >
                        <Trash2 className="h-4 w-4" />
                        Eliminar
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}