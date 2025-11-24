import { NEWS_SOURCES, getSourceById } from '../lib/newsSources';
import { newsEmotionStore, type NewsEmotionData } from '../state/newsEmotionStore';
import { classifyBatchWithAuris } from './sources/aurisSandbox';
import { ingestNarrative, ingestAffect } from './hncWorker';

// Simple sentiment lexicon for fallback
const NEGATIVE_WORDS = new Set([
  'crisis', 'war', 'death', 'killed', 'attack', 'violence', 'terror', 'bomb', 'murder',
  'disaster', 'crash', 'fire', 'flood', 'earthquake', 'pandemic', 'disease', 'sick',
  'recession', 'unemployment', 'poverty', 'corrupt', 'scandal', 'fraud', 'illegal',
  'protest', 'riot', 'conflict', 'threat', 'danger', 'emergency', 'warning', 'alert'
]);

const POSITIVE_WORDS = new Set([
  'success', 'victory', 'win', 'celebrate', 'joy', 'happy', 'love', 'peace', 'hope',
  'breakthrough', 'achievement', 'progress', 'growth', 'recovery', 'heal', 'cure',
  'agreement', 'cooperation', 'unity', 'support', 'help', 'rescue', 'save', 'protect'
]);

function analyzeEmotion(title: string): { valence: number; arousal: number; isNegative: boolean } {
  const words = title.toLowerCase().split(/\s+/);
  let negCount = 0, posCount = 0;
  
  words.forEach(word => {
    if (NEGATIVE_WORDS.has(word)) negCount++;
    if (POSITIVE_WORDS.has(word)) posCount++;
  });
  
  const valence = posCount > negCount ? 0.7 : negCount > posCount ? 0.3 : 0.5;
  const arousal = (negCount + posCount) > 0 ? 0.8 : 0.4;
  const isNegative = valence < 0.4;
  
  return { valence, arousal, isNegative };
}

async function fetchNewsFromSource(source: typeof NEWS_SOURCES[0]): Promise<NewsEmotionData[]> {
  try {
    const proxyUrl = import.meta.env.VITE_NEWS_PROXY_URL as string | undefined;
    const apiEndpoint = import.meta.env.VITE_NEWS_API_ENDPOINT as string | undefined;
    const gnewsKey = import.meta.env.VITE_GNEWS_API_KEY as string | undefined;
    
    let articles: any[] = [];
    
    if (proxyUrl) {
      const response = await fetch(`${proxyUrl}?url=${encodeURIComponent(source.rssUrl)}`);
      if (response.ok) {
        const data = await response.json();
        articles = data.items || [];
      }
    } else if (apiEndpoint) {
      const response = await fetch(`${apiEndpoint}?source=${source.id}`);
      if (response.ok) {
        const data = await response.json();
        articles = data.articles || [];
      }
    } else if (gnewsKey && source.id === 'reuters') {
      const response = await fetch(`https://gnews.io/api/v4/search?q=${source.name}&lang=en&max=10&apikey=${gnewsKey}`);
      if (response.ok) {
        const data = await response.json();
        articles = data.articles || [];
      }
    }
    
    return articles.map((article: any) => {
      const emotion = analyzeEmotion(article.title);
      return {
        id: `${source.id}-${Date.now()}-${Math.random()}`,
        title: article.title,
        sourceId: source.id,
        sourceName: source.name,
        region: source.region,
        timestamp: Date.now(),
        ...emotion
      };
    });
  } catch (error) {
    console.error(`Error fetching from ${source.name}:`, error);
    return [];
  }
}

async function pollAllSources() {
  const promises = NEWS_SOURCES.map(fetchNewsFromSource);
  const results = await Promise.allSettled(promises);
  
  const allData: NewsEmotionData[] = [];
  results.forEach(result => {
    if (result.status === 'fulfilled') {
      allData.push(...result.value);
    }
  });
  
  if (allData.length > 0) {
    newsEmotionStore.addBatch(allData);
    
    // Enhanced emotion classification with Auris
    try {
      const headlines = allData.map(item => item.title);
      const aurisResults = await classifyBatchWithAuris(headlines);
      
      // Ingest into HNC system
      allData.forEach((item, idx) => {
        const auris = aurisResults[idx];
        if (auris) {
          // Ingest narrative data
          const narrative = {
            t: item.timestamp,
            station: item.sourceName,
            region: item.region,
            text: item.title,
            emotion: auris.emotion,
            tags: auris.tags
          };
          ingestNarrative(narrative);
          
          // Ingest affect data
          const affect = {
            t: item.timestamp,
            v: auris.valence,
            a: auris.arousal
          };
          ingestAffect(affect);
        }
      });
      
      console.log(`🧠 Ingested ${allData.length} items into HNC`);
    } catch (error) {
      console.warn('Auris classification failed, using fallback:', error);
    }
  }
}

// Start polling
let intervalId: number;

export function startNewsWorker() {
  if (intervalId) return;
  
  // Initial fetch
  pollAllSources();
  
  // Poll every 2 minutes
  intervalId = setInterval(pollAllSources, 2 * 60 * 1000);
}

export function stopNewsWorker() {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = 0;
  }
}