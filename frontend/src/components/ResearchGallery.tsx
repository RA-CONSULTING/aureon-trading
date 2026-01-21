import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface ResearchImage {
  url: string;
  title: string;
  description: string;
  category: string;
}

const researchImages: ResearchImage[] = [
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678949190_d56a6bae.png",
    title: "Personal Field Resonance",
    description: "Individual harmonic field visualization showing consciousness-field interaction patterns",
    category: "field"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678951056_411745c5.png",
    title: "Harmonic Flow Dynamics",
    description: "Colorful wave patterns representing energy flow and resonance propagation",
    category: "visualization"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678952425_cdd8e692.png",
    title: "Ireland Field Mapping",
    description: "Geomagnetic field visualization over Ireland showing harmonic resonance patterns",
    category: "field"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678953646_75318803.png",
    title: "Consciousness Entanglement",
    description: "Two-person field interaction with infinity symbol representing quantum entanglement",
    category: "consciousness"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678954939_a952920c.png",
    title: "HNC Research Validation",
    description: "Scientific poster detailing Harmonic Nexus Core empirical validation studies",
    category: "research"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678956511_78b5f407.png",
    title: "Global Coherence Wave",
    description: "Replicated global coherence experiments showing +3.5% and +3.9% shifts",
    category: "research"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678958058_7f2abcf9.png",
    title: "Unity Broadcast Results",
    description: "Field-level proof of conscious coherence transmission through HNC",
    category: "research"
  },
  {
    url: "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756678959360_2f00e6a6.png",
    title: "Breakthrough Field Experiment",
    description: "Complete field experiment results showing 23.4% coherence increase",
    category: "research"
  }
];

interface ResearchGalleryProps {
  category?: string;
}

export default function ResearchGallery({ category }: ResearchGalleryProps) {
  const filteredImages = category 
    ? researchImages.filter(img => img.category === category)
    : researchImages;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {filteredImages.map((image, index) => (
        <Card key={index} className="overflow-hidden hover:shadow-lg transition-shadow bg-slate-700/50 border-slate-600">
          <div className="aspect-video relative">
            <img
              src={image.url}
              alt={image.title}
              className="w-full h-full object-cover"
            />
          </div>
          <CardContent className="p-3">
            <h3 className="font-semibold text-sm mb-1 text-white">{image.title}</h3>
            <p className="text-xs text-gray-300">{image.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}