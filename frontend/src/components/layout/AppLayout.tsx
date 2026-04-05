import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { AppFooter } from './FooterIn';

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
  | { type: 'divider' };

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { t } = useTranslation();

  const { user, tenant, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const sidebarLinks: SidebarLink[] = [
    { type: 'link', href: '/app', labelKey: 'app.sidebar.overview', icon: LayoutDashboard },
    { type: 'link', href: '/app/upload', labelKey: 'app.sidebar.upload', icon: Upload },
    { type: 'link', href: '/app/dashboards', labelKey: 'app.sidebar.dashboards', icon: FolderKanban },
    { type: 'link', href: '/app/reports', labelKey: 'app.sidebar.reports', icon: FileText },
    { type: 'divider' },
    { type: 'link', href: '/app/tutorials', labelKey: 'app.sidebar.tutorials', icon: BookOpen },
    { type: 'link', href: '/app/faq', labelKey: 'app.sidebar.faq', icon: HelpCircle },
    { type: 'link', href: '/app/contact', labelKey: 'app.sidebar.contact', icon: Mail },
    { type: 'divider' },
    { type: 'link', href: '/app/profile', labelKey: 'app.sidebar.profile', icon: User },
    { type: 'link', href: '/app/imports', labelKey: 'app.sidebar.imports', icon: Database },
  ];

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  const isActiveLink = (href: string) =>
    href === '/app' ? pathname === '/app' : pathname.startsWith(href);

  const planLabel =
    tenant?.plan ? t(`app.plan.${tenant.plan}`) : t('app.plan.free');

  return (
    <div className="min-h-screen flex flex-col bg-muted/30">
      {/* Top Bar */}
      <header className="sticky top-0 z-50 h-16 border-b bg-background">
        <div className="flex h-full items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden p-2 -ml-2"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            <Link href="/app" className="flex items-center gap-2 font-semibold text-foreground">
              <BarChart3 className="h-6 w-6 text-secondary" />
              <span className="text-lg hidden sm:inline">{t('app.brand')}</span>
            </Link>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 hidden sm:flex">
                  <Building2 className="h-4 w-4" />
                  <span className="max-w-[150px] truncate">
                    {tenant?.name || t('app.topbar.selectWorkspace')}
                  </span>
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuItem>
                  <Building2 className="h-4 w-4 mr-2" />
                  {tenant?.name}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" aria-label={t('app.topbar.notifications')}>
              <Bell className="h-5 w-5" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-medium">
                    {user?.fullName?.charAt(0) || 'U'}
                  </div>
                  <span className="hidden sm:inline max-w-[120px] truncate">
                    {user?.fullName}
                  </span>
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user?.fullName}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/app/profile')}>
                  <User className="h-4 w-4 mr-2" />
                  {t('app.user.profile')}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-destructive">
                  <LogOut className="h-4 w-4 mr-2" />
                  {t('app.user.logout')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-foreground/20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={`fixed lg:sticky top-16 z-40 h-[calc(100vh-4rem)] w-64 border-r bg-background transition-transform ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <nav className="flex flex-col h-full py-4">
            <div className="flex-1 px-3 space-y-1">
              {sidebarLinks.map((item, index) =>
                item.type === 'divider' ? (
                  <div key={index} className="my-3 border-t" />
                ) : (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium ${
                      isActiveLink(item.href)
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    {t(item.labelKey)}
                  </Link>
                )
              )}
            </div>

            <div className="px-3 pt-4 border-t mt-auto">
              <div className="px-3 py-2">
                <p className="text-xs text-muted-foreground">{planLabel}</p>
              </div>
            </div>
          </nav>
        </aside>

        <main className="flex-1 overflow-auto">
          <div className="container py-6 lg:py-8 max-w-6xl">{children}</div>
        </main>
      </div>
      <AppFooter/>
    </div>
  );
}
