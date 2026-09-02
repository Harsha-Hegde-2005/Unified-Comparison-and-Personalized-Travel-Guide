import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/places_autocomplete_field.dart';
import '../widgets/google_map_view.dart';
import '../widgets/app_settings_modal.dart';

class TransitHubScreen extends StatefulWidget {
  final int initialTabIndex;

  const TransitHubScreen({
    super.key,
    this.initialTabIndex = 0,
  });

  @override
  State<TransitHubScreen> createState() => _TransitHubScreenState();
}

class _TransitHubScreenState extends State<TransitHubScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 4,
      vsync: this,
      initialIndex: widget.initialTabIndex.clamp(0, 3),
    );
  }

  @override
  void didUpdateWidget(TransitHubScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialTabIndex != widget.initialTabIndex) {
      _tabController.animateTo(widget.initialTabIndex.clamp(0, 3));
    }
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
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'App Settings',
            onPressed: () => showAppSettingsModal(context),
          ),
        ],
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
            Tab(icon: Icon(Icons.pin_drop_rounded), text: 'Stops Info'),
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
  String _activeMode = 'bmtc'; // 'bmtc' | 'metro'
  String _direction = 'forward'; // 'forward' | 'return'
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

  Future<void> _search([String? queryTerm]) async {
    final q = (queryTerm ?? _controller.text).trim();
    if (q.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _direction = 'forward';
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

  Color _getRouteColor(String routeName, String type) {
    if (type == 'metro' || routeName.toLowerCase().contains('line')) {
      final n = routeName.toLowerCase();
      if (n.contains('purple')) return const Color(0xFF800080);
      if (n.contains('yellow')) return const Color(0xFFD97706);
      return const Color(0xFF008000); // Green
    }
    if (routeName.toUpperCase().startsWith('KIA') || routeName.toUpperCase().startsWith('V-')) {
      return const Color(0xFF7C3AED);
    }
    return AppTheme.bmtcColor;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final metroLines = [
      {'name': 'Purple Line', 'color': const Color(0xFF800080), 'desc': 'Whitefield ↔ Challaghatta', 'stations': '37'},
      {'name': 'Green Line', 'color': const Color(0xFF008000), 'desc': 'Silk Institute ↔ Nagasandra/Madavara', 'stations': '31'},
      {'name': 'Yellow Line', 'color': const Color(0xFFD97706), 'desc': 'R.V. Road ↔ Bommasandra', 'stations': '16'},
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Mode Selector Buttons (BMTC Bus vs Namma Metro)
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _activeMode == 'bmtc' ? AppTheme.bmtcColor : cardBg,
                  foregroundColor: _activeMode == 'bmtc' ? Colors.white : textColor,
                  elevation: _activeMode == 'bmtc' ? 2 : 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: _activeMode == 'bmtc' ? AppTheme.bmtcColor : AppTheme.getBorder(isDark)),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: () {
                  setState(() {
                    _activeMode = 'bmtc';
                    _data = null;
                    _error = null;
                    _controller.text = '500D';
                  });
                  _search('500D');
                },
                icon: const Icon(Icons.directions_bus_rounded, size: 18),
                label: const Text('BMTC Bus', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _activeMode == 'metro' ? AppTheme.metroColor : cardBg,
                  foregroundColor: _activeMode == 'metro' ? Colors.white : textColor,
                  elevation: _activeMode == 'metro' ? 2 : 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: _activeMode == 'metro' ? AppTheme.metroColor : AppTheme.getBorder(isDark)),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: () {
                  setState(() {
                    _activeMode = 'metro';
                    _data = null;
                    _error = null;
                    _controller.text = 'Purple Line';
                  });
                  _search('Purple Line');
                },
                icon: const Icon(Icons.subway_rounded, size: 18),
                label: const Text('Namma Metro', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        if (_activeMode == 'bmtc') ...[
          // BMTC Route Number Input Search
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: InputDecoration(
                    labelText: 'BUS / ROUTE NUMBER',
                    hintText: 'e.g. 500D, 335E, KIA-8, 360-K',
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
                onPressed: () => _search(),
                child: const Text('Search'),
              ),
            ],
          ),
        ] else ...[
          // Namma Metro 3 Line Buttons
          Text('SELECT A NAMMA METRO LINE:',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
          const SizedBox(height: 8),
          Column(
            children: metroLines.map((line) {
              final isSelected = _data != null && _data!['route'] == line['name'];
              final lineColor = line['color'] as Color;

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                child: InkWell(
                  onTap: () {
                    _controller.text = line['name'] as String;
                    _search(line['name'] as String);
                  },
                  borderRadius: BorderRadius.circular(14),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isSelected ? lineColor.withValues(alpha: 0.12) : cardBg,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: isSelected ? lineColor : lineColor.withValues(alpha: 0.4), width: 1.5),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 12,
                          height: 36,
                          decoration: BoxDecoration(
                            color: lineColor,
                            borderRadius: BorderRadius.circular(6),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    line['name'] as String,
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: textColor),
                                  ),
                                  PillBadge(text: '${line['stations']} STATIONS', color: lineColor, isSmall: true),
                                ],
                              ),
                              const SizedBox(height: 2),
                              Text(line['desc'] as String, style: TextStyle(fontSize: 11, color: mutedColor)),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Icon(Icons.chevron_right_rounded, color: lineColor, size: 20),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
        else if (_error != null)
          Center(child: Text(_error!, style: TextStyle(color: mutedColor)))
        else if (_data != null) ...[
          // Route details header card
          Builder(
            builder: (context) {
              final rName = _data!['route']?.toString() ?? '';
              final rType = _data!['type']?.toString() ?? 'bmtc';
              final color = _getRouteColor(rName, rType);
              final stops = _direction == 'forward'
                  ? ((_data!['stops'] as List<dynamic>?)?.cast<String>() ?? [])
                  : ((_data!['reverse_stops'] as List<dynamic>?)?.cast<String>() ?? []);

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
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
                              rName,
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: textColor),
                            ),
                            PillBadge(
                              text: rType == 'metro'
                                  ? 'NAMMA METRO'
                                  : (rName.toUpperCase().startsWith('KIA') ? 'VAYU VAJRA' : 'BMTC BUS'),
                              color: color,
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          stops.isNotEmpty ? '${stops.first} ➔ ${stops.last}' : 'Route details',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: color),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Text('${stops.length} STOPS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: mutedColor)),
                            if (_data!['trips'] != null) ...[
                              Text(' · ', style: TextStyle(color: mutedColor)),
                              Text('${_data!['trips']} trips/day', style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.bold)),
                            ],
                            if (_data!['schedule'] != null) ...[
                              Text(' · ', style: TextStyle(color: mutedColor)),
                              Text('🕐 ${_data!['schedule']['departure']} → ${_data!['schedule']['arrival']}',
                                  style: TextStyle(fontSize: 11, color: mutedColor)),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Outbound / Inbound direction toggle if reverse_stops exist
                  if (_data!['reverse_stops'] is List && (_data!['reverse_stops'] as List).isNotEmpty) ...[
                    Row(
                      children: [
                        Expanded(
                          child: ChoiceChip(
                            label: const Center(child: Text('Outbound / Forward', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                            selected: _direction == 'forward',
                            selectedColor: color.withValues(alpha: 0.2),
                            onSelected: (_) => setState(() => _direction = 'forward'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ChoiceChip(
                            label: const Center(child: Text('Inbound / Return', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                            selected: _direction == 'return',
                            selectedColor: color.withValues(alpha: 0.2),
                            onSelected: (_) => setState(() => _direction = 'return'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],

                  // Map View of the Route
                  if (_routePoints.isNotEmpty) ...[
                    GoogleMapView(
                      points: _routePoints,
                      routeColor: color,
                      height: 190,
                    ),
                    const SizedBox(height: 14),
                  ],

                  // Intermediate Stops List
                  Text('STOPS IN SEQUENCE (${stops.length} STOPS)',
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
                      itemCount: stops.length,
                      separatorBuilder: (context, index) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final stop = stops[index];
                        final isEndpoint = index == 0 || index == stops.length - 1;

                        return ListTile(
                          dense: true,
                          leading: CircleAvatar(
                            radius: 12,
                            backgroundColor: isEndpoint ? color : color.withValues(alpha: 0.15),
                            child: Text(
                              '${index + 1}',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: isEndpoint ? Colors.white : color,
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
                          subtitle: isEndpoint
                              ? Text(index == 0 ? 'Start Station/Stop' : 'Destination Station/Stop',
                                  style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.bold))
                              : null,
                          trailing: isEndpoint
                              ? Icon(index == 0 ? Icons.play_circle_fill_rounded : Icons.location_on_rounded, color: color, size: 18)
                              : null,
                        );
                      },
                    ),
                  ),
                ],
              );
            },
          ),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────
// TAB 2: TIMETABLES (METRO & BMTC)
// ─────────────────────────────────────────────────────────────
class TimetableTabView extends StatefulWidget {
  const TimetableTabView({super.key});

  @override
  State<TimetableTabView> createState() => _TimetableTabViewState();
}

class _TimetableTabViewState extends State<TimetableTabView> {
  String _activeMode = 'bmtc'; // 'bmtc' | 'metro'

  // BMTC fields
  final _bmtcRouteCtrl = TextEditingController(text: '500D');
  final _bmtcStopCtrl = TextEditingController(text: 'Hebbal');
  Map<String, dynamic>? _bmtcResult;
  bool _bmtcLoading = false;
  String? _bmtcError;

  // Metro fields
  final _metroStationCtrl = TextEditingController(text: 'Indiranagar');
  Map<String, dynamic>? _metroResult;
  bool _metroLoading = false;
  String? _metroError;

  @override
  void initState() {
    super.initState();
    _searchBmtc();
  }

  Future<void> _searchBmtc() async {
    final r = _bmtcRouteCtrl.text.trim();
    final s = _bmtcStopCtrl.text.trim();
    if (r.isEmpty) return;

    setState(() {
      _bmtcLoading = true;
      _bmtcError = null;
      _bmtcResult = null;
    });

    final res = await ApiService.fetchRouteTimetable(r, s);
    if (!mounted) return;

    if (res != null && (res['departures'] != null || res['board_stop'] != null)) {
      setState(() {
        _bmtcLoading = false;
        _bmtcResult = res;
      });
    } else {
      setState(() {
        _bmtcLoading = false;
        _bmtcError = 'No timetable found for bus "$r" at stop "${s.isEmpty ? "default" : s}".';
      });
    }
  }

  Future<void> _searchMetro() async {
    final s = _metroStationCtrl.text.trim();
    if (s.isEmpty) return;

    setState(() {
      _metroLoading = true;
      _metroError = null;
      _metroResult = null;
    });

    final res = await ApiService.metroTimetable(source: s);
    if (!mounted) return;

    if (res != null && (res['departures'] != null || res['resolved_station'] != null)) {
      setState(() {
        _metroLoading = false;
        _metroResult = res;
      });
    } else {
      setState(() {
        _metroLoading = false;
        _metroError = 'No metro timetable found for station "$s".';
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
        // Mode Selector Buttons (BMTC Bus vs Namma Metro)
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _activeMode == 'bmtc' ? AppTheme.bmtcColor : cardBg,
                  foregroundColor: _activeMode == 'bmtc' ? Colors.white : textColor,
                  elevation: _activeMode == 'bmtc' ? 2 : 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: _activeMode == 'bmtc' ? AppTheme.bmtcColor : AppTheme.getBorder(isDark)),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: () {
                  setState(() {
                    _activeMode = 'bmtc';
                  });
                  if (_bmtcResult == null) _searchBmtc();
                },
                icon: const Icon(Icons.directions_bus_rounded, size: 18),
                label: const Text('BMTC Bus Timetable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _activeMode == 'metro' ? AppTheme.metroColor : cardBg,
                  foregroundColor: _activeMode == 'metro' ? Colors.white : textColor,
                  elevation: _activeMode == 'metro' ? 2 : 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: _activeMode == 'metro' ? AppTheme.metroColor : AppTheme.getBorder(isDark)),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: () {
                  setState(() {
                    _activeMode = 'metro';
                  });
                  if (_metroResult == null) _searchMetro();
                },
                icon: const Icon(Icons.subway_rounded, size: 18),
                label: const Text('Namma Metro Timetable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        if (_activeMode == 'bmtc') ...[
          // BMTC Input Form (Route Number + Bus Stop)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _bmtcRouteCtrl,
                decoration: InputDecoration(
                  labelText: 'BUS / ROUTE NUMBER',
                  hintText: 'e.g. 500D, 335E, KIA-8, 360-K',
                  prefixIcon: const Icon(Icons.alt_route_rounded),
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onSubmitted: (_) => _searchBmtc(),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _bmtcStopCtrl,
                decoration: InputDecoration(
                  labelText: 'BUS STOP NAME',
                  hintText: 'e.g. Hebbal, Silk Board, Majestic, Whitefield',
                  prefixIcon: const Icon(Icons.pin_drop_rounded),
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onSubmitted: (_) => _searchBmtc(),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.bmtcColor,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: _searchBmtc,
                  icon: const Icon(Icons.schedule_rounded, size: 18),
                  label: const Text('Get Bus Timetable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (_bmtcLoading)
            const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
          else if (_bmtcError != null)
            Center(child: Text(_bmtcError!, style: TextStyle(color: mutedColor)))
          else if (_bmtcResult != null) ...[
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
                        'Route: ${_bmtcResult!['route'] ?? _bmtcRouteCtrl.text}',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                      ),
                      if (_bmtcResult!['total_trips'] != null)
                        PillBadge(text: '${_bmtcResult!['total_trips']} TRIPS/DAY', color: AppTheme.bmtcColor),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Boarding Stop: ${_bmtcResult!['board_stop'] ?? _bmtcStopCtrl.text}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.bmtcColor),
                  ),
                  const SizedBox(height: 14),

                  Text('SCHEDULED DEPARTURES FROM STOP:',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                  const SizedBox(height: 10),

                  if (_bmtcResult!['departures'] is List && (_bmtcResult!['departures'] as List).isNotEmpty)
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: (_bmtcResult!['departures'] as List).map((dep) {
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppTheme.bmtcColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.access_time_filled_rounded, size: 12, color: AppTheme.bmtcColor),
                              const SizedBox(width: 4),
                              Text(dep.toString(),
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.bmtcColor)),
                            ],
                          ),
                        );
                      }).toList(),
                    )
                  else
                    Text('No specific departure slots found. Regular bus service operational ~05:30 - 23:00.',
                        style: TextStyle(fontSize: 12, color: mutedColor)),
                ],
              ),
            ),
          ],
        ] else ...[
          // Metro Input Form (Station / Line)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _metroStationCtrl,
                decoration: InputDecoration(
                  labelText: 'METRO STATION NAME',
                  hintText: 'e.g. Indiranagar, MG Road, Whitefield, Majestic, Nagasandra',
                  prefixIcon: const Icon(Icons.subway_rounded),
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onSubmitted: (_) => _searchMetro(),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.metroColor,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: _searchMetro,
                  icon: const Icon(Icons.schedule_rounded, size: 18),
                  label: const Text('Get Metro Timetable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (_metroLoading)
            const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
          else if (_metroError != null)
            Center(child: Text(_metroError!, style: TextStyle(color: mutedColor)))
          else if (_metroResult != null) ...[
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
                        _metroResult!['resolved_station'] ?? _metroStationCtrl.text,
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                      ),
                      if (_metroResult!['line'] != null)
                        PillBadge(text: _metroResult!['line'].toString().toUpperCase(), color: AppTheme.metroColor),
                    ],
                  ),
                  const SizedBox(height: 6),
                  if (_metroResult!['frequency'] != null)
                    Text(
                      'Train Frequency: ${_metroResult!['frequency']} ${_metroResult!['is_peak'] == true ? "(Peak Hours ⚡)" : "(Normal)"}',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.metroColor),
                    ),
                  const SizedBox(height: 14),

                  Text('UPCOMING TRAIN DEPARTURES:',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                  const SizedBox(height: 10),

                  if (_metroResult!['departures'] is List && (_metroResult!['departures'] as List).isNotEmpty)
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: (_metroResult!['departures'] as List).map((dep) {
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppTheme.metroColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.subway_rounded, size: 12, color: AppTheme.metroColor),
                              const SizedBox(width: 4),
                              Text(dep.toString(),
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.metroColor)),
                            ],
                          ),
                        );
                      }).toList(),
                    )
                  else
                    Text('No train departure slots found. Operating window is 05:00 AM – 11:00 PM.',
                        style: TextStyle(fontSize: 12, color: mutedColor)),
                ],
              ),
            ),
          ],
        ],
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
// ─────────────────────────────────────────────────────────────
// TAB 4: STOPS INFO (NEAREST BUS STOP & METRO STATION NEAR ME OR PLACE)
// ─────────────────────────────────────────────────────────────
class StopArrivalsTabView extends StatefulWidget {
  const StopArrivalsTabView({super.key});

  @override
  State<StopArrivalsTabView> createState() => _StopArrivalsTabViewState();
}

class _StopArrivalsTabViewState extends State<StopArrivalsTabView> {
  final _searchCtrl = TextEditingController(text: 'Indiranagar');
  Map<String, dynamic>? _stopsInfo;
  bool _loading = false;
  String? _error;

  // Selected bus stop details
  String? _selectedBusStop;
  List<dynamic> _visitingBuses = [];
  bool _busLoading = false;

  // Selected bus timetable dialog/expansion
  String? _activeBusRoute;
  Map<String, dynamic>? _activeBusSchedule;
  bool _busScheduleLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchInfo(query: 'Indiranagar');
  }

  Future<void> _fetchInfo({String? query, double? lat, double? lng}) async {
    setState(() {
      _loading = true;
      _error = null;
      _selectedBusStop = null;
      _visitingBuses = [];
    });

    final res = await ApiService.fetchStopsInfo(query: query, lat: lat, lng: lng);
    if (!mounted) return;

    if (res != null && (res['nearest_bmtc'] != null || res['nearest_metro'] != null)) {
      setState(() {
        _loading = false;
        _stopsInfo = res;
        if (res['nearest_bmtc'] != null && res['nearest_bmtc']['stop_name'] != null) {
          _selectedBusStop = res['nearest_bmtc']['stop_name'].toString();
          if (res['nearest_bmtc']['visiting_buses'] is List) {
            _visitingBuses = res['nearest_bmtc']['visiting_buses'];
          }
        }
      });
    } else {
      setState(() {
        _loading = false;
        _error = 'Failed to find nearest stops for "${query ?? "location"}".';
      });
    }
  }

  Future<void> _loadBusesForStop(String stopName) async {
    setState(() {
      _selectedBusStop = stopName;
      _busLoading = true;
      _visitingBuses = [];
    });

    final res = await ApiService.fetchBmtcBusesForStop(stopName);
    if (!mounted) return;

    if (res != null && res['buses'] is List) {
      setState(() {
        _busLoading = false;
        _visitingBuses = (res['buses'] as List).map((b) => b['route']?.toString() ?? b.toString()).toList();
      });
    } else {
      setState(() => _busLoading = false);
    }
  }

  Future<void> _showBusSchedule(String routeName, String stopName) async {
    setState(() {
      _activeBusRoute = routeName;
      _busScheduleLoading = true;
      _activeBusSchedule = null;
    });

    final res = await ApiService.fetchRouteTimetable(routeName, stopName);
    if (!mounted) return;

    setState(() {
      _busScheduleLoading = false;
      _activeBusSchedule = res;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final bmtcData = _stopsInfo?['nearest_bmtc'] as Map<String, dynamic>?;
    final metroData = _stopsInfo?['nearest_metro'] as Map<String, dynamic>?;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Top row: Near Me button + Google Place search field
        Row(
          children: [
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.bmtcColor,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
              ),
              onPressed: () {
                _searchCtrl.text = 'My Location';
                _fetchInfo(lat: 12.93496, lng: 77.53488);
              },
              icon: const Icon(Icons.my_location_rounded, size: 18),
              label: const Text('Near Me', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: PlacesAutocompleteField(
                controller: _searchCtrl,
                label: 'SEARCH PLACE FOR NEAREST STOPS',
                hint: 'e.g. Koramangala, Indiranagar, Majestic',
                icon: Icons.search_rounded,
                iconColor: AppTheme.bmtcColor,
                onPlaceSelected: (name, lat, lng) => _fetchInfo(query: name, lat: lat, lng: lng),
                onSubmitted: () => _fetchInfo(query: _searchCtrl.text.trim()),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
        else if (_error != null)
          Center(child: Text(_error!, style: TextStyle(color: mutedColor)))
        else ...[

          // 🚇 NEAREST METRO STATION CARD WITH LINE & DEPARTURES
          if (metroData != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.metroColor.withValues(alpha: isDark ? 0.15 : 0.08),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.subway_rounded, color: AppTheme.metroColor, size: 22),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          metroData['station_name']?.toString() ?? 'Nearest Metro Station',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                        ),
                      ),
                      PillBadge(
                        text: metroData['line']?.toString() ?? 'PURPLE LINE',
                        color: AppTheme.metroColor,
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Icon(Icons.near_me_rounded, size: 13, color: mutedColor),
                      const SizedBox(width: 4),
                      Text('${metroData['distance_km'] ?? 0.5} km away',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: mutedColor)),
                      const SizedBox(width: 12),
                      Text('• Frequency: ${metroData['frequency'] ?? "8 min"}',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.metroColor)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('UPCOMING TRAIN TIMINGS:',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                  const SizedBox(height: 8),
                  if (metroData['departures'] is List && (metroData['departures'] as List).isNotEmpty)
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: (metroData['departures'] as List).map((dep) {
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.metroColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.3)),
                          ),
                          child: Text(dep.toString(),
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.metroColor)),
                        );
                      }).toList(),
                    )
                  else
                    Text('Regular train services running 05:00 AM – 11:00 PM.',
                        style: TextStyle(fontSize: 11, color: mutedColor)),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // 🚌 NEAREST BMTC BUS STOP CARD WITH VISITING BUSES
          if (bmtcData != null) ...[
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
                    children: [
                      const Icon(Icons.directions_bus_rounded, color: AppTheme.bmtcColor, size: 22),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          bmtcData['stop_name']?.toString() ?? 'Nearest Bus Stop',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                        ),
                      ),
                      PillBadge(text: '${bmtcData['distance_km'] ?? 0.2} KM AWAY', color: AppTheme.bmtcColor),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Nearby Stop selector chips
                  if (bmtcData['nearby_stops'] is List && (bmtcData['nearby_stops'] as List).isNotEmpty) ...[
                    Text('NEARBY ALTERNATIVE STOPS:',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                    const SizedBox(height: 6),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: (bmtcData['nearby_stops'] as List).map((ns) {
                          final name = ns['stop_name']?.toString() ?? '';
                          final isSelected = _selectedBusStop == name;
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: FilterChip(
                              label: Text(name, style: const TextStyle(fontSize: 11)),
                              selected: isSelected,
                              selectedColor: AppTheme.bmtcColor.withValues(alpha: 0.2),
                              onSelected: (_) => _loadBusesForStop(name),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  Text('ALL BUSES VISITING THIS STOP:',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                  const SizedBox(height: 8),

                  if (_busLoading)
                    const Center(child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator()))
                  else if (_visitingBuses.isNotEmpty)
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _visitingBuses.map((busNo) {
                        final busStr = busNo.toString();
                        final isActive = _activeBusRoute == busStr;
                        return InkWell(
                          onTap: () => _showBusSchedule(busStr, _selectedBusStop ?? bmtcData['stop_name']),
                          borderRadius: BorderRadius.circular(8),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: isActive ? AppTheme.bmtcColor : AppTheme.bmtcColor.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.4)),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.directions_bus_rounded, size: 12, color: isActive ? Colors.white : AppTheme.bmtcColor),
                                const SizedBox(width: 4),
                                Text(busStr,
                                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: isActive ? Colors.white : AppTheme.bmtcColor)),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    )
                  else
                    Text('No specific bus routes recorded for this stop.', style: TextStyle(fontSize: 12, color: mutedColor)),

                  // Selected Bus Schedule Expansion
                  if (_activeBusRoute != null) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.bmtcColor.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.3)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('Bus $_activeBusRoute Schedule from $_selectedBusStop',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: textColor)),
                              IconButton(
                                icon: const Icon(Icons.close, size: 16),
                                onPressed: () => setState(() => _activeBusRoute = null),
                              ),
                            ],
                          ),
                          if (_busScheduleLoading)
                            const Center(child: Padding(padding: EdgeInsets.all(10), child: CircularProgressIndicator()))
                          else if (_activeBusSchedule != null &&
                              _activeBusSchedule!['departures'] is List &&
                              (_activeBusSchedule!['departures'] as List).isNotEmpty)
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: (_activeBusSchedule!['departures'] as List).map((dep) {
                                return Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: cardBg,
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.3)),
                                  ),
                                  child: Text('🕒 $dep',
                                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                                );
                              }).toList(),
                            )
                          else
                            Text('Regular service running ~05:30 AM – 11:00 PM.', style: TextStyle(fontSize: 11, color: mutedColor)),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ],
    );
  }
}
