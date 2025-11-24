// functions/api/rss.ts - Cloudflare Pages Functions
interface PagesFunction {
  (context: { request: Request }): Promise<Response>;
}

export const onRequestGet: PagesFunction = async (context) => {
  const url = context.request.url;
  const q = new URL(url).searchParams.get('url');
  if (!q) return new Response(JSON.stringify({ error: 'Missing url' }), { status: 400 });

  try {
    const r = await fetch(q, { 
      headers: { 'user-agent': 'NewsProxy/1.0' },
      signal: AbortSignal.timeout(10000)
    });
    if (!r.ok) return new Response(JSON.stringify({ error: 'Upstream error' }), { status: r.status });

    const xml = await r.text();
    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, 25).map(m => {
      const b = m[1];
      const pick = (tag: string) => (b.match(new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, 'i')) || [])[1]?.trim();
      return { title: pick('title'), link: pick('link'), pubDate: pick('pubDate') };
    });

    return new Response(JSON.stringify({ items }), { 
      headers: { 
        'Cache-Control': 'max-age=60',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type'
      } 
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Fetch failed' }), { status: 500 });
  }
};