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

export const fetchEmergencyQuote = async (
  pickup: GeoPoint,
  dropoff: GeoPoint
): Promise<EmergencyQuote> => {
  const response = await api.post<EmergencyQuote>('dispatch/emergency-quote', {
    pickup,
    dropoff,
  });
  return response.data;
};

export default api;
