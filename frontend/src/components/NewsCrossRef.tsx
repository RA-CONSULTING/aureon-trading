import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Globe } from 'lucide-react';

async function fetchNews(q:string){
  const endpoint = import.meta.env.VITE_NEWS_API_ENDPOINT as string|undefined;
  if (endpoint) {
    const r = await fetch(`${endpoint}?q=${encodeURIComponent(q)}`); 
    if(!r.ok) return []; 
    const data = await r.json();
    return (data.articles??[]).map((a:any)=>({
      title:a.title,
      url:a.url,
      source:a.source?.name,
      publishedAt:a.publishedAt
    }));
  }
  const g = import.meta.env.VITE_GNEWS_API_KEY as string|undefined;
  if (g) { 
    const r=await fetch(`https://gnews.io/api/v4/search?q=${encodeURIComponent(q)}&lang=en&max=5&apikey=${g}`); 
    if(!r.ok) return []; 
    const d=await r.json(); 
    return (d.articles??[]).map((a:any)=>({
      title:a.title,
      url:a.url,
      source:a.source?.name,
      publishedAt:a.publishedAt
    })); 
  }
  return [];
}

export default function NewsCrossRef({ query }:{ query:string }) {
  const [items,setItems]=React.useState<any[]|null>(null);
  
  React.useEffect(()=>{
    fetchNews(query).then(setItems).catch(()=>setItems([]));
  },[query]);
  
  return (
    <Card className="bg-white/10 border-white/20 text-white">
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Globe className="w-4 h-4"/> 
          Related news
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        {!items?.length ? (
          <div>Set <code>VITE_NEWS_API_ENDPOINT</code> or <code>VITE_GNEWS_API_KEY</code> in <code>.env</code>.</div>
        ) : (
          items.map((it,i)=>(
            <div key={i} className="flex items-center justify-between gap-2">
              <a href={it.url} target="_blank" rel="noreferrer" className="hover:underline">
                {it.title}
              </a>
              {it.source && (
                <Badge variant="secondary" className="text-[10px]">
                  {it.source}
                </Badge>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}