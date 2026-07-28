'use client';

import { useRouter } from 'next/navigation';
import { RunWizard } from '@/components/run-wizard';

export default function NewRunPage() {
  const router = useRouter();
  return <RunWizard onClose={() => router.push('/')} />;
}
