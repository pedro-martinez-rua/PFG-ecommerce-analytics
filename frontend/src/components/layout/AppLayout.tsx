import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Footer } from './Footer';

import {
  BarChart3,
  LayoutDashboard,
  Upload,
  FolderKanban,
  FileText,
  BookOpen,
  HelpCircle,
  Mail,
  User,
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  X,
  Building2,
  Database,
} from 'lucide-react';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface AppLayoutProps {
  children: React.ReactNode;
}

type SidebarLink =
  | { type: 'link'; href: string; labelKey: string; icon: React.ComponentType<{ className?: string }> }
  | { type: 'divider'; label?: string };

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { t } = useTranslation();

  const { user, tenant, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const sidebarLinks: SidebarLink[] = [
    // Principal
    { type: 'link', href: '/app',            labelKey: 'app.sidebar.overview',   icon: LayoutDashboard },
    { type: 'link', href: '/app/upload',     labelKey: 'app.sidebar.upload',     icon: Upload },
    { type: 'link', href: '/app/dashboards', labelKey: 'app.sidebar.dashboards', icon: FolderKanban },
    { type: 'link', href: '/app/reports',    labelKey: 'app.sidebar.reports',    icon: FileText },
    { type: 'link', href: '/app/imports',    labelKey: 'app.sidebar.imports',    icon: Database },
    // Soporte
    { type: 'divider', label: t('app.sidebar.support', 'Soporte') },
    { type: 'link', href: '/app/tutorials', labelKey: 'app.sidebar.tutorials', icon: BookOpen },
    { type: 'link', href: '/app/faq',       labelKey: 'app.sidebar.faq',       icon: HelpCircle },
    { type: 'link', href: '/app/contact',   labelKey: 'app.sidebar.contact',   icon: Mail },
    // Cuenta
    { type: 'divider', label: t('app.sidebar.account', 'Cuenta') },
    { type: 'link', href: '/app/profile', labelKey: 'app.sidebar.profile', icon: User },
  ];

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  const isActiveLink = (href: string) =>
    href === '/app' ? pathname === '/app' : pathname.startsWith(href);

  const planLabel = tenant?.plan ? t(`app.plan.${tenant.plan}`) : t('app.plan.free');

  // Iniciales del usuario para el avatar
  const initials = user?.fullName
    ?.split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'U';

  return (
    <div className="min-h-screen flex flex-col bg-muted/30">

      {/* ── Top Bar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 h-16 border-b bg-background shadow-subtle">
        <div className="flex h-full items-center justify-between px-4 lg:px-6">

          {/* Izquierda */}
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden p-2 -ml-2 rounded-md hover:bg-muted transition-colors"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            <Link href="/app" className="flex items-center gap-2.5 font-bold text-foreground">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <BarChart3 className="h-4.5 w-4.5 text-primary-foreground" style={{ width: 18, height: 18 }} />
              </div>
              <span className="text-base hidden sm:inline tracking-tight">{t('app.brand')}</span>
            </Link>

            {/* Workspace selector */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-1.5 hidden sm:flex text-muted-foreground hover:text-foreground">
                  <Building2 className="h-3.5 w-3.5" />
                  <span className="max-w-[140px] truncate text-sm">{tenant?.name || t('app.topbar.selectWorkspace')}</span>
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-48">
                <DropdownMenuItem className="font-medium">
                  <Building2 className="h-4 w-4 mr-2 text-muted-foreground" />
                  {tenant?.name}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Derecha */}
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="text-muted-foreground" aria-label={t('app.topbar.notifications')}>
              <Bell className="h-4.5 w-4.5" style={{ width: 18, height: 18 }} />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2 pl-1.5">
                  {/* Avatar con iniciales */}
                  <div className="h-8 w-8 rounded-full bg-secondary/15 border border-secondary/20 flex items-center justify-center text-secondary text-xs font-bold">
                    {initials}
                  </div>
                  <span className="hidden sm:inline text-sm max-w-[120px] truncate text-foreground">
                    {user?.fullName}
                  </span>
                  <ChevronDown className="h-3 w-3 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-3 py-2 border-b">
                  <p className="text-sm font-medium truncate">{user?.fullName}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <DropdownMenuItem onClick={() => navigate('/app/profile')} className="mt-1">
                  <User className="h-4 w-4 mr-2 text-muted-foreground" />
                  {t('app.user.profile')}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                  <LogOut className="h-4 w-4 mr-2" />
                  {t('app.user.logout')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Backdrop móvil */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ── Sidebar ──────────────────────────────────────── */}
        <aside
          className={`fixed lg:sticky top-16 z-40 h-[calc(100vh-4rem)] w-60 border-r bg-background transition-transform duration-200 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <nav className="flex flex-col h-full py-3">
            <div className="flex-1 px-2 space-y-0.5">
              {sidebarLinks.map((item, index) => {
                if (item.type === 'divider') {
                  return (
                    <div key={index} className="pt-4 pb-1 px-3">
                      {item.label && (
                        <p className="text-[11px] font-semibold text-muted-foreground/60 uppercase tracking-widest">
                          {item.label}
                        </p>
                      )}
                    </div>
                  );
                }

                const active = isActiveLink(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                      active
                        ? 'bg-secondary/10 text-secondary font-semibold border-l-2 border-secondary pl-[10px]'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <item.icon className={`h-4 w-4 flex-shrink-0 ${active ? 'text-secondary' : ''}`} />
                    <span>{t(item.labelKey)}</span>
                  </Link>
                );
              })}
            </div>

            {/* Plan badge */}
            <div className="px-3 pt-3 border-t mt-2">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50">
                <div className="h-1.5 w-1.5 rounded-full bg-success" />
                <p className="text-xs text-muted-foreground">{planLabel}</p>
              </div>
            </div>
          </nav>
        </aside>

        {/* ── Main Content ─────────────────────────────────── */}
        <main className="flex-1 overflow-auto min-w-0">
          <div className="container py-6 lg:py-8 max-w-6xl">{children}</div>
        </main>
      </div>

      <Footer />
    </div>
  );
}