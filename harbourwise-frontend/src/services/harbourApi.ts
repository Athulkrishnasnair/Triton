import type {
  AlertItem,
  AnnouncementRecord,
  BuyerRecord,
  ConditionRecord,
  DashboardSnapshot,
  FacilityRecord,
  HarbourRecord,
  LandingRecord,
  MarketRecord,
  StatItem,
} from '@/data/dashboard';

interface ApiErrorPayload {
  error?: string | { message?: string; code?: string };
}

interface BackendLanding {
  id: number;
  harbour: string;
  species: string;
  quantity_kg: number;
  landing_time: string | null;
  is_demo_data?: boolean;
}

interface BackendPrice {
  id: number;
  harbour_id: number;
  harbour: string;
  species_id: number;
  species: string;
  average_price: number;
  min_price: number;
  max_price: number;
  recorded_at: string | null;
  freshness?: string;
  is_demo_data?: boolean;
}

interface BackendDemand {
  species_id: number;
  remaining_quantity_kg: number;
  is_demo_data?: boolean;
}

interface BackendBuyer {
  id: number;
  name: string;
  organization: string | null;
  status: string;
  is_demo_data?: boolean;
}

interface BackendAnnouncement {
  id: number;
  title: string;
  message: string;
  published_at: string | null;
  source?: string;
  is_demo_data?: boolean;
}

interface BackendAlert {
  id: number;
  title: string;
  message: string;
  severity: string;
  created_at: string | null;
  is_demo_data?: boolean;
}

interface BackendIce {
  capacity_tonnes: number;
  available_tonnes: number;
  status: string;
  is_demo_data?: boolean;
}

interface BackendStorage {
  capacity_tonnes: number;
  available_tonnes: number;
  status: string;
  is_demo_data?: boolean;
}

interface BackendDashboard {
  harbour: HarbourRecord;
  recent_landings: BackendLanding[];
  prices: BackendPrice[];
  active_auctions: unknown[];
  active_buyers: BackendBuyer[];
  buyer_demand: BackendDemand[];
  ice: BackendIce | null;
  cold_storage: BackendStorage | null;
  announcements: BackendAnnouncement[];
  active_alerts: BackendAlert[];
}

export class HarbourApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = 'HarbourApiError';
  }
}

function apiBaseUrl(): string {
  const value = import.meta.env.VITE_API_BASE_URL?.trim().replace(/\/+$/, '');
  if (!value) {
    throw new HarbourApiError('VITE_API_BASE_URL is not set. Copy .env.example to .env.local and set the backend URL.');
  }
  return value;
}

async function requestJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'include',
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new HarbourApiError('The KALASTUS backend could not be reached. Check that it is running and that its URL is correct.');
  }

  const bodyText = await response.text();
  let payload: unknown;
  try {
    payload = bodyText ? JSON.parse(bodyText) : null;
  } catch {
    throw new HarbourApiError(`The backend returned invalid JSON (HTTP ${response.status}).`, response.status);
  }

  if (!response.ok) {
    const body = payload as ApiErrorPayload | null;
    const error = body?.error;
    const message = typeof error === 'string' ? error : error?.message;
    throw new HarbourApiError(message || `The backend request failed (HTTP ${response.status}).`, response.status);
  }
  if (payload === null || typeof payload !== 'object') {
    throw new HarbourApiError('The backend returned an empty or invalid response.', response.status);
  }
  return payload as T;
}

export async function getHealth(signal?: AbortSignal): Promise<void> {
  await requestJson<{ status: string; service: string }>('/api/health', signal);
}

export async function getHarbours(signal?: AbortSignal): Promise<HarbourRecord[]> {
  const payload = await requestJson<{ harbours: HarbourRecord[] }>('/api/harbours', signal);
  return payload.harbours;
}

async function getHarbourDashboard(harbourId: number, signal?: AbortSignal): Promise<BackendDashboard> {
  return requestJson<BackendDashboard>(`/api/harbours/${harbourId}/dashboard`, signal);
}

function formatLocalTime(value: string | null): string {
  if (!value) return 'Time unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Time unavailable';
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function isTodayInKerala(value: string | null): boolean {
  if (!value) return false;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const formatter = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' });
  return formatter.format(date) === formatter.format(new Date());
}

function relativeTime(value: string | null): string {
  if (!value) return 'Time unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Time unavailable';
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60_000));
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.floor(hours / 24)} days ago`;
}

function displayQuantity(value: number): string {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(value);
}

function statusLabel(value: string | undefined): string {
  if (!value) return 'Not reported';
  return value.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function uniqueById<T extends { id: number }>(items: T[]): T[] {
  return [...new Map(items.map((item) => [item.id, item])).values()];
}

function toAlerts(items: BackendAlert[]): AlertItem[] {
  return items.map((item) => ({
    id: item.id,
    level: item.severity.toLowerCase() === 'critical'
      ? 'critical'
      : item.severity.toLowerCase() === 'warning' ? 'warning' : 'info',
    title: item.title,
    detail: item.message,
    time: relativeTime(item.created_at),
    isDemo: Boolean(item.is_demo_data),
  }));
}

function toAnnouncements(items: BackendAnnouncement[]): AnnouncementRecord[] {
  return items.map((item) => ({
    id: item.id,
    title: item.title,
    message: item.message,
    time: formatLocalTime(item.published_at),
    isDemo: Boolean(item.is_demo_data || item.source === 'DEMO'),
  }));
}

function toConditions(dashboards: BackendDashboard[]): ConditionRecord[] {
  const iceRows = dashboards.filter((item) => item.ice);
  const iceAvailable = iceRows.reduce((sum, item) => sum + (item.ice?.available_tonnes || 0), 0);
  const iceStatus = iceRows.some((item) => item.ice?.status === 'LIMITED')
    ? 'limited'
    : iceRows.length ? 'available' : 'unavailable';
  const demandKg = dashboards.reduce((sum, item) => sum + item.buyer_demand.reduce(
    (subtotal, demand) => subtotal + demand.remaining_quantity_kg,
    0,
  ), 0);

  return [
    { label: 'Weather', value: 'Unavailable', detail: 'No weather endpoint in backend', status: 'unavailable' },
    {
      label: 'Ice Supply',
      value: iceRows.length ? `${displayQuantity(iceAvailable)} t available` : 'No records',
      detail: iceRows.length ? `${iceRows.length} harbour report(s)` : 'No ice data returned',
      status: iceStatus,
    },
    {
      label: 'Buyer Demand',
      value: demandKg ? `${displayQuantity(demandKg)} kg open` : 'No demand records',
      detail: 'Remaining quantity from buyer demand records',
      status: demandKg ? 'available' : 'unavailable',
    },
    { label: 'Sea State', value: 'Unavailable', detail: 'No sea-state endpoint in backend', status: 'unavailable' },
  ];
}

function makeStats(
  landings: LandingRecord[],
): StatItem[] {
  const currentLandings = landings.filter((landing) => isTodayInKerala(landing.landingTime));
  const totalKg = currentLandings.reduce((sum, landing) => sum + landing.volume, 0);
  const unavailable = 'Not provided by API';

  return [
    { label: 'Active Vessels', value: '—', change: unavailable, trend: 'flat', spark: [], icon: 'ship' },
    {
      label: "Today's Landings",
      value: currentLandings.length ? `${displayQuantity(totalKg)} kg` : 'No records',
      change: currentLandings.length ? `${currentLandings.length} record(s)` : 'No landing reported today',
      trend: 'flat',
      spark: [],
      icon: 'anchor',
    },
    { label: 'Market Index', value: '—', change: unavailable, trend: 'flat', spark: [], icon: 'trending-up' },
    { label: 'Harbour Slots Filled', value: '—', change: unavailable, trend: 'flat', spark: [], icon: 'map-pin' },
  ];
}

export async function loadDashboardSnapshot(
  harbours: HarbourRecord[],
  selectedHarbour: string,
  signal?: AbortSignal,
): Promise<DashboardSnapshot> {
  const selected = selectedHarbour === 'All Harbours'
    ? harbours
    : harbours.filter((harbour) => harbour.name === selectedHarbour);
  const dashboards = await Promise.all(selected.map((harbour) => getHarbourDashboard(harbour.id, signal)));

  const landingRows = dashboards.flatMap((dashboard) => dashboard.recent_landings);
  const buyerRows = uniqueById(dashboards.flatMap((dashboard) => dashboard.active_buyers));
  const demandByHarbourAndSpecies = new Map<string, number>();
  dashboards.forEach((dashboard) => dashboard.buyer_demand.forEach((demand) => {
    const key = `${dashboard.harbour.id}:${demand.species_id}`;
    demandByHarbourAndSpecies.set(key, (demandByHarbourAndSpecies.get(key) || 0) + demand.remaining_quantity_kg);
  }));

  const markets: MarketRecord[] = dashboards.flatMap((dashboard) => dashboard.prices.map((price) => ({
    id: price.id,
    speciesId: price.species_id,
    species: price.species,
    harbour: price.harbour,
    pricePerKg: price.average_price,
    minPrice: price.min_price,
    maxPrice: price.max_price,
    demandKg: demandByHarbourAndSpecies.get(`${price.harbour_id}:${price.species_id}`) ?? null,
    recordedAt: price.recorded_at,
    freshness: price.freshness === 'LIVE' || price.freshness === 'RECENT' ? price.freshness : 'HISTORICAL',
    isDemo: Boolean(price.is_demo_data),
  })));

  const landings: LandingRecord[] = landingRows
    .filter((landing) => isTodayInKerala(landing.landing_time))
    .map((landing) => ({
      id: landing.id,
      harbour: landing.harbour,
      species: landing.species,
      volume: landing.quantity_kg,
      landingTime: landing.landing_time,
      isDemo: Boolean(landing.is_demo_data),
    }));

  const facilities: FacilityRecord[] = dashboards.flatMap((dashboard) => {
    const rows: FacilityRecord[] = [];
    if (dashboard.ice) rows.push({
      name: 'Ice Plant',
      harbour: dashboard.harbour.name,
      status: statusLabel(dashboard.ice.status),
      available: dashboard.ice.available_tonnes,
      capacity: dashboard.ice.capacity_tonnes,
      unit: 'tonnes',
      isDemo: Boolean(dashboard.ice.is_demo_data),
    });
    if (dashboard.cold_storage) rows.push({
      name: 'Cold Storage',
      harbour: dashboard.harbour.name,
      status: statusLabel(dashboard.cold_storage.status),
      available: dashboard.cold_storage.available_tonnes,
      capacity: dashboard.cold_storage.capacity_tonnes,
      unit: 'tonnes',
      isDemo: Boolean(dashboard.cold_storage.is_demo_data),
    });
    return rows;
  });

  const announcements = toAnnouncements(uniqueById(dashboards.flatMap((dashboard) => dashboard.announcements)));
  const alerts = toAlerts(uniqueById(dashboards.flatMap((dashboard) => dashboard.active_alerts)));
  const buyers: BuyerRecord[] = buyerRows.map((buyer) => ({
    id: buyer.id,
    name: buyer.name,
    organization: buyer.organization,
    status: statusLabel(buyer.status),
    isDemo: Boolean(buyer.is_demo_data),
  }));

  const sourceRows = dashboards.flatMap((dashboard) => [
    ...dashboard.recent_landings,
    ...dashboard.prices,
    ...dashboard.buyer_demand,
    ...dashboard.active_buyers,
    ...dashboard.announcements,
    ...dashboard.active_alerts,
    ...(dashboard.ice ? [dashboard.ice] : []),
    ...(dashboard.cold_storage ? [dashboard.cold_storage] : []),
  ]);
  const isDemo = sourceRows.some((record) => Boolean(record.is_demo_data));

  return {
    stats: makeStats(landings),
    markets,
    vessels: [],
    landings,
    facilities,
    buyers,
    announcements,
    alerts,
    conditions: toConditions(dashboards),
    isDemo,
  };
}
