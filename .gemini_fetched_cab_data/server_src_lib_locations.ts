export interface Location {
  id: string;
  name: string;
  area: string;
  lat: number;
  lng: number;
}

export const BENGALURU_LOCATIONS: Location[] = [
  { id: "pes_university_rr", name: "PES University (Ring Road Campus)", area: "100 Feet Ring Road, Banashankari 3rd Stage", lat: 12.9344, lng: 77.5345 },
  { id: "pes_university_ec", name: "PES University (Electronic City Campus)", area: "Hosur Road, Electronic City", lat: 12.8517, lng: 77.6654 },
  { id: "kempegowda_airport", name: "Kempegowda International Airport (BLR)", area: "Devenahalli", lat: 13.1986, lng: 77.7066 },
  { id: "majestic", name: "KSR Bengaluru Railway Station (Majestic)", area: "Majestic", lat: 12.9781, lng: 77.5697 },
  { id: "koramangala", name: "Koramangala 5th Block (Sony Signal)", area: "Koramangala", lat: 12.9352, lng: 77.6245 },
  { id: "indiranagar", name: "Indiranagar 100ft Road", area: "Indiranagar", lat: 12.9784, lng: 77.6408 },
  { id: "electronic_city", name: "Electronic City Phase 1", area: "Electronic City", lat: 12.8452, lng: 77.6602 },
  { id: "whitefield", name: "ITPB Whitefield", area: "Whitefield", lat: 12.9863, lng: 77.7381 },
  { id: "mg_road", name: "MG Road Metro Station", area: "Central Bengaluru", lat: 12.9756, lng: 77.6066 },
  { id: "hsr_layout", name: "HSR Layout BDA Complex", area: "HSR Layout", lat: 12.9116, lng: 77.6389 },
  { id: "bellandur", name: "Ecospace Park, Bellandur", area: "Outer Ring Road", lat: 12.9260, lng: 77.6762 },
  { id: "marathahalli", name: "Marathahalli Multiplex", area: "Marathahalli", lat: 12.9553, lng: 77.7009 },
  { id: "jayanagar", name: "Jayanagar 4th Block Complex", area: "Jayanagar", lat: 12.9298, lng: 77.5826 },
  { id: "banashankari", name: "Banashankari Bus Terminal", area: "Banashankari", lat: 12.9255, lng: 77.5468 },
  { id: "yeshwanthpur", name: "Yeshwanthpur Railway Station", area: "Yeshwanthpur", lat: 13.0238, lng: 77.5510 },
  { id: "hebbal", name: "Hebbal Flyover", area: "Hebbal", lat: 13.0359, lng: 77.5970 },
  { id: "yelahanka", name: "Yelahanka New Town", area: "Yelahanka", lat: 13.1007, lng: 77.5963 },
  { id: "rvce", name: "RV College of Engineering (RVCE)", area: "Mysore Road", lat: 12.9237, lng: 77.4987 },
  { id: "bmsce", name: "BMS College of Engineering", area: "Bull Temple Road, Basavanagudi", lat: 12.9410, lng: 77.5655 },
  { id: "christ_university", name: "Christ University (Main Campus)", area: "Hosur Road", lat: 12.9343, lng: 77.6060 },
  { id: "silk_board", name: "Central Silk Board Junction", area: "BTM Layout / HSR", lat: 12.9177, lng: 77.6238 },
  { id: "malleshwaram", name: "Malleshwaram 8th Cross", area: "Malleshwaram", lat: 13.0012, lng: 77.5712 },
  { id: "rajajinagar", name: "Rajajinagar Metro Station", area: "Rajajinagar", lat: 12.9984, lng: 77.5552 },
  { id: "rr_nagar", name: "Rajarajeshwari Nagar Gate", area: "RR Nagar", lat: 12.9279, lng: 77.5186 }
];

export function searchLocations(query?: string): Location[] {
  if (!query || query.trim().length === 0) {
    return BENGALURU_LOCATIONS;
  }
  const q = query.toLowerCase().trim();
  return BENGALURU_LOCATIONS.filter(
    (loc) =>
      loc.name.toLowerCase().includes(q) ||
      loc.area.toLowerCase().includes(q)
  );
}
