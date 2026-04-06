import React, { useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Link } from '@/components/Link';
import { Button } from '@/components/ui/button';
import { BarChart3, Menu, X } from 'lucide-react';
// import { Languages, Check } from 'lucide-react'; // i18n disabled

/*
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
*/

// type LangOption = { code: 'es' | 'en'; label: string };

const navLinks = [
  { href: '/', key: 'nav.product' },
  { href: '/tutorials', key: 'nav.tutorials' },
  { href: '/faq', key: 'nav.faq' },
  { href: '/contact', key: 'nav.contact' },
];

export function Navbar() {
  const { pathname } = useLocation();
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  /*
  const langOptions: LangOption[] = useMemo(
    () => [
      { code: 'es', label: 'Español' },
      { code: 'en', label: 'English' },
    ],
    []
  );

  const currentLang = (i18n.language?.startsWith('en') ? 'en' : 'es') as 'es' | 'en';

  const changeLang = async (lng: 'es' | 'en') => {
    if (lng === currentLang) return;
    await i18n.changeLanguage(lng);
  };
  */

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container flex h-16 items-center justify-between">
        
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-semibold text-foreground">
          <BarChart3 className="h-6 w-6 text-secondary" />
          <span className="text-lg">CommerceIQ</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors hover:text-foreground ${
                pathname === link.href ? 'text-foreground' : 'text-muted-foreground'
              }`}
            >
              {t(link.key)}
            </Link>
          ))}
        </div>

        {/* Desktop Right */}
        <div className="hidden md:flex items-center gap-3">

          {/* Language selector disabled */}
          {/*
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Languages className="h-4 w-4" />
                {currentLang === 'es' ? 'ES' : 'EN'}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {langOptions.map((opt) => (
                <DropdownMenuItem key={opt.code} onClick={() => changeLang(opt.code)}>
                  <span className="flex items-center justify-between w-full">
                    <span>{opt.label}</span>
                    {opt.code === currentLang ? <Check className="h-4 w-4" /> : null}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          */}

          <Link href="/login">
            <Button variant="ghost" size="sm">
              {t('nav.login')}
            </Button>
          </Link>

          <Link href="/register">
            <Button size="sm">{t('nav.register')}</Button>
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t bg-background">
          <div className="container py-4 space-y-4">

            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
                onClick={() => setMobileMenuOpen(false)}
              >
                {t(link.key)}
              </Link>
            ))}

            {/* Mobile Language disabled */}
            {/*
            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
                <Languages className="h-4 w-4" />
                Language
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={currentLang === 'es' ? 'default' : 'outline'}
                  onClick={() => changeLang('es')}
                >
                  ES
                </Button>
                <Button
                  variant={currentLang === 'en' ? 'default' : 'outline'}
                  onClick={() => changeLang('en')}
                >
                  EN
                </Button>
              </div>
            </div>
            */}

            <div className="pt-4 border-t flex flex-col gap-2">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full">
                  {t('nav.login')}
                </Button>
              </Link>

              <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full">{t('nav.register')}</Button>
              </Link>
            </div>

          </div>
        </div>
      )}
    </header>
  );
}