/**
 * @module shell
 * @description Application shell with sidebar navigation and theme controls.
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Database, Moon, Play, Settings, Sun, Monitor, Zap } from 'lucide-react';
import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { useTheme, type Theme } from '@/lib/theme';

// Explicit typing for nav items so the IDE/TS understands the icon component props
const nav: Array<{ href: string; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { href: '/',        label: 'Overview', icon: Activity },
  { href: '/runs',    label: 'Runs',     icon: Play     },
  // Indexes (RAG) hidden — retrieval/embeddings are disabled in this deployment.
];

// Theme icons typed to accept className (SVG props)
const themeIcons: Record<Theme, React.ComponentType<{ className?: string }>> = { light: Sun, dark: Moon, dimmed: Monitor };
const themeLabels: Record<Theme, string> = { light: 'Light', dark: 'Dark', dimmed: 'Dimmed' };

type NavItemProps = { href: string; label: string; icon: React.ComponentType<{ className?: string }>; active: boolean };

const NavItem: React.FC<NavItemProps> = ({ href, label, icon: Icon, active }) => {
  return (
    <Link
      href={href}
      prefetch={false}
      title={label}
      className={cn(
        'group/item relative flex h-9 items-center gap-3 rounded-md px-2 text-sm transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg focus-visible:ring-inset',
        active
          ? 'bg-sidenav-selected text-fg font-medium'
          : 'text-fg-muted hover:bg-neutral-subtle hover:text-fg',
      )}
    >
      {/* Active indicator bar */}
      {active && (
        <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-accent-fg" />
      )}
      <Icon className={cn('h-4 w-4 shrink-0 transition-colors', active ? 'text-fg' : 'text-fg-muted group-hover/item:text-fg')} />
      <span className={cn(
        'truncate text-sm transition-[opacity,transform] duration-200',
        'opacity-0 -translate-x-1 group-hover/nav:opacity-100 group-hover/nav:translate-x-0',
      )}>
        {label}
      </span>
    </Link>
  );
}

/** Application shell with sidebar navigation, theme toggle, and content area. */
export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { theme, cycle } = useTheme();
  const ThemeIcon = themeIcons[theme];

  return (
    <div className="flex min-h-screen bg-canvas text-fg">
      {/* Desktop sidebar */}
      <aside className="group/nav fixed inset-y-0 left-0 z-30 hidden w-12 flex-col border-r border-border bg-canvas-subtle transition-[width] duration-200 ease-out hover:w-48 lg:flex">
        {/* Logo */}
        <div className="flex h-12 items-center border-b border-border px-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent-emphasis">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className={cn(
            'ml-2.5 truncate text-sm font-semibold text-fg',
            'opacity-0 transition-[opacity,transform] duration-200 -translate-x-1 group-hover/nav:opacity-100 group-hover/nav:translate-x-0',
          )}>
            Refactor Platform
          </span>
        </div>

        {/* Nav items */}
        <nav className="flex flex-1 flex-col gap-0.5 px-1.5 pt-2">
          {nav.map(item => (
            <NavItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              active={pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))}
            />
          ))}
        </nav>

        {/* Bottom: settings + theme */}
        <div className="space-y-0.5 px-1.5 pb-3">
          <NavItem
            href="/settings"
            label="Settings"
            icon={Settings}
            active={pathname === '/settings'}
          />
          <button
            type="button"
            onClick={cycle}
            title={`Theme: ${themeLabels[theme]}`}
            className={cn(
              'flex h-9 w-full items-center gap-3 rounded-md px-2 text-sm text-fg-muted',
              'transition-colors duration-150 hover:bg-neutral-subtle hover:text-fg',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg focus-visible:ring-inset',
            )}
          >
            <ThemeIcon className="h-4 w-4 shrink-0" />
            <span className={cn(
              'truncate capitalize',
              'opacity-0 -translate-x-1 transition-[opacity,transform] duration-200 group-hover/nav:opacity-100 group-hover/nav:translate-x-0',
            )}>
              {themeLabels[theme]}
            </span>
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="fixed inset-x-0 top-0 z-30 flex h-12 items-center justify-between border-b border-border bg-canvas-subtle px-3 lg:hidden">
        <div className="flex items-center gap-0.5">
          <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent-emphasis">
            <Zap className="h-3.5 w-3.5 text-white" />
          </div>
          {nav.map(item => {
            const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                prefetch={false}
                title={item.label}
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-md transition-colors duration-150',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg',
                  active ? 'bg-sidenav-selected text-fg' : 'text-fg-muted hover:bg-neutral-subtle hover:text-fg',
                )}
              >
                <Icon className="h-4 w-4" />
              </Link>
            );
          })}
        </div>
        <div className="flex items-center gap-0.5">
          <Link
            href="/settings"
            prefetch={false}
            title="Settings"
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-md transition-colors duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg',
              pathname === '/settings' ? 'bg-sidenav-selected text-fg' : 'text-fg-muted hover:bg-neutral-subtle hover:text-fg',
            )}
          >
            <Settings className="h-4 w-4" />
          </Link>
          <button
            type="button"
            onClick={cycle}
            title={`Theme: ${themeLabels[theme]}`}
            className="flex h-8 w-8 items-center justify-center rounded-md text-fg-muted transition-colors hover:bg-neutral-subtle hover:text-fg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg"
          >
            <ThemeIcon className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="min-w-0 flex-1 pt-12 lg:pl-12 lg:pt-0">
        <div className="mx-auto max-w-[1400px] px-4 py-4 lg:px-6 lg:py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
