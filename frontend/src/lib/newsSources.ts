export interface NewsSource {
  id: string;
  name: string;
  rssUrl: string;
  region: string;
  country: string;
}

export const NEWS_SOURCES: NewsSource[] = [
  { id: 'bbc', name: 'BBC World', rssUrl: 'https://feeds.bbci.co.uk/news/world/rss.xml', region: 'Europe', country: 'UK' },
  { id: 'cnn', name: 'CNN Top', rssUrl: 'http://rss.cnn.com/rss/edition.rss', region: 'North America', country: 'US' },
  { id: 'reuters', name: 'Reuters World', rssUrl: 'https://www.reuters.com/world/rss', region: 'Global', country: 'Global' },
  { id: 'ap', name: 'Associated Press Top', rssUrl: 'https://apnews.com/hub/ap-top-news?output=rss', region: 'North America', country: 'US' },
  { id: 'sky', name: 'Sky News', rssUrl: 'https://feeds.skynews.com/feeds/rss/world.xml', region: 'Europe', country: 'UK' },
  { id: 'aljazeera', name: 'Al Jazeera', rssUrl: 'https://www.aljazeera.com/xml/rss/all.xml', region: 'Middle East', country: 'Qatar' },
  { id: 'dw', name: 'Deutsche Welle Top', rssUrl: 'https://rss.dw.com/rdf/rss-en-all', region: 'Europe', country: 'Germany' },
  { id: 'guardian', name: 'The Guardian World', rssUrl: 'https://www.theguardian.com/world/rss', region: 'Europe', country: 'UK' },
  { id: 'fox', name: 'Fox News World', rssUrl: 'https://feeds.foxnews.com/foxnews/world', region: 'North America', country: 'US' },
  { id: 'nyt', name: 'New York Times World', rssUrl: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', region: 'North America', country: 'US' }
];

export function getSourceById(id: string): NewsSource | undefined {
  return NEWS_SOURCES.find(s => s.id === id);
}

export function getSourcesByRegion(region: string): NewsSource[] {
  return NEWS_SOURCES.filter(s => s.region === region);
}