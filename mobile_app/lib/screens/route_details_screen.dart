import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import '../theme.dart';
import '../utils/geolocation_helper.dart';
import '../widgets/linear_route_map.dart';
import '../widgets/travel_guide.dart';
import '../widgets/google_map_view.dart';
import '../widgets/app_settings_modal.dart';

class RouteDetailsScreen extends StatefulWidget {
  final String source;
  final String destination;
  final Map<String, dynamic> option;
  final ll.LatLng? srcCoord;
  final ll.LatLng? dstCoord;

  const RouteDetailsScreen({
    super.key,
    required this.source,
    required this.destination,
    required this.option,
    this.srcCoord,
    this.dstCoord,
  });

  @override
  State<RouteDetailsScreen> createState() => _RouteDetailsScreenState();
}

class _RouteDetailsScreenState extends State<RouteDetailsScreen> {
  final fm.MapController _mapController = fm.MapController();
  List<ll.LatLng> _routePoints = [];
  List<Map<String, dynamic>> _segmentPolylines = [];

  int _activeSegmentIndex = 0;
  bool _isLiveNavigating = false;
  bool _useRealGps = true;
  Timer? _navTimer;
  StreamSubscription<ll.LatLng>? _gpsSubscription;
  double _liveProgress = 0.0;
  ll.LatLng? _liveGpsPoint;

  static const Map<String, ll.LatLng> _knownCoords = {
    'majestic': ll.LatLng(12.9767, 77.5713),
    'indiranagar': ll.LatLng(12.9784, 77.6408),
    'whitefield': ll.LatLng(12.9698, 77.7500),
    'electronic city': ll.LatLng(12.8452, 77.6602),
    'silk board': ll.LatLng(12.9174, 77.6238),
    'mg road': ll.LatLng(12.9756, 77.6066),
    'hebbal': ll.LatLng(13.0358, 77.5970),
    'banashankari': ll.LatLng(12.9255, 77.5739),
    'yeshwantpur': ll.LatLng(13.0238, 77.5529),
    'koramangala': ll.LatLng(12.9352, 77.6245),
    'marathahalli': ll.LatLng(12.9591, 77.6974),
    'btm layout': ll.LatLng(12.9166, 77.6101),
    'jayanagar': ll.LatLng(12.9308, 77.5838),
    'kempegowda bus station': ll.LatLng(12.9767, 77.5713),
    'airport': ll.LatLng(13.1986, 77.7066),
  };

  @override
  void initState() {
    super.initState();
    _fetchRouteCoords();
  }

  @override
  void dispose() {
    _navTimer?.cancel();
    _gpsSubscription?.cancel();
    super.dispose();
  }

  ll.LatLng? _lookupKnownCoord(String name) {
    final n = name.trim().toLowerCase();
    for (final entry in _knownCoords.entries) {
      if (n.contains(entry.key) || entry.key.contains(n)) {
        return entry.value;
      }
    }
    return null;
  }

  Future<void> _fetchRouteCoords() async {
    final List<String> stops = [];
    final opt = widget.option;
    final optMode = opt['mode']?.toString() ?? 'bmtc';

    if (opt['segments'] is List) {
      for (final seg in opt['segments']) {
        if (seg is Map<String, dynamic>) {
          if (seg['from'] != null) stops.add(seg['from'].toString());
          if (seg['to'] != null) stops.add(seg['to'].toString());
          if (seg['stops'] is List) {
            for (final s in seg['stops']) {
              stops.add(s.toString());
            }
          }
        }
      }
    }

    stops.insert(0, widget.source);
    stops.add(widget.destination);

    final uniqueStops = stops.toSet().toList();
    final res = await ApiService.fetchStopCoords(uniqueStops);
    final coords = res?['coordinates'] as Map<String, dynamic>? ?? {};

    final List<ll.LatLng> points = [];

    for (final s in uniqueStops) {
      if (coords.containsKey(s)) {
        final c = coords[s] as Map<String, dynamic>;
        final lat = (c['lat'] as num?)?.toDouble();
        final lng = (c['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          points.add(ll.LatLng(lat, lng));
        }
      } else {
        final fallback = _lookupKnownCoord(s);
        if (fallback != null) points.add(fallback);
      }
    }

    if (points.isEmpty) {
      final sFall = _lookupKnownCoord(widget.source) ?? const ll.LatLng(12.9767, 77.5713);
      final dFall = _lookupKnownCoord(widget.destination) ?? const ll.LatLng(12.9784, 77.6408);
      points.addAll([sFall, dFall]);
    }

    final List<Map<String, dynamic>> segPolylines = [];
    if (opt['segments'] is List) {
      final segs = opt['segments'] as List<dynamic>;
      for (final seg in segs) {
        if (seg is Map<String, dynamic>) {
          final segType = seg['type']?.toString() ?? '';
          final routeName = seg['route']?.toString() ?? '';
          final isWalk = segType == 'walk' || routeName.toLowerCase().contains('walk');
          final isMetro = segType == 'metro' || routeName.toLowerCase().contains('line');

          Color segColor = AppTheme.getModeColor(optMode);
          if (isMetro) {
            final r = routeName.toLowerCase();
            if (r.contains('green')) {
              segColor = const Color(0xFF22C55E); 
            } else if (r.contains('purple')) {
              segColor = const Color(0xFF8B5CF6); 
            } else if (r.contains('yellow')) {
              segColor = const Color(0xFFEAB308); 
            } else {
              segColor = const Color(0xFF8B5CF6);
            }
          } else if (isWalk) {
            segColor = const Color(0xFF6B7A99);
          }

          final List<ll.LatLng> segPts = [];
          final segStops = (seg['stops'] as List<dynamic>?) ?? [];
          for (final s in segStops) {
            final sStr = s.toString();
            if (coords.containsKey(sStr)) {
              final c = coords[sStr] as Map<String, dynamic>;
              final lat = (c['lat'] as num?)?.toDouble();
              final lng = (c['lng'] as num?)?.toDouble();
              if (lat != null && lng != null) {
                segPts.add(ll.LatLng(lat, lng));
              }
            } else {
              final fallback = _lookupKnownCoord(sStr);
              if (fallback != null) segPts.add(fallback);
            }
          }

          if (segPts.length >= 2) {
            segPolylines.add({
              'points': segPts,
              'color': segColor,
              'isWalk': isWalk,
              'isMetro': isMetro,
              'routeName': routeName,
            });
          }
        }
      }
    }

    if (mounted) {
      setState(() {
        _segmentPolylines = segPolylines;
        _routePoints = points;
      });

      final activePoints = _segmentPolylines.isNotEmpty
          ? _segmentPolylines.expand((s) => (s['points'] as List<ll.LatLng>)).toList()
          : _routePoints;

      if (activePoints.length >= 2) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          try {
            final bounds = fm.LatLngBounds.fromPoints(activePoints);
            _mapController.fitCamera(
              fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(40)),
            );
          } catch (_) {}
        });
      }
    }
  }

  void _toggleLiveNav() {
    if (_isLiveNavigating) {
      _navTimer?.cancel();
      _gpsSubscription?.cancel();
      setState(() {
        _isLiveNavigating = false;
        _liveProgress = 0.0;
        _liveGpsPoint = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⏹ Live GPS Navigation stopped')),
      );
    } else {
      if (_useRealGps) {
        setState(() {
          _isLiveNavigating = true;
          _liveProgress = 0.0;
          _liveGpsPoint = widget.srcCoord ?? (_routePoints.isNotEmpty ? _routePoints.first : null);
        });

        _gpsSubscription = GeolocationHelper.watchPositionStream().listen((pos) {
          if (!mounted) return;
          _updateRealGpsPosition(pos);
        });
      } else {
        setState(() {
          _isLiveNavigating = true;
          _liveProgress = 0.0;
          _liveGpsPoint = widget.srcCoord ?? (_routePoints.isNotEmpty ? _routePoints.first : null);
        });

        _navTimer = Timer.periodic(const Duration(seconds: 1), (t) {
          if (!mounted) return;
          setState(() {
            _liveProgress += 3.0;
            if (_liveProgress >= 100.0) {
              _liveProgress = 100.0;
              t.cancel();
              _isLiveNavigating = false;
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('🎉 Destination Reached! Navigation Complete.'),
                  backgroundColor: AppTheme.green,
                ),
              );
            } else {
              final idx = ((_liveProgress / 100.0) * (_routePoints.length - 1)).floor();
              _liveGpsPoint = _routePoints[idx.clamp(0, _routePoints.length - 1)];
            }
          });
        });
      }
    }
  }

  void _updateRealGpsPosition(ll.LatLng pos) {
    if (_routePoints.isEmpty) return;

    final start = _routePoints.first;
    final end = _routePoints.last;
    final totalDistance = const ll.Distance().as(ll.LengthUnit.Meter, start, end);
    final userDistance = const ll.Distance().as(ll.LengthUnit.Meter, start, pos);

    double prog = 0.0;
    if (totalDistance > 0) {
      prog = ((userDistance / totalDistance) * 100.0).clamp(0.0, 100.0);
    }

    final guide = widget.option['guide'] as List<dynamic>?;
    int stepIdx = _activeSegmentIndex;
    if (guide != null && guide.isNotEmpty) {
      stepIdx = ((prog / 100.0) * guide.length).floor().clamp(0, guide.length - 1);
    }

    setState(() {
      _liveGpsPoint = pos;
      _liveProgress = prog;
      _activeSegmentIndex = stepIdx;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final mode = widget.option['mode']?.toString() ?? 'bmtc';
    final modeColor = AppTheme.getModeColor(mode);
    final time = widget.option['time'] ?? 0;
    final cost = widget.option['cost'] ?? 0;
    final dist = widget.option['distance'] ?? 0.0;
    final guide = widget.option['guide'] as List<dynamic>?;
    final segments = widget.option['segments'] as List<dynamic>?;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          '${AppTheme.getModeLabel(mode)} Route',
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _isLiveNavigating ? Icons.stop_circle_rounded : Icons.navigation_rounded,
              color: _isLiveNavigating ? AppTheme.red : AppTheme.green,
            ),
            tooltip: _isLiveNavigating ? 'Stop Navigation' : 'Start Live Navigation',
            onPressed: _toggleLiveNav,
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'App Settings',
            onPressed: () => showAppSettingsModal(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: SegmentedButton<bool>(
                    segments: const [
                      ButtonSegment<bool>(
                        value: true,
                        label: Text('📡 Real GPS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        icon: Icon(Icons.my_location_rounded, size: 14),
                      ),
                      ButtonSegment<bool>(
                        value: false,
                        label: Text('▶️ Demo Simulator', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        icon: Icon(Icons.play_arrow_rounded, size: 14),
                      ),
                    ],
                    selected: {_useRealGps},
                    onSelectionChanged: (setVal) {
                      if (_isLiveNavigating) _toggleLiveNav();
                      setState(() => _useRealGps = setVal.first);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isLiveNavigating ? AppTheme.red : AppTheme.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  elevation: 4,
                ),
                onPressed: _toggleLiveNav,
                icon: Icon(
                  _isLiveNavigating ? Icons.pause_circle_filled_rounded : Icons.play_circle_fill_rounded,
                  size: 22,
                ),
                label: Text(
                  _isLiveNavigating
                      ? 'STOP LIVE GPS NAVIGATION'
                      : '🚀 START LIVE NAVIGATION (${_liveProgress.toStringAsFixed(0)}%)',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 0.3),
                ),
              ),
            ),
            const SizedBox(height: 14),

            if (_isLiveNavigating)
              Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF10B981), Color(0xFF047857)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.green.withValues(alpha: 0.35),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    )
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.navigation_rounded, color: Colors.white, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              _useRealGps ? 'REAL-TIME GPS TRACKING' : 'DEMO SIMULATION ACTIVE',
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.25),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            '${_liveProgress.toStringAsFixed(0)}% Done',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: (_liveProgress / 100.0).clamp(0.0, 1.0),
                        backgroundColor: Colors.white24,
                        color: Colors.white,
                        minHeight: 6,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Current Step (${_activeSegmentIndex + 1}/${guide?.length ?? 1}): ${guide != null && guide.length > _activeSegmentIndex ? (guide[_activeSegmentIndex]['text'] ?? '') : 'En route'}',
                      style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),

            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${widget.source} → ${widget.destination}',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: textColor),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 1,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '⏱️ $time min  ·  ₹$cost  ·  🚶 ${dist}km',
                          style: TextStyle(fontSize: 12, color: mutedColor, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  PillBadge(
                    text: AppTheme.getModeLabel(mode),
                    color: modeColor,
                    icon: AppTheme.getModeIcon(mode),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            GoogleMapView(
              points: _routePoints,
              segmentPolylines: _segmentPolylines,
              srcPoint: widget.srcCoord,
              dstPoint: widget.dstCoord,
              liveGpsPoint: _liveGpsPoint,
              liveGpsProgress: _isLiveNavigating ? _liveProgress : null,
              routeColor: modeColor,
              height: 240,
            ),
            const SizedBox(height: 16),

            LinearRouteMap(
              segments: segments,
              activeMode: mode,
            ),
            const SizedBox(height: 16),

            // 6. Step-by-Step Travel Guide with NAVIGATE WALK buttons
            TravelGuide(
              guide: guide,
              color: modeColor,
              activeSegmentIndex: _activeSegmentIndex,
              onStepTapped: (idx) {
                setState(() => _activeSegmentIndex = idx);
              },
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
