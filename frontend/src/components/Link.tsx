import React from 'react';
import { Link as RouterLink } from 'react-router-dom';

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  children: React.ReactNode;
  className?: string;
  activeClassName?: string; // lo dejaremos para el siguiente paso si quieres estados activos
}

export function Link({ href, children, className = '', onClick, ...props }: LinkProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) onClick(e);
    // si el consumer hace preventDefault, respetamos.
  };

  return (
    <RouterLink
      to={href}
      onClick={handleClick}
      className={className}
      {...props}
    >
      {children}
    </RouterLink>
  );
}
