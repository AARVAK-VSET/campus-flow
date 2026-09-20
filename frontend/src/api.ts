import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
});

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface ProviderQuote {
  provider: string;
  provider_name: string;
  base_fare: number;
  per_km_rate: number;
  estimated_fare: number;
}

export interface EmergencyQuote {
  currency: string;
  distance_km: number;
  quotes: ProviderQuote[];
}

// Distance and fares are computed and validated by the backend dispatch service.
export const fetchEmergencyQuote = async (pickup: GeoPoint, dropoff: GeoPoint): Promise<EmergencyQuote> => {
  const res = await api.post<EmergencyQuote>('dispatch/emergency-quote', { pickup, dropoff });
  return res.data;
};

export default api;
