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
    <div className="min-h-screen flex flex-col">
      {/* Simple header */}
      <header className="border-b">
        <div className="container flex h-16 items-center">
          <Link href="/" className="flex items-center gap-2 font-semibold text-foreground">
            <BarChart3 className="h-6 w-6 text-secondary" />
            <span className="text-lg">{t('auth.brand')}</span>
          </Link>
        </div>
      </header>

      {/* Centered content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">{children}</div>
      </main>

      {/* Simple footer */}
      <footer className="border-t py-4">
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
