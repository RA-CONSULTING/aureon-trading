import React from 'react';

export default function NewsHealth() {
  const [status, setStatus] = React.useState('loading');
  const [source, setSource] = React.useState('env');

  React.useEffect(() => {
    const proxyUrl = import.meta.env.VITE_NEWS_PROXY_URL;
    const gnewsKey = import.meta.env.VITE_GNEWS_API_KEY;
    
    setSource(proxyUrl ? 'proxy' : gnewsKey ? 'gnews' : 'none');

    (async () => {
      try {
        const url = proxyUrl 
          ? `${proxyUrl}?url=${encodeURIComponent('https://feeds.bbci.co.uk/news/world/rss.xml')}`
          : gnewsKey 
          ? `https://gnews.io/api/v4/search?q=world&lang=en&max=1&apikey=${gnewsKey}`
          : '';

        if (!url) return setStatus('fail');

        const response = await fetch(url, { cache: 'no-store' });
        setStatus(response.ok ? 'ok' : 'fail');
      } catch {
        setStatus('fail');
      }
    })();
  }, []);

  return (
    <span className={`px-3 py-1 rounded text-sm font-medium ${
      status === 'ok' ? 'bg-green-100 text-green-800 border border-green-200' : 
      status === 'loading' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' : 
      'bg-red-100 text-red-800 border border-red-200'
    }`}>
      news:{source}:{status}
    </span>
  );
}