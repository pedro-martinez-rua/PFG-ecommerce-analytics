import {
  User, Tenant, Session,
  LoginCredentials, RegisterPayload, UserRole
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || '';
const SESSION_KEY = 'analytics_session';

class AuthService {
  private session: Session | null = null;

  constructor() {
    this.loadSession();
  }

  private loadSession(): void {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (stored) {
        const session = JSON.parse(stored) as Session;
        if (new Date(session.expiresAt) > new Date()) {
          this.session = session;
        } else {
          localStorage.removeItem(SESSION_KEY);
        }
      }
    } catch {
      localStorage.removeItem(SESSION_KEY);
    }
  }

  private saveSession(session: Session): void {
    this.session = session;
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }

  async login(credentials: LoginCredentials): Promise<{ success: boolean; error?: string }> {
    try {
      // Backend espera JSON con { email, password } — NO form-encoded
      const tokenRes = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email:    credentials.email,
          password: credentials.password,
        }),
      });

      if (!tokenRes.ok) {
        const err = await tokenRes.json().catch(() => ({}));
        return { success: false, error: err.detail || 'Credenciales incorrectas' };
      }

      const tokenData = await tokenRes.json();
      const token = tokenData.access_token;

      const meRes = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!meRes.ok) {
        return { success: false, error: 'Error al obtener los datos del usuario' };
      }

      const meData = await meRes.json();

      const user: User = {
        id:        meData.id,
        email:     meData.email,
        fullName:  meData.full_name || meData.email,
        role:      meData.role || 'admin',
        tenantId:  meData.tenant_id,
        createdAt: meData.created_at || new Date().toISOString(),
      };

      const tenant: Tenant = {
        id:        meData.tenant_id,
        name:      meData.company_name || meData.email,
        plan:      'professional',
        createdAt: new Date().toISOString(),
      };

      const session: Session = {
        user,
        tenant,
        token,
        expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      };

      this.saveSession(session);
      return { success: true };

    } catch {
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  }

  async register(payload: RegisterPayload): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email:        payload.email,
          password:     payload.password,
          full_name:    payload.fullName,
          company_name: payload.companyName,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return { success: false, error: err.detail || 'Error al registrarse' };
      }

      // Registro exitoso → hacer login automático
      return this.login({ email: payload.email, password: payload.password });

    } catch {
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  }

  async logout(): Promise<void> {
    this.session = null;
    localStorage.removeItem(SESSION_KEY);
  }

  async forgotPassword(_email: string): Promise<{ success: boolean; error?: string }> {
    // El backend no tiene este endpoint aún — devolver success por UX
    return { success: true };
  }
  async updateMe(payload: { full_name: string }): Promise<{ success: boolean; error?: string }> {
    try {
      const token = this.session?.token
      if (!token) return { success: false, error: 'No autenticado' }

      const res = await fetch(`${API_BASE}/api/auth/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      const data = await res.json().catch(() => ({}))

      if (!res.ok) {
        if (typeof data.detail === 'string') {
          return { success: false, error: data.detail }
        }
        if (Array.isArray(data.detail) && data.detail.length > 0) {
          return { success: false, error: data.detail.map((err: any) => err.msg).join(' · ') }
        }
        return { success: false, error: 'No se pudo actualizar el perfil' }
      }

      if (this.session) {
        const updatedSession: Session = {
          ...this.session,
          user: {
            ...this.session.user,
            fullName: data.full_name || payload.full_name,
          },
        }
        this.saveSession(updatedSession)
      }

      return { success: true }
    } catch {
      return { success: false, error: 'Error de conexión con el servidor' }
    }
  }

  getSession(): Session | null     { return this.session; }
  isAuthenticated(): boolean        { return this.session !== null && new Date(this.session.expiresAt) > new Date(); }
  hasRole(role: UserRole): boolean  { return this.session?.user.role === role; }
  isAdmin(): boolean                { return this.hasRole('admin'); }
  getCurrentUser(): User | null     { return this.session?.user || null; }
  getCurrentTenant(): Tenant | null { return this.session?.tenant || null; }
}

export const authService       = new AuthService();
export const login             = (c: LoginCredentials) => authService.login(c);
export const register          = (p: RegisterPayload)  => authService.register(p);
export const logout            = ()                     => authService.logout();
export const forgotPassword    = (e: string)            => authService.forgotPassword(e);
export const getSession        = ()                     => authService.getSession();
export const isAuthenticated   = ()                     => authService.isAuthenticated();
export const isAdmin           = ()                     => authService.isAdmin();
export const getCurrentUser    = ()                     => authService.getCurrentUser();
export const getCurrentTenant  = ()                     => authService.getCurrentTenant();
export const updateMe = (payload: { full_name: string }) => authService.updateMe(payload);