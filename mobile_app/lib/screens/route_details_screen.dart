import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';

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
  bool _isLoadingCoords = false;

  @override
  void initState() {
    super.initState();
    _fetchRouteCoords();
  }

  Future<void> _fetchRouteCoords() async {
    final List<String> stops = [];
    final opt = widget.option;
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

    if (stops.isEmpty) return;

    setState(() {
      _isLoadingCoords = true;
    });

    final uniqueStops = stops.toSet().toList();
    final res = await ApiService.fetchStopCoords(uniqueStops);
    final coords = res?['coordinates'] as Map<String, dynamic>?;

    if (coords != null && mounted) {
      final List<ll.LatLng> points = [];
      if (opt['segments'] is List) {
        for (final seg in opt['segments']) {
          if (seg is Map<String, dynamic>) {
            final fromText = seg['from']?.toString();
            final toText = seg['to']?.toString();

            if (fromText != null && coords.containsKey(fromText)) {
              final c = coords[fromText] as Map<String, dynamic>;
              points.add(ll.LatLng((c['lat'] as num).toDouble(), (c['lng'] as num).toDouble()));
            }

            if (seg['stops'] is List) {
              for (final s in seg['stops']) {
                final stopName = s.toString();
                if (coords.containsKey(stopName)) {
                  final c = coords[stopName] as Map<String, dynamic>;
                  points.add(ll.LatLng((c['lat'] as num).toDouble(), (c['lng'] as num).toDouble()));
                }
              }
            }

            if (toText != null && coords.containsKey(toText)) {
              final c = coords[toText] as Map<String, dynamic>;
              points.add(ll.LatLng((c['lat'] as num).toDouble(), (c['lng'] as num).toDouble()));
            }
          }
        }
      }

      setState(() {
        _routePoints = points;
        _isLoadingCoords = false;
      });

      if (_routePoints.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            final bounds = fm.LatLngBounds.fromPoints(_routePoints);
            _mapController.fitCamera(
              fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(60)),
            );
          }
        });
      }
    } else {
      setState(() {
        _isLoadingCoords = false;
      });
    }
  }

  IconData _getIconForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return Icons.directions_bus;
      case 'metro':
        return Icons.subway;
      case 'cab':
        return Icons.local_taxi;
      case 'car':
        return Icons.directions_car;
      case 'multimodal':
        return Icons.shuffle;
      default:
        return Icons.directions;
    }
  }

  String _getLabelForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return 'BMTC Bus';
      case 'metro':
        return 'Namma Metro';
      case 'cab':
        return 'Cab / Auto';
      case 'car':
        return 'Personal Vehicle';
      case 'multimodal':
        return 'Multimodal Journey';
      default:
        return mode.toUpperCase();
    }
  }

  Widget _mapBtn(IconData icon, VoidCallback onPressed) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(230),
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(38),
            blurRadius: 6,
            offset: const Offset(0, 3),
          )
        ],
      ),
      child: IconButton(
        icon: Icon(icon, color: const Color(0xFF7C5CFF), size: 20),
        onPressed: onPressed,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accentPurple = const Color(0xFF7C5CFF);
    final cardBgColor = isDark ? const Color(0xFF1E2130) : Colors.white;

    final mode = widget.option['mode']?.toString() ?? '';
    final duration = widget.option['time'] ?? 0;
    final cost = widget.option['cost'] ?? 0;
    final walk = widget.option['distance'] ?? 0.0;
    final explanation = widget.option['explanation']?.toString() ?? '';
    final guideSteps = widget.option['guide'] as List<dynamic>? ?? [];

    final center = widget.srcCoord ?? widget.dstCoord ?? const ll.LatLng(12.9716, 77.5946);

    final markers = <fm.Marker>[
      if (widget.srcCoord != null)
        fm.Marker(
          point: widget.srcCoord!,
          width: 48,
          height: 58,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.green,
                  borderRadius: BorderRadius.circular(6),
                  boxShadow: [BoxShadow(color: Colors.black.withAlpha(76), blurRadius: 4)],
                ),
                child: const Text('FROM', style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
              ),
              const Icon(Icons.location_pin, color: Colors.green, size: 32),
            ],
          ),
        ),
      if (widget.dstCoord != null)
        fm.Marker(
          point: widget.dstCoord!,
          width: 48,
          height: 58,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(6),
                  boxShadow: [BoxShadow(color: Colors.black.withAlpha(76), blurRadius: 4)],
                ),
                child: const Text('TO', style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)),
              ),
              const Icon(Icons.location_pin, color: Colors.red, size: 32),
            ],
          ),
        ),
    ];

    final directLine = <ll.LatLng>[
      if (widget.srcCoord != null) widget.srcCoord!,
      if (widget.dstCoord != null) widget.dstCoord!,
    ];

    Widget mapWidget = fm.FlutterMap(
      mapController: _mapController,
      options: fm.MapOptions(
        initialCenter: center,
        initialZoom: 12.5,
        interactionOptions: const fm.InteractionOptions(
          flags: fm.InteractiveFlag.pinchZoom | fm.InteractiveFlag.drag,
        ),
      ),
      children: [
        fm.TileLayer(
          urlTemplate: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
          userAgentPackageName: 'com.bmtc.app',
          maxZoom: 19,
        ),
        if (_routePoints.isNotEmpty)
          fm.PolylineLayer(
            polylines: [
              fm.Polyline(
                points: _routePoints,
                color: accentPurple,
                strokeWidth: 5,
              ),
            ],
          )
        else if (directLine.length == 2)
          fm.PolylineLayer(
            polylines: [
              fm.Polyline(
                points: directLine,
                color: accentPurple,
                strokeWidth: 4,
                isDotted: true,
              ),
            ],
          ),
        fm.MarkerLayer(markers: markers),
      ],
    );

    if (isDark && !kIsWeb) {
      mapWidget = ColorFiltered(
        colorFilter: const ColorFilter.matrix([
          -1, 0, 0, 0, 255,
           0,-1, 0, 0, 255,
           0, 0,-1, 0, 255,
           0, 0, 0, 1,   0,
        ]),
        child: mapWidget,
      );
    }

    return Scaffold(
      body: Stack(
        children: [
          // Detailed map takes the background
          Positioned.fill(child: mapWidget),

          // Custom back button and header panel
          Positioned(
            top: MediaQuery.of(context).padding.top + 10,
            left: 16,
            right: 16,
            child: Row(
              children: [
                Container(
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.black87),
                    onPressed: () => Navigator.pop(context),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: cardBgColor,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: accentPurple.withAlpha(26),
                          child: Icon(_getIconForMode(mode), color: accentPurple),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _getLabelForMode(mode),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                              Text(
                                '⏱️ $duration min  ·  ₹$cost  ·  🚶 ${walk}km',
                                style: const TextStyle(fontSize: 12, color: Colors.grey),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Zoom control buttons
          Positioned(
            top: MediaQuery.of(context).padding.top + 80,
            right: 16,
            child: Column(
              children: [
                _mapBtn(Icons.add, () => _mapController.move(
                    _mapController.camera.center,
                    (_mapController.camera.zoom + 1).clamp(1, 19))),
                const SizedBox(height: 8),
                _mapBtn(Icons.remove, () => _mapController.move(
                    _mapController.camera.center,
                    (_mapController.camera.zoom - 1).clamp(1, 19))),
              ],
            ),
          ),

          // Guidelines sheet at the bottom
          DraggableScrollableSheet(
            initialChildSize: 0.35,
            minChildSize: 0.20,
            maxChildSize: 0.85,
            builder: (context, scrollController) {
              return Container(
                decoration: BoxDecoration(
                  color: cardBgColor,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withAlpha(38),
                      blurRadius: 10,
                      offset: const Offset(0, -3),
                    )
                  ],
                ),
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  children: [
                    // Handle bar
                    Center(
                      child: Container(
                        width: 40,
                        height: 5,
                        decoration: BoxDecoration(
                          color: isDark ? Colors.white24 : Colors.black12,
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    if (explanation.isNotEmpty) ...[
                      Text(
                        '💡 Smart Insights',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: isDark ? Colors.white : Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: accentPurple.withAlpha(20),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: accentPurple.withAlpha(38)),
                        ),
                        child: Text(
                          explanation,
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark ? Colors.grey[300] : Colors.grey[800],
                            height: 1.4,
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                    ],

                    Text(
                      '🗺️ Step-by-Step Directions',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: isDark ? Colors.white : Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 8),

                    if (_isLoadingCoords)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 20),
                        child: Center(
                          child: CircularProgressIndicator(),
                        ),
                      )
                    else if (guideSteps.isNotEmpty)
                      ...guideSteps.map((step) {
                        if (step is Map<String, dynamic>) {
                          final stepText = step['text']?.toString() ?? '';
                          final stepDur = step['duration']?.toString() ?? '';
                          final stepDetail = step['detail']?.toString() ?? '';
                          final stepIconStr = step['icon']?.toString() ?? 'directions';

                          IconData stepIcon = Icons.directions;
                          if (stepIconStr.contains('walk')) stepIcon = Icons.directions_walk;
                          if (stepIconStr.contains('bus')) stepIcon = Icons.directions_bus;
                          if (stepIconStr.contains('train') || stepIconStr.contains('metro') || stepIconStr.contains('subway')) stepIcon = Icons.subway;
                          if (stepIconStr.contains('cab') || stepIconStr.contains('car') || stepIconStr.contains('taxi')) stepIcon = Icons.local_taxi;

                          return Container(
                            margin: const EdgeInsets.symmetric(vertical: 6),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isDark ? Colors.white.withAlpha(5) : Colors.black.withAlpha(4),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                CircleAvatar(
                                  radius: 16,
                                  backgroundColor: accentPurple.withAlpha(26),
                                  child: Icon(stepIcon, size: 16, color: accentPurple),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        stepText,
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: isDark ? Colors.white : Colors.black87,
                                        ),
                                      ),
                                      if (stepDur.isNotEmpty || stepDetail.isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          [stepDur, stepDetail].where((s) => s.isNotEmpty).join(' · '),
                                          style: const TextStyle(fontSize: 11, color: Colors.grey),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        }
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.arrow_right, size: 16, color: Colors.grey),
                              const SizedBox(width: 4),
                              Expanded(child: Text(step.toString(), style: const TextStyle(fontSize: 12))),
                            ],
                          ),
                        );
                      })
                    else
                      const Text(
                        'No detailed steps available.',
                        style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.grey),
                      ),

                    const SizedBox(height: 24),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
