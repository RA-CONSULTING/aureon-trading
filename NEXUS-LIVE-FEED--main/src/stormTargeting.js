const severityOrder = { Extreme: 4, Severe: 3, Moderate: 2, Minor: 1, Unknown: 0 };

/**
 * Find and target the most severe active storm using NOAA weather alerts.
 *
 * @param {Function} fetchFn optional fetch implementation for testing
 * @returns {Promise<Object|null>} storm data or null if none found
 */
async function findAndTargetStorm(fetchFn = fetch) {
  const url = 'https://api.weather.gov/alerts/active?status=actual&message_type=alert';
  const response = await fetchFn(url, {
    headers: {
      'User-Agent': 'NEXUS-LIVE-FEED/1.0 (support@nexus.example)'
    }
  });
  const json = await response.json();
  const features = json.features || [];
  if (features.length === 0) {
    return null;
  }
  const storms = features.map(f => ({
    id: f.id,
    headline: f.properties && f.properties.headline,
    severity: f.properties && f.properties.severity || 'Unknown',
    event: f.properties && f.properties.event
  }));
  storms.sort((a, b) => (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0));
  return storms[0];
}

module.exports = { findAndTargetStorm };
