export interface Country {
  id: string;
  name: string;
  regionId: string;
  capital: string;
  population: number;
  area: number;
  currency: string;
  languages: string[];
  imageUrl: string;
  coordinates: { lat: number; lng: number };
  timeZone: string;
  gdp: number;
  continent: string;
}

export interface Capital {
  id: string;
  name: string;
  countryId: string;
  population: number;
  area: number;
  coordinates: { lat: number; lng: number };
  timeZone: string;
  founded: string;
  imageUrl: string;
  landmarks: string[];
  economicCenter: boolean;
}

export const COUNTRIES: Country[] = [
  {
    id: 'usa',
    name: 'United States',
    regionId: 'north-america',
    capital: 'Washington D.C.',
    population: 331900000,
    area: 9833517,
    currency: 'USD',
    languages: ['English'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321848245_002d84a2.webp',
    coordinates: { lat: 39.8283, lng: -98.5795 },
    timeZone: 'UTC-5 to UTC-10',
    gdp: 21430000000000,
    continent: 'Americas'
  },
  {
    id: 'canada',
    name: 'Canada',
    regionId: 'north-america',
    capital: 'Ottawa',
    population: 38000000,
    area: 9984670,
    currency: 'CAD',
    languages: ['English', 'French'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321850067_dc772071.webp',
    coordinates: { lat: 56.1304, lng: -106.3468 },
    timeZone: 'UTC-3.5 to UTC-8',
    gdp: 1736000000000,
    continent: 'Americas'
  },
  {
    id: 'uk',
    name: 'United Kingdom',
    regionId: 'europe',
    capital: 'London',
    population: 67500000,
    area: 243610,
    currency: 'GBP',
    languages: ['English'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321852159_a84ce6f6.webp',
    coordinates: { lat: 55.3781, lng: -3.4360 },
    timeZone: 'UTC+0',
    gdp: 2830000000000,
    continent: 'Europe'
  },
  {
    id: 'france',
    name: 'France',
    regionId: 'europe',
    capital: 'Paris',
    population: 67400000,
    area: 643801,
    currency: 'EUR',
    languages: ['French'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321854236_d0ba260c.webp',
    coordinates: { lat: 46.2276, lng: 2.2137 },
    timeZone: 'UTC+1',
    gdp: 2630000000000,
    continent: 'Europe'
  }
];

export const CAPITALS: Capital[] = [
  {
    id: 'washington-dc',
    name: 'Washington D.C.',
    countryId: 'usa',
    population: 705000,
    area: 177,
    coordinates: { lat: 38.9072, lng: -77.0369 },
    timeZone: 'UTC-5',
    founded: '1790',
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321858274_c0ed4e79.webp',
    landmarks: ['White House', 'Capitol Building', 'Lincoln Memorial'],
    economicCenter: false
  },
  {
    id: 'ottawa',
    name: 'Ottawa',
    countryId: 'canada',
    population: 994837,
    area: 2790,
    coordinates: { lat: 45.4215, lng: -75.6972 },
    timeZone: 'UTC-5',
    founded: '1826',
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321860561_832a6bdc.webp',
    landmarks: ['Parliament Hill', 'Rideau Canal', 'National Gallery'],
    economicCenter: false
  },
  {
    id: 'london',
    name: 'London',
    countryId: 'uk',
    population: 9000000,
    area: 1572,
    coordinates: { lat: 51.5074, lng: -0.1278 },
    timeZone: 'UTC+0',
    founded: '43 AD',
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321862398_c2133aa1.webp',
    landmarks: ['Big Ben', 'Tower Bridge', 'Buckingham Palace'],
    economicCenter: true
  },
  {
    id: 'paris',
    name: 'Paris',
    countryId: 'france',
    population: 2161000,
    area: 105,
    coordinates: { lat: 48.8566, lng: 2.3522 },
    timeZone: 'UTC+1',
    founded: '3rd century BC',
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756321864539_e96f802d.webp',
    landmarks: ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame'],
    economicCenter: true
  }
];