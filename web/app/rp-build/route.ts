import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { NextResponse } from 'next/server';

/** What this dashboard image was built from.
 *
 *  Served outside `/api`, which is proxied to the backend, so the answer comes
 *  from the dashboard container itself rather than from the API. `build-stamp`
 *  is written by docker/frontend.Dockerfile; a development server has none and
 *  reports the bundle identifier alone.
 */
export const dynamic = 'force-dynamic';

async function read(relative: string): Promise<string> {
  try {
    return (await readFile(path.join(process.cwd(), relative), 'utf8')).trim();
  } catch {
    return '';
  }
}

export async function GET() {
  const stamp = await read('build-stamp');
  const values: Record<string, string> = {};
  for (const line of stamp.split('\n')) {
    const [key, ...rest] = line.split('=');
    if (key.trim()) values[key.trim()] = rest.join('=').trim();
  }
  return NextResponse.json(
    {
      fingerprint: values.fingerprint || '',
      revision: values.revision || process.env.RP_BUILD_REV || '',
      builtAt: values.builtAt || '',
      buildId: await read('.next/BUILD_ID'),
    },
    { headers: { 'Cache-Control': 'no-store' } },
  );
}
