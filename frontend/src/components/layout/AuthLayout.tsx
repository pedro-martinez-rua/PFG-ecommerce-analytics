import React from 'react';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { BarChart3 } from 'lucide-react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Simple header */}
      <header className="border-b bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="container flex h-16 items-center">
          <Link href="/" className="flex items-center gap-3 font-semibold text-foreground">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <BarChart3 className="h-4 w-4" />
            </div>
            <span className="text-lg tracking-tight">{t('auth.brand')}</span>
          </Link>
        </div>
      </header>

      {/* Centered content */}
      <main className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-md rounded-3xl border bg-card p-8 shadow-sm">{children}</div>
      </main>

      {/* Simple footer */}
      <footer className="border-t bg-background py-4">
        <div className="container flex justify-center gap-6 text-sm text-muted-foreground">
          <a href="#" className="hover:text-foreground transition-colors">
            {t('auth.footer.privacy')}
          </a>
          <a href="#" className="hover:text-foreground transition-colors">
            {t('auth.footer.terms')}
          </a>
          <Link href="/contact" className="hover:text-foreground transition-colors">
            {t('auth.footer.contact')}
          </Link>
        </div>
      </footer>
    </div>
  );
}
