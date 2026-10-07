export type Trend = 'up' | 'down' | 'flat';

export interface HarbourRecord {
  id: number;
  name: string;
  district: string;
  status: string;
}

export interface StatItem {
  label: string;
  value: string;
  change: string;
  trend: Trend;
  /** Empty unless the backend supplies a genuine historical series. */
  spark: number[];
  icon: string;
}

export interface MarketRecord {
  id: number;
  speciesId: number;
  species: string;
  harbour: string;
  pricePerKg: number;
  minPrice: number;
  maxPrice: number;
  demandKg: number | null;
  recordedAt: string | null;
  freshness: 'LIVE' | 'RECENT' | 'HISTORICAL';
  isDemo: boolean;
}

export interface VesselRecord {
  id: string;
  name: string;
  type: string;
  harbour: string;
  arrival: string;
  catchKg: number;
  status: string;
  value: string;
}

export interface LandingRecord {
  id: number;
  harbour: string;
  species: string;
  volume: number;
  landingTime: string | null;
  isDemo: boolean;
}

export interface FacilityRecord {
  name: string;
  harbour: string;
  status: string;
  available: number | null;
  capacity: number | null;
  unit: string;
  isDemo: boolean;
}

export interface BuyerRecord {
  id: number;
  name: string;
  organization: string | null;
  status: string;
  isDemo: boolean;
}

export interface AnnouncementRecord {
  id: number;
  title: string;
  message: string;
  time: string;
  isDemo: boolean;
}

export interface AlertItem {
  id: number;
  level: 'info' | 'warning' | 'critical';
  title: string;
  detail: string;
  time: string;
  isDemo: boolean;
}

export interface ConditionRecord {
  label: string;
  value: string;
  detail: string;
  status: 'available' | 'limited' | 'unavailable';
}

export interface DashboardSnapshot {
  stats: StatItem[];
  markets: MarketRecord[];
  /** The existing API has no vessel or AIS endpoint. */
  vessels: VesselRecord[];
  landings: LandingRecord[];
  facilities: FacilityRecord[];
  buyers: BuyerRecord[];
  announcements: AnnouncementRecord[];
  alerts: AlertItem[];
  conditions: ConditionRecord[];
  isDemo: boolean;
}
