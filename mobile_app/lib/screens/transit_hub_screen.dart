import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/places_autocomplete_field.dart';
import '../widgets/google_map_view.dart';

class TransitHubScreen extends StatefulWidget {
  const TransitHubScreen({super.key});

  @override
  State<TransitHubScreen> createState() => _TransitHubScreenState();
}

class _TransitHubScreenState extends State<TransitHubScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transit Hub & Schedules', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppTheme.bmtcColor,
          unselectedLabelColor: AppTheme.getMuted(isDark),
          indicatorColor: AppTheme.bmtcColor,
          tabs: const [
            Tab(icon: Icon(Icons.alt_route_rounded), text: 'Route Lookup'),
            Tab(icon: Icon(Icons.schedule_rounded), text: 'Timetables'),
            Tab(icon: Icon(Icons.directions_bus_rounded), text: 'Direct Buses'),
            Tab(icon: Icon(Icons.departure_board_rounded), text: 'Stop Arrivals'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          BusRouteLookupTabView(),
          TimetableTabView(),
          AllBusesTabView(),
          StopArrivalsTabView(),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// TAB 1: BUS ROUTE LOOKUP WITH INTERACTIVE MAP
// ─────────────────────────────────────────────────────────────
class BusRouteLookupTabView extends StatefulWidget {
  const BusRouteLookupTabView({super.key});

  @override
  State<BusRouteLookupTabView> createState() => _BusRouteLookupTabViewState();
}

class _BusRouteLookupTabViewState extends State<BusRouteLookupTabView> {
  final _controller = TextEditingController(text: '500D');
  final fm.MapController _mapController = fm.MapController();
  Map<String, dynamic>? _data;
  List<ll.LatLng> _routePoints = [];
  bool _loading = false;
  String? _error;

  static const Map<String, ll.LatLng> _knownCoords = {
    'majestic': ll.LatLng(12.9767, 77.5713),
    'indiranagar': ll.LatLng(12.9784, 77.6408),
    'whitefield': ll.LatLng(12.9698, 77.7500),
    'electronic city': ll.LatLng(12.8452, 77.6602),
    'silk board': ll.LatLng(12.9174, 77.6238),
    'hebbal': ll.LatLng(13.0358, 77.5970),
    'banashankari': ll.LatLng(12.9255, 77.5739),
    'yeshwantpur': ll.LatLng(13.0238, 77.5529),
    'koramangala': ll.LatLng(12.9352, 77.6245),
    'marathahalli': ll.LatLng(12.9591, 77.6974),
    'btm layout': ll.LatLng(12.9166, 77.6101),
  };

  @override
  void initState() {
    super.initState();
    _search();
  }

  Future<void> _search() async {
    final q = _controller.text.trim();
    if (q.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _routePoints = [];
    });

    final res = await ApiService.fetchRouteDetails(q);
    if (!mounted) return;

    if (res != null && res['route'] != null) {
      final stops = (res['stops'] as List<dynamic>?)?.cast<String>() ?? [];
      final uniqueStops = stops.toSet().toList();

      final coordsRes = await ApiService.fetchStopCoords(uniqueStops);
      final coords = coordsRes?['coordinates'] as Map<String, dynamic>? ?? {};

      final List<ll.LatLng> points = [];
      for (final s in uniqueStops) {
        if (coords.containsKey(s)) {
          final c = coords[s] as Map<String, dynamic>;
          final lat = (c['lat'] as num?)?.toDouble();
          final lng = (c['lng'] as num?)?.toDouble();
          if (lat != null && lng != null) points.add(ll.LatLng(lat, lng));
        } else {
          final n = s.toLowerCase();
          for (final e in _knownCoords.entries) {
            if (n.contains(e.key) || e.key.contains(n)) {
              points.add(e.value);
              break;
            }
          }
        }
      }

      if (points.isEmpty) {
        points.addAll([const ll.LatLng(13.0358, 77.5970), const ll.LatLng(12.9174, 77.6238)]);
      }

      setState(() {
        _loading = false;
        _data = res;
        _routePoints = points;
      });

      if (_routePoints.length >= 2) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          try {
            final bounds = fm.LatLngBounds.fromPoints(_routePoints);
            _mapController.fitCamera(fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(30)));
          } catch (_) {}
        });
      }
    } else {
      setState(() {
        _loading = false;
        _error = 'No route details found for "$q".';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  labelText: 'SEARCH BMTC ROUTE',
                  hintText: 'e.g. 500D, 335E, KIA-8, G-4',
                  prefixIcon: const Icon(Icons.search_rounded),
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onSubmitted: (_) => _search(),
              ),
            ),
            const SizedBox(width: 10),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.bmtcColor,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              ),
              onPressed: _search,
              child: const Text('Search'),
            ),
          ],
        ),
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
        else if (_error != null)
          Center(child: Text(_error!, style: TextStyle(color: mutedColor)))
        else if (_data != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.getBorder(isDark)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Route: ${_data!['route']}',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: textColor),
                    ),
                    PillBadge(
                      text: (_data!['route']?.toString().toUpperCase().startsWith('KIA') ?? false)
                          ? 'VAYU VAJRA'
                          : 'BMTC BUS',
                      color: AppTheme.bmtcColor,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  '${_data!['origin'] ?? 'Origin'} ➔ ${_data!['destination'] ?? 'Destination'}',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.bmtcColor),
                ),
                if (_data!['distance'] != null) ...[
                  const SizedBox(height: 4),
                  Text('Total Distance: ${_data!['distance']} km', style: TextStyle(fontSize: 12, color: mutedColor)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Map View of the Bus Route
          if (_routePoints.isNotEmpty) ...[
            GoogleMapView(
              points: _routePoints,
              routeColor: AppTheme.bmtcColor,
              height: 190,
            ),
            const SizedBox(height: 14),
          ],

          // Stops List
          if (_data!['stops'] is List) ...[
            Text('STOPS IN SEQUENCE (${(_data!['stops'] as List).length} STOPS)',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: (_data!['stops'] as List).length,
                separatorBuilder: (context, index) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final stop = (_data!['stops'] as List)[index];
                  final isEndpoint = index == 0 || index == (_data!['stops'] as List).length - 1;

                  return ListTile(
                    dense: true,
                    leading: CircleAvatar(
                      radius: 12,
                      backgroundColor: isEndpoint
                          ? AppTheme.bmtcColor
                          : AppTheme.bmtcColor.withValues(alpha: 0.15),
                      child: Text(
                        '${index + 1}',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isEndpoint ? Colors.white : AppTheme.bmtcColor,
                        ),
                      ),
                    ),
                    title: Text(
                      stop.toString(),
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: isEndpoint ? FontWeight.bold : FontWeight.w500,
                        color: textColor,
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────
// TAB 2: TIMETABLES (METRO & BMTC)
// ─────────────────────────────────────────────────────────────
class TimetableTabView extends StatelessWidget {
  const TimetableTabView({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            const Icon(Icons.subway_rounded, color: AppTheme.metroColor, size: 20),
            const SizedBox(width: 8),
            Text(
              'NAMMA METRO TIMETABLE & FREQUENCY',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
            ),
          ],
        ),
        const SizedBox(height: 10),

        _buildMetroLineCard('Purple Line (Challaghatta ↔ Whitefield)', '05:00 AM – 11:00 PM', 'Peak: Every 4–5 min · Off-peak: Every 8–10 min', const Color(0xFF8B5CF6), isDark),
        const SizedBox(height: 10),
        _buildMetroLineCard('Green Line (Silk Institute ↔ Nagasandra)', '05:00 AM – 11:00 PM', 'Peak: Every 5–6 min · Off-peak: Every 8–10 min', const Color(0xFF10B981), isDark),
        const SizedBox(height: 10),
        _buildMetroLineCard('Yellow Line (RV Road ↔ Bommasandra)', '05:30 AM – 10:30 PM', 'Peak: Every 6–8 min · Off-peak: Every 12 min', const Color(0xFFEAB308), isDark),

        const SizedBox(height: 24),

        Row(
          children: [
            const Icon(Icons.directions_bus_rounded, color: AppTheme.bmtcColor, size: 20),
            const SizedBox(width: 8),
            Text(
              'MAJOR BMTC CORRIDOR FREQUENCIES',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.getBorder(isDark)),
          ),
          child: Column(
            children: [
              _buildBmtcScheduleRow('500D (Hebbal ↔ Silk Board via ORR)', 'Every 3–5 min', '24x7 Active', textColor),
              const Divider(height: 16),
              _buildBmtcScheduleRow('335E (Majestic ↔ Kadugodi via Whitefield)', 'Every 8–10 min', '05:30 AM – 11:00 PM', textColor),
              const Divider(height: 16),
              _buildBmtcScheduleRow('KIA-8 (Electronic City ↔ Airport)', 'Every 20 min', '24x7 Active', textColor),
              const Divider(height: 16),
              _buildBmtcScheduleRow('G-4 (Brigade Rd ↔ Bannerghatta Zoo)', 'Every 12 min', '06:00 AM – 10:00 PM', textColor),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMetroLineCard(String lineName, String hours, String freq, Color color, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDark ? 0.15 : 0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(lineName, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
              PillBadge(text: 'ACTIVE', color: color, isSmall: true),
            ],
          ),
          const SizedBox(height: 6),
          Text('Operating Hours: $hours', style: const TextStyle(fontSize: 12)),
          const SizedBox(height: 2),
          Text('Frequency: $freq', style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
        ],
      ),
    );
  }

  Widget _buildBmtcScheduleRow(String route, String freq, String hours, Color textColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(route, style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12, color: textColor)),
              Text('Hours: $hours', style: const TextStyle(fontSize: 10, color: Colors.grey)),
            ],
          ),
        ),
        PillBadge(text: freq, color: AppTheme.bmtcColor, isSmall: true),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────
// TAB 3: DIRECT ALL BUSES WITH AUTOCOMPLETE
// ─────────────────────────────────────────────────────────────
class AllBusesTabView extends StatefulWidget {
  const AllBusesTabView({super.key});

  @override
  State<AllBusesTabView> createState() => _AllBusesTabViewState();
}

class _AllBusesTabViewState extends State<AllBusesTabView> {
  final _srcCtrl = TextEditingController(text: 'Majestic');
  final _dstCtrl = TextEditingController(text: 'Indiranagar');
  Map<String, dynamic>? _data;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _search();
  }

  Future<void> _search() async {
    final s = _srcCtrl.text.trim();
    final d = _dstCtrl.text.trim();
    if (s.isEmpty || d.isEmpty) return;

    setState(() => _loading = true);
    final res = await ApiService.fetchAllBuses(source: s, destination: d);
    if (mounted) {
      setState(() {
        _data = res;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final directBuses = _data?['direct_buses'] as List<dynamic>? ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Column(
          children: [
            PlacesAutocompleteField(
              controller: _srcCtrl,
              label: 'FROM (ORIGIN)',
              icon: Icons.trip_origin_rounded,
              iconColor: AppTheme.green,
              onPlaceSelected: (name, lat, lng) => _search(),
            ),
            const SizedBox(height: 10),
            PlacesAutocompleteField(
              controller: _dstCtrl,
              label: 'TO (DESTINATION)',
              icon: Icons.location_on_rounded,
              iconColor: AppTheme.red,
              onPlaceSelected: (name, lat, lng) => _search(),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.bmtcColor,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: _search,
                icon: const Icon(Icons.search_rounded, size: 18),
                label: const Text('Find Direct Bus Routes', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
        else if (directBuses.isEmpty)
          Center(child: Text('No direct buses found between these stops.', style: TextStyle(color: mutedColor)))
        else ...[
          Text('DIRECT BUS ROUTES (${directBuses.length} FOUND)',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
          const SizedBox(height: 8),
          ...directBuses.map((b) {
            final routeName = b['route']?.toString() ?? 'BMTC';
            final isVajra = routeName.toUpperCase().startsWith('V-') || routeName.toUpperCase().startsWith('KIA');
            final fare = b['fare'] ?? (isVajra ? 45 : 20);

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: (isVajra ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(Icons.directions_bus_rounded, color: isVajra ? AppTheme.blue : AppTheme.bmtcColor, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(routeName, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: textColor)),
                        Text(isVajra ? 'Volvo AC Express' : 'BMTC Ordinary', style: TextStyle(fontSize: 11, color: mutedColor)),
                      ],
                    ),
                  ),
                  PillBadge(text: '₹$fare', color: AppTheme.green),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────
// TAB 4: STOP ARRIVALS WITH AUTOCOMPLETE
// ─────────────────────────────────────────────────────────────
class StopArrivalsTabView extends StatefulWidget {
  const StopArrivalsTabView({super.key});

  @override
  State<StopArrivalsTabView> createState() => _StopArrivalsTabViewState();
}

class _StopArrivalsTabViewState extends State<StopArrivalsTabView> {
  final _ctrl = TextEditingController(text: 'Majestic');
  Map<String, dynamic>? _data;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _search();
  }

  Future<void> _search() async {
    final s = _ctrl.text.trim();
    if (s.isEmpty) return;

    setState(() => _loading = true);
    final res = await ApiService.fetchStopArrivals(s);
    if (mounted) {
      setState(() {
        _data = res;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final arrivals = _data?['arrivals'] as List<dynamic>? ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        PlacesAutocompleteField(
          controller: _ctrl,
          label: 'BUS STOP NAME',
          hint: 'e.g. Majestic, Indiranagar, Silk Board',
          icon: Icons.pin_drop_rounded,
          iconColor: AppTheme.bmtcColor,
          onPlaceSelected: (name, lat, lng) => _search(),
          onSubmitted: _search,
        ),
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
        else if (arrivals.isEmpty)
          Center(child: Text('No upcoming live arrivals found for this stop.', style: TextStyle(color: mutedColor)))
        else ...[
          Text('UPCOMING BUS ARRIVALS',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
          const SizedBox(height: 8),
          ...arrivals.map((a) {
            final route = a['route']?.toString() ?? 'BMTC';
            final eta = a['eta_mins'] ?? 5;
            final dest = a['destination']?.toString() ?? 'Destination';

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: AppTheme.bmtcColor.withValues(alpha: 0.15),
                    child: const Icon(Icons.directions_bus, color: AppTheme.bmtcColor, size: 18),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Route $route', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor)),
                        Text('Towards: $dest', style: TextStyle(fontSize: 11, color: mutedColor)),
                      ],
                    ),
                  ),
                  PillBadge(text: 'in $eta min', color: AppTheme.green),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }
}
