import { Region } from '@/components/RegionCard';

export const REGIONS: Region[] = [
  {
    id: 'north-america',
    name: 'North America',
    continent: 'Americas',
    population: 579000000,
    area: 24709000,
    climate: 'Varied - Arctic to Tropical',
    languages: ['English', 'Spanish', 'French'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320814766_52ed716f.webp',
    coordinates: { lat: 45.0, lng: -100.0 },
    timeZone: 'UTC-5 to UTC-10',
    currency: 'USD, CAD, MXN'
  },
  {
    id: 'south-america',
    name: 'South America',
    continent: 'Americas',
    population: 434000000,
    area: 17840000,
    climate: 'Tropical to Temperate',
    languages: ['Spanish', 'Portuguese', 'English'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320816804_cd0e6934.webp',
    coordinates: { lat: -15.0, lng: -60.0 },
    timeZone: 'UTC-2 to UTC-5',
    currency: 'BRL, ARS, COP'
  },
  {
    id: 'europe',
    name: 'Europe',
    continent: 'Europe',
    population: 748000000,
    area: 10180000,
    climate: 'Temperate to Subarctic',
    languages: ['English', 'German', 'French', 'Italian'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320819037_7fe0af01.webp',
    coordinates: { lat: 54.0, lng: 15.0 },
    timeZone: 'UTC+0 to UTC+3',
    currency: 'EUR, GBP, CHF'
  },
  {
    id: 'asia',
    name: 'Asia',
    continent: 'Asia',
    population: 4641000000,
    area: 44579000,
    climate: 'Arctic to Tropical',
    languages: ['Mandarin', 'Hindi', 'Arabic', 'Japanese'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320820954_290b1b72.webp',
    coordinates: { lat: 30.0, lng: 100.0 },
    timeZone: 'UTC+5 to UTC+9',
    currency: 'CNY, JPY, INR'
  },
  {
    id: 'africa',
    name: 'Africa',
    continent: 'Africa',
    population: 1340000000,
    area: 30370000,
    climate: 'Tropical to Arid',
    languages: ['Arabic', 'Swahili', 'French', 'English'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320823107_9eccb346.webp',
    coordinates: { lat: 0.0, lng: 20.0 },
    timeZone: 'UTC+0 to UTC+4',
    currency: 'ZAR, EGP, NGN'
  },
  {
    id: 'oceania',
    name: 'Oceania',
    continent: 'Oceania',
    population: 45000000,
    area: 8600000,
    climate: 'Tropical to Temperate',
    languages: ['English', 'Tok Pisin', 'French'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320825194_3c3aec82.webp',
    coordinates: { lat: -25.0, lng: 140.0 },
    timeZone: 'UTC+8 to UTC+13',
    currency: 'AUD, NZD, FJD'
  },
  {
    id: 'antarctica',
    name: 'Antarctica',
    continent: 'Antarctica',
    population: 5000,
    area: 14200000,
    climate: 'Polar',
    languages: ['English', 'Russian', 'Spanish'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320827293_c2e6073f.webp',
    coordinates: { lat: -90.0, lng: 0.0 },
    timeZone: 'All time zones',
    currency: 'Research stations'
  },
  {
    id: 'arctic',
    name: 'Arctic Region',
    continent: 'Arctic',
    population: 4000000,
    area: 21000000,
    climate: 'Polar',
    languages: ['English', 'Russian', 'Inuit'],
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/68a080d9d73c7b43a9733c1d_1756320829527_caeaf5c5.webp',
    coordinates: { lat: 90.0, lng: 0.0 },
    timeZone: 'All time zones',
    currency: 'Various'
  }
];