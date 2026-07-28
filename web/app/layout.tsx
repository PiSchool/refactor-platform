import './globals.css';
import type { Metadata } from 'next';
import { Providers } from '@/components/providers';
import { Shell } from '@/components/shell';
import { LockGate } from '@/components/lock-screen';

export const metadata: Metadata = { title: 'Refactor Platform', description: 'Refactoring-agent benchmark platform' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body>
        <Providers>
          <LockGate>
            <Shell>{children}</Shell>
          </LockGate>
        </Providers>
      </body>
    </html>
  );
}
