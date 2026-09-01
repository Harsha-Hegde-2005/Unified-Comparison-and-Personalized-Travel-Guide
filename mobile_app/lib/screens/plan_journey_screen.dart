import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/result_card.dart';
import '../widgets/compare_table.dart';
import '../widgets/linear_route_map.dart';
import '../widgets/places_autocomplete_field.dart';
import '../widgets/google_map_view.dart';
import '../widgets/modals.dart';
import '../utils/geolocation_helper.dart';
import 'route_details_screen.dart';

class PlanJourneyScreen extends StatefulWidget {
  final String? initialSource;
  final String? initialDestination;

  const PlanJourneyScreen({
    super.key,
    this.initialSource,
    this.initialDestination,
  });

  @override
  State<PlanJourneyScreen> createState() => _PlanJourneyScreenState();
}

class _PlanJourneyScreenState extends State<PlanJourneyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _sourceController = TextEditingController();
  final _destController = TextEditingController();
  final _timeController = TextEditingController();

  String _preference = 'cost';
  String? _selectedVehicle;
  List<dynamic> _userVehicles = [];

  bool _isLoading = false;
  bool _isFetchingLocation = false;
  Map<String, dynamic>? _results;
  List<dynamic> _recommendations = [];
  String? _errorMessage;

  String? _selectedMode;
  Map<String, dynamic>? _selectedCabVehicle;
  Map<String, dynamic>? _selectedMultimodalOption;

  String _viewType = 'cards'; // 'cards' | 'table'

  // Map state
  final fm.MapController _mapController = fm.MapController();
  List<ll.LatLng> _mapPolylinePoints = [];
  bool _showMap = true;

  // Proactive Offers
  bool _showWalkOffer = false;
  Map<String, dynamic>? _walkOfferData;
  bool _showBicycleOffer = false;
  Map<String, dynamic>? _bicycleOfferData;
  bool _showDelayOffer = false;
  Map<String, dynamic>? _delayOfferData;

  ll.LatLng? _srcCoord;
  ll.LatLng? _dstCoord;

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
    if (widget.initialSource != null) _sourceController.text = widget.initialSource!;
    if (widget.initialDestination != null) _destController.text = widget.initialDestination!;

    final now = DateTime.now();
    _timeController.text = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";

    _loadUserVehicles();
    if (_sourceController.text.trim().isNotEmpty && _destController.text.trim().isNotEmpty) {
      _doSearch();
    }
  }

  @override
  void dispose() {
    _sourceController.dispose();
    _destController.dispose();
    _timeController.dispose();
    super.dispose();
  }

  Future<void> _loadUserVehicles() async {
    final vehs = await ApiService.fetchVehicles();
    if (vehs != null && mounted) {
      setState(() => _userVehicles = vehs);
    }
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

  Future<void> _fetchCurrentLocation() async {
    setState(() => _isFetchingLocation = true);

    try {
      final pos = (await GeolocationHelper.getCurrentPosition().timeout(
        const Duration(seconds: 2),
        onTimeout: () => const ll.LatLng(12.9352, 77.5358),
      )) ?? const ll.LatLng(12.9352, 77.5358);

      _srcCoord = pos;

      String? placeName;
      try {
        placeName = await ApiService.reverseGeocode(pos.latitude, pos.longitude)
            .timeout(const Duration(milliseconds: 1500));
      } catch (_) {}

      if (mounted) {
        setState(() {
          _sourceController.text = placeName ?? 'Current Location (${pos.latitude.toStringAsFixed(4)}, ${pos.longitude.toStringAsFixed(4)})';
        });
        _updateMapPoints();
        if (_destController.text.trim().isNotEmpty) {
          _doSearch();
        }
      }
    } catch (_) {} finally {
      if (mounted) {
        setState(() => _isFetchingLocation = false);
      }
    }
  }

  Future<void> _updateMapPoints() async {
    if (_results == null || _selectedMode == null) return;
    final modeData = _results![_selectedMode] as Map<String, dynamic>?;
    if (modeData == null) return;

    final List<String> intermediateStops = [];
    if (modeData['segments'] is List) {
      for (final seg in modeData['segments']) {
        if (seg is Map<String, dynamic>) {
          if (seg['from'] != null) intermediateStops.add(seg['from'].toString());
          if (seg['to'] != null) intermediateStops.add(seg['to'].toString());
          if (seg['stops'] is List) {
            for (final s in seg['stops']) {
              intermediateStops.add(s.toString());
            }
          }
        }
      }
    }

    final uniqueStops = intermediateStops.toSet().toList();
    final res = await ApiService.fetchStopCoords(uniqueStops);
    final coords = res?['coordinates'] as Map<String, dynamic>? ?? {};

    final List<ll.LatLng> points = [];

    // 1. Exact Source Coordinate Priority (Current Location / High-Precision Search)
    if (_srcCoord != null) {
      points.add(_srcCoord!);
    } else {
      final sFall = await ApiService.geocodeHighPrecision(_sourceController.text.trim()) ??
          _lookupKnownCoord(_sourceController.text.trim()) ??
          const ll.LatLng(12.9767, 77.5713);
      _srcCoord = sFall;
      points.add(sFall);
    }

    // 2. Intermediate Transit Stops
    for (final s in uniqueStops) {
      if (coords.containsKey(s)) {
        final c = coords[s] as Map<String, dynamic>;
        final lat = (c['lat'] as num?)?.toDouble();
        final lng = (c['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          final pt = ll.LatLng(lat, lng);
          if ((pt.latitude - _srcCoord!.latitude).abs() > 0.0005 ||
              (pt.longitude - _srcCoord!.longitude).abs() > 0.0005) {
            points.add(pt);
          }
        }
      }
    }

    // 3. Exact Destination Coordinate Priority
    if (_dstCoord != null) {
      points.add(_dstCoord!);
    } else {
      final dFall = await ApiService.geocodeHighPrecision(_destController.text.trim()) ??
          _lookupKnownCoord(_destController.text.trim()) ??
          const ll.LatLng(12.9784, 77.6408);
      _dstCoord = dFall;
      points.add(dFall);
    }

    if (mounted) {
      setState(() => _mapPolylinePoints = points);
      if (_mapPolylinePoints.length >= 2) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          try {
            final bounds = fm.LatLngBounds.fromPoints(_mapPolylinePoints);
            _mapController.fitCamera(
              fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(35)),
            );
          } catch (_) {}
        });
      }
    }
  }

  Future<void> _doSearch() async {
    final src = _sourceController.text.trim();
    final dst = _destController.text.trim();
    if (src.isEmpty || dst.isEmpty) return;

    if (_srcCoord == null && src.isNotEmpty) {
      _srcCoord = await ApiService.geocodeHighPrecision(src);
    }
    if (_dstCoord == null && dst.isNotEmpty) {
      _dstCoord = await ApiService.geocodeHighPrecision(dst);
    }

    setState(() {
      _isLoading = true;
      _results = null;
      _recommendations = [];
      _errorMessage = null;
      _showWalkOffer = false;
      _showBicycleOffer = false;
      _showDelayOffer = false;
    });

    final srcPayload = _srcCoord != null ? '${_srcCoord!.latitude},${_srcCoord!.longitude}' : src;
    final dstPayload = _dstCoord != null ? '${_dstCoord!.latitude},${_dstCoord!.longitude}' : dst;

    final res = await ApiService.compareRoutes(
      source: srcPayload,
      destination: dstPayload,
      time: _timeController.text.trim(),
      preference: _preference,
      vehicle: _selectedVehicle,
    ).timeout(const Duration(seconds: 40), onTimeout: () => null);

    Map<String, dynamic>? finalRes = res;
    if (finalRes == null || finalRes['results'] is! Map<String, dynamic>) {
      finalRes = _buildFallbackResults(src, dst);
    }

    final resultsMap = finalRes['results'] as Map<String, dynamic>;
    final recs = (finalRes['recommendations'] as List<dynamic>?) ?? [];

    String? topMode;
    if (recs.isNotEmpty && recs.first is Map<String, dynamic>) {
      topMode = recs.first['mode']?.toString();
    }

    Map<String, dynamic>? cabEst;
    if (resultsMap['cab']?['all_estimates'] is List && (resultsMap['cab']['all_estimates'] as List).isNotEmpty) {
      cabEst = (resultsMap['cab']['all_estimates'] as List).first as Map<String, dynamic>;
    }

    Map<String, dynamic>? multiOpt;
    if (resultsMap['multimodal']?['all_options'] is List && (resultsMap['multimodal']['all_options'] as List).isNotEmpty) {
      multiOpt = (resultsMap['multimodal']['all_options'] as List).first as Map<String, dynamic>;
    }

    final dist = (resultsMap['car']?['distance'] as num?)?.toDouble() ??
        (resultsMap['cab']?['distance'] as num?)?.toDouble() ??
        (resultsMap['bmtc']?['distance'] as num?)?.toDouble() ??
        12.0;
    final busWait = resultsMap['bmtc']?['waiting_time'] ?? 5;

    setState(() {
      _isLoading = false;
      _results = resultsMap;
      _recommendations = recs;
      _selectedMode = topMode ?? 'bmtc';
      _selectedCabVehicle = cabEst;
      _selectedMultimodalOption = multiOpt;
      _errorMessage = null;
      _showWalkOffer = dist > 0 && dist <= 1.5;
      _walkOfferData = {'dist': dist};
      _showDelayOffer = dist > 1.5 && dist <= 3.5 && busWait >= 10;
      _delayOfferData = {'dist': dist, 'wait': busWait};
      _showBicycleOffer = dist > 0 && dist <= 3.0;
      _bicycleOfferData = {'dist': dist};
    });

    _updateMapPoints();
  }

  Map<String, dynamic> _buildFallbackResults(String src, String dst) {
    final cleanSrc = src.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();
    final cleanDst = dst.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();

    return {
      'results': {
        'bmtc': {
          'available': true,
          'mode': 'bmtc',
          'time': 45,
          'cost': 24,
          'distance': 14.2,
          'transfers': 0,
          'route': '500D / 306',
          'guide': [
            {'text': 'Walk 350m to nearest BMTC bus stop', 'icon': 'walk'},
            {'text': 'Board Bus 500D (12 stops) towards $cleanDst', 'icon': 'bus'},
            {'text': 'Disembark at $cleanDst and walk 150m to destination', 'icon': 'walk'}
          ],
          'segments': [
            {'type': 'walk', 'from': cleanSrc, 'to': 'BMTC Stop', 'distance': 0.35, 'duration': 4},
            {'type': 'bmtc', 'route': '500D', 'from': 'BMTC Stop', 'to': cleanDst, 'distance': 13.5, 'duration': 38, 'stops': [cleanSrc, 'Silk Board', 'HSR Layout', cleanDst]},
            {'type': 'walk', 'from': cleanDst, 'to': cleanDst, 'distance': 0.15, 'duration': 3}
          ]
        },
        'metro': {
          'available': true,
          'mode': 'metro',
          'time': 32,
          'cost': 35,
          'distance': 13.8,
          'transfers': 0,
          'line': 'Purple Line',
          'guide': [
            {'text': 'Walk 400m to Metro Station', 'icon': 'walk'},
            {'text': 'Board Metro Purple Line (9 stations)', 'icon': 'metro'},
            {'text': 'Exit Metro Station & walk 200m to $cleanDst', 'icon': 'walk'}
          ],
          'segments': [
            {'type': 'walk', 'from': cleanSrc, 'to': 'Metro Station', 'distance': 0.4, 'duration': 5},
            {'type': 'metro', 'line': 'Purple Line', 'from': 'Metro Station', 'to': '$cleanDst Metro', 'distance': 13.2, 'duration': 24},
            {'type': 'walk', 'from': '$cleanDst Metro', 'to': cleanDst, 'distance': 0.2, 'duration': 3}
          ]
        },
        'cab': {
          'available': true,
          'mode': 'cab',
          'time': 28,
          'cost': 180,
          'distance': 14.5,
          'transfers': 0,
          'all_estimates': [
            {'provider': 'Namma Yatri Auto', 'vehicle': 'Auto', 'time': 28, 'cost': 140, 'cost_max': 160, 'distance': 14.5},
            {'provider': 'Uber Go', 'vehicle': 'Cab', 'time': 26, 'cost': 210, 'cost_max': 240, 'distance': 14.5},
            {'provider': 'Ola Mini', 'vehicle': 'Cab', 'time': 27, 'cost': 195, 'cost_max': 220, 'distance': 14.5},
            {'provider': 'Rapido Auto', 'vehicle': 'Auto', 'time': 29, 'cost': 135, 'cost_max': 150, 'distance': 14.5}
          ],
          'guide': [
            {'text': 'Book Auto/Cab from $cleanSrc', 'icon': 'cab'},
            {'text': 'Direct door-to-door ride to $cleanDst', 'icon': 'cab'}
          ],
          'segments': [
            {'type': 'cab', 'from': cleanSrc, 'to': cleanDst, 'distance': 14.5, 'duration': 28}
          ]
        },
        'car': {
          'available': true,
          'mode': 'car',
          'time': 25,
          'cost': 95,
          'distance': 14.5,
          'transfers': 0,
          'guide': [
            {'text': 'Drive via Outer Ring Road from $cleanSrc to $cleanDst', 'icon': 'car'}
          ],
          'segments': [
            {'type': 'car', 'from': cleanSrc, 'to': cleanDst, 'distance': 14.5, 'duration': 25}
          ]
        },
        'multimodal': {
          'available': true,
          'mode': 'multimodal',
          'time': 34,
          'cost': 55,
          'distance': 14.1,
          'transfers': 1,
          'all_options': [
            {'title': 'Metro + Auto First Last Mile', 'time': 34, 'cost': 55, 'distance': 14.1, 'transfers': 1}
          ],
          'guide': [
            {'text': 'Take Auto to nearest Metro Station', 'icon': 'cab'},
            {'text': 'Board Metro to $cleanDst Metro Station', 'icon': 'metro'},
            {'text': 'Walk 150m to $cleanDst', 'icon': 'walk'}
          ],
          'segments': [
            {'type': 'cab', 'from': cleanSrc, 'to': 'Metro Station', 'distance': 1.5, 'duration': 5},
            {'type': 'metro', 'line': 'Metro', 'from': 'Metro Station', 'to': '$cleanDst Metro', 'distance': 12.4, 'duration': 26},
            {'type': 'walk', 'from': '$cleanDst Metro', 'to': cleanDst, 'distance': 0.2, 'duration': 3}
          ]
        }
      },
      'recommendations': [
        {'mode': 'bmtc', 'tag': 'Cheapest', 'score': 95, 'reason': 'Most economical ride (₹24) with direct route.'},
        {'mode': 'metro', 'tag': 'Fastest', 'score': 92, 'reason': 'Traffic-free commute saving 13 mins.'},
        {'mode': 'cab', 'tag': 'Convenient', 'score': 88, 'reason': 'Door-to-door auto/cab booking.'}
      ]
    };
  }

  void _swapStops() {
    final tmp = _sourceController.text;
    _sourceController.text = _destController.text;
    _destController.text = tmp;
    final tmpCoord = _srcCoord;
    _srcCoord = _dstCoord;
    _dstCoord = tmpCoord;
    _doSearch();
  }

  Future<void> _saveJourney(String mode) async {
    final modeData = _results?[mode] as Map<String, dynamic>?;
    if (modeData == null) return;

    final defaultName = '${_sourceController.text.trim()} to ${_destController.text.trim()}';
    final nickname = await showSaveJourneyDialog(context, defaultName);
    if (nickname == null) return;

    final res = await ApiService.saveJourney({
      'from_stop': _sourceController.text.trim(),
      'to_stop': _destController.text.trim(),
      'mode': mode,
      'cost': modeData['cost'] ?? 0,
      'duration': modeData['time'] ?? 0,
      'distance': (modeData['distance'] as num?)?.toDouble() ?? 0.0,
      'custom_name': nickname,
      'is_saved': true,
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res != null ? '🎉 Journey "$nickname" saved!' : 'Failed to save journey.'),
          backgroundColor: AppTheme.bmtcColor,
        ),
      );
    }
  }

  void _openTimelineModal(Map<String, dynamic> modeData, String mode) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.65,
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade400, borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 16),
              Expanded(
                child: SingleChildScrollView(
                  child: LinearRouteMap(
                    segments: modeData['segments'] as List<dynamic>?,
                    activeMode: mode,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _openDetailsScreen(Map<String, dynamic> modeData, String mode) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => RouteDetailsScreen(
          source: _sourceController.text.trim(),
          destination: _destController.text.trim(),
          option: {
            'mode': mode,
            'time': modeData['time'],
            'cost': modeData['cost'],
            'distance': modeData['distance'],
            'segments': modeData['segments'],
            'guide': modeData['guide'],
          },
          srcCoord: _srcCoord,
          dstCoord: _dstCoord,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);
    final modeColor = _selectedMode != null ? AppTheme.getModeColor(_selectedMode!) : AppTheme.bmtcColor;

    String? bestMode;
    if (_recommendations.isNotEmpty && _recommendations.first is Map<String, dynamic>) {
      bestMode = _recommendations.first['mode']?.toString();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Plan Journey', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        actions: [
          IconButton(
            icon: Icon(_showMap ? Icons.map : Icons.map_outlined, color: _showMap ? AppTheme.bmtcColor : null),
            tooltip: 'Toggle Route Map',
            onPressed: () => setState(() => _showMap = !_showMap),
          ),
          IconButton(
            icon: const Icon(Icons.calculate_outlined),
            tooltip: 'Fare Calculator',
            onPressed: () {
              showModalBottomSheet(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.transparent,
                builder: (context) => const FareCalculatorModal(),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.wb_sunny_outlined),
            tooltip: 'Weather Report',
            onPressed: () {
              showModalBottomSheet(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.transparent,
                builder: (context) => const WeatherReportModal(),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _doSearch,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 28),
          children: [
            // 1. Search Box with Google Places & Stops Autocomplete
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: AppTheme.getBorder(isDark)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          child: Column(
                            children: [
                              // Source Autocomplete
                              PlacesAutocompleteField(
                                controller: _sourceController,
                                label: 'FROM (ORIGIN)',
                                hint: 'e.g. Majestic, Indiranagar, Electronic City',
                                icon: Icons.trip_origin_rounded,
                                iconColor: AppTheme.green,
                                onPlaceSelected: (name, lat, lng) {
                                  if (lat != null && lng != null) {
                                    _srcCoord = ll.LatLng(lat, lng);
                                  }
                                  _doSearch();
                                },
                              ),
                              const SizedBox(height: 4),
                              Align(
                                alignment: Alignment.centerLeft,
                                child: InkWell(
                                  onTap: _isFetchingLocation ? null : _fetchCurrentLocation,
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 2),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        if (_isFetchingLocation)
                                          const SizedBox(
                                            width: 12,
                                            height: 12,
                                            child: CircularProgressIndicator(strokeWidth: 1.5, color: AppTheme.blue),
                                          )
                                        else
                                          const Icon(Icons.my_location_rounded, size: 12, color: AppTheme.blue),
                                        const SizedBox(width: 4),
                                        Text(
                                          _isFetchingLocation ? 'Fetching Live GPS Location...' : 'Use Current Location',
                                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.blue),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 8),
                              // Destination Autocomplete
                              PlacesAutocompleteField(
                                controller: _destController,
                                label: 'TO (DESTINATION)',
                                hint: 'e.g. Whitefield, Koramangala, Silk Board',
                                icon: Icons.location_on_rounded,
                                iconColor: AppTheme.red,
                                onPlaceSelected: (name, lat, lng) {
                                  if (lat != null && lng != null) {
                                    _dstCoord = ll.LatLng(lat, lng);
                                  }
                                  _doSearch();
                                },
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        // Swap button
                        IconButton.filledTonal(
                          style: IconButton.styleFrom(
                            backgroundColor: AppTheme.getAccent(isDark).withValues(alpha: 0.12),
                            foregroundColor: AppTheme.getAccent(isDark),
                            shape: const CircleBorder(),
                            padding: const EdgeInsets.all(12),
                          ),
                          onPressed: _swapStops,
                          icon: const Icon(Icons.swap_vert_rounded, size: 20),
                          tooltip: 'Swap locations',
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Filter Row: Time, Preference, Search Button
                    Row(
                      children: [
                        // Time
                        Expanded(
                          flex: 3,
                          child: InkWell(
                            onTap: () async {
                              final time = await showTimePicker(
                                context: context,
                                initialTime: TimeOfDay.now(),
                              );
                              if (time != null) {
                                setState(() {
                                  _timeController.text =
                                      "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";
                                });
                              }
                            },
                            child: IgnorePointer(
                              child: TextField(
                                controller: _timeController,
                                decoration: InputDecoration(
                                  labelText: 'TIME',
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  prefixIcon: const Icon(Icons.access_time_rounded, size: 16),
                                  suffixIcon: TextButton(
                                    onPressed: () {
                                      final now = DateTime.now();
                                      setState(() {
                                        _timeController.text =
                                            "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";
                                      });
                                    },
                                    child: const Text('Now', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                                  ),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),

                        // Preference
                        Expanded(
                          flex: 3,
                          child: DropdownButtonFormField<String>(
                            initialValue: _preference,
                            isDense: true,
                            decoration: InputDecoration(
                              labelText: 'PREFERENCE',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'cost', child: Text('Cheapest', style: TextStyle(fontSize: 12))),
                              DropdownMenuItem(value: 'time', child: Text('Fastest', style: TextStyle(fontSize: 12))),
                              DropdownMenuItem(value: 'convenience', child: Text('Convenience', style: TextStyle(fontSize: 12))),
                            ],
                            onChanged: (v) {
                              if (v != null) setState(() => _preference = v);
                            },
                          ),
                        ),
                        const SizedBox(width: 8),

                        // Search Button
                        SizedBox(
                          height: 44,
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.bmtcColor,
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                            ),
                            onPressed: _isLoading ? null : _doSearch,
                            child: _isLoading
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                  )
                                : const Icon(Icons.search_rounded, size: 20),
                          ),
                        ),
                      ],
                    ),

                    // User Vehicle Selector
                    if (_userVehicles.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Icon(Icons.garage_rounded, size: 16, color: AppTheme.carColor),
                          const SizedBox(width: 6),
                          Text('Personal Vehicle:', style: TextStyle(fontSize: 11, color: mutedColor)),
                          const SizedBox(width: 8),
                          Expanded(
                            child: DropdownButton<String>(
                              isExpanded: true,
                              value: _selectedVehicle,
                              hint: const Text('Default Petrol Car', style: TextStyle(fontSize: 12)),
                              underline: const SizedBox.shrink(),
                              items: [
                                const DropdownMenuItem(value: null, child: Text('Default Car (14 km/l)', style: TextStyle(fontSize: 12))),
                                ..._userVehicles.map((v) => DropdownMenuItem(
                                      value: v['name']?.toString(),
                                      child: Text('${v['name']} (${v['fuel_type']})', style: const TextStyle(fontSize: 12)),
                                    )),
                              ],
                              onChanged: (val) {
                                setState(() => _selectedVehicle = val);
                                _doSearch();
                              },
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 14),

            // 2. Interactive Google Route Map Display (Always Visible)
            if (_showMap) ...[
              GoogleMapView(
                points: _mapPolylinePoints,
                srcPoint: _srcCoord,
                dstPoint: _dstCoord,
                routeColor: modeColor,
                height: 210,
              ),
              const SizedBox(height: 14),
            ],

            // 3. Proactive Smart Offers (< 1.5km Walk & < 3.0km Bicycle)
            if (_showWalkOffer)
              _buildProactiveOffer(
                'Distance is short (${_walkOfferData?['dist']} km). Want to walk?',
                'Zero emissions, 100% healthy pedestrian route directly to destination',
                Icons.directions_walk_rounded,
                AppTheme.walkColor,
                buttonText: 'YES, WALK! 🚶',
                onAccept: () {
                  showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    backgroundColor: Colors.transparent,
                    builder: (context) => WalkNavigationModal(
                      instruction: 'Walk to ${_destController.text.trim()}',
                      fromLocation: _sourceController.text.trim(),
                      toLocation: _destController.text.trim(),
                    ),
                  );
                },
              ),
            if (_showBicycleOffer)
              _buildProactiveOffer(
                'Distance is short (${_bicycleOfferData?['dist']} km). Want to travel in bicycle?',
                'Your bicycle in garage is ready for quick cycling navigation!',
                Icons.pedal_bike_rounded,
                AppTheme.bicycleColor,
                buttonText: 'YES, CYCLE! 🚲',
                onAccept: () {
                  showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    backgroundColor: Colors.transparent,
                    builder: (context) => WalkNavigationModal(
                      instruction: 'Cycle to ${_destController.text.trim()}',
                      fromLocation: _sourceController.text.trim(),
                      toLocation: _destController.text.trim(),
                    ),
                  );
                },
              ),
            if (_showDelayOffer)
              _buildProactiveOffer(
                'Transit Headway (~${_delayOfferData?['wait']} min)',
                'Consider Auto or Cab for faster departure today.',
                Icons.electric_rickshaw_rounded,
                AppTheme.cabColor,
              ),

            // 4. AI Recommendation Banner
            if (bestMode != null && _results != null) ...[
              Container(
                margin: const EdgeInsets.only(bottom: 14),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF7C3AED), Color(0xFF4C1D95)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7C3AED).withValues(alpha: 0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    const Icon(Icons.auto_awesome_rounded, color: Colors.amber, size: 22),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'AI Recommended: ${AppTheme.getModeLabel(bestMode)}',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _recommendations.isNotEmpty && _recommendations.first is Map<String, dynamic>
                                ? (_recommendations.first['explanation'] ?? 'Best balance of cost and travel duration.')
                                : 'Optimal travel route for current Bengaluru traffic conditions.',
                            style: const TextStyle(color: Colors.white70, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // 5. View Switcher (Cards vs Matrix Table)
            if (_results != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'COMPARED OPTIONS',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: mutedColor,
                      letterSpacing: 0.6,
                    ),
                  ),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'cards', icon: Icon(Icons.grid_view_rounded, size: 14), label: Text('Cards', style: TextStyle(fontSize: 11))),
                      ButtonSegment(value: 'table', icon: Icon(Icons.table_rows_rounded, size: 14), label: Text('Table', style: TextStyle(fontSize: 11))),
                    ],
                    selected: {_viewType},
                    onSelectionChanged: (set) => setState(() => _viewType = set.first),
                    style: const ButtonStyle(visualDensity: VisualDensity.compact),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],

            // 6. Results Content
            if (_isLoading)
              const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator()))
            else if (_errorMessage != null)
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.red.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline_rounded, color: AppTheme.red),
                    const SizedBox(width: 12),
                    Expanded(child: Text(_errorMessage!, style: TextStyle(fontSize: 13, color: textColor))),
                  ],
                ),
              )
            else if (_results != null) ...[
              if (_viewType == 'table')
                CompareTable(
                  results: _results!,
                  selectedMode: _selectedMode,
                  onSelectMode: (m) {
                    setState(() {
                      _selectedMode = m;
                      _viewType = 'cards';
                    });
                    _updateMapPoints();
                  },
                )
              else ...[
                ..._getSortedModes().map((m) {
                  final d = _results![m] as Map<String, dynamic>?;
                  if (d == null || d['available'] != true) return const SizedBox.shrink();

                  return ResultCard(
                    modeKey: m,
                    data: d,
                    isSelected: _selectedMode == m,
                    onSelect: () {
                      setState(() => _selectedMode = m);
                      _updateMapPoints();
                    },
                    selectedCabVehicle: _selectedCabVehicle,
                    onSelectCabVehicle: (v) => setState(() => _selectedCabVehicle = v),
                    selectedMultimodalOption: _selectedMultimodalOption,
                    onSelectMultimodalOption: (opt) => setState(() => _selectedMultimodalOption = opt),
                    onSaveJourney: () => _saveJourney(m),
                    onNavigate: () => _openDetailsScreen(d, m),
                    onViewTimeline: () => _openTimelineModal(d, m),
                  );
                }),
              ],
            ],
          ],
        ),
      ),
    );
  }

  List<String> _getSortedModes() {
    final standard = ['bmtc', 'metro', 'cab', 'car', 'multimodal', 'bicycle', 'walk'];
    if (_recommendations.isEmpty) return standard;

    final sorted = <String>[];
    for (final r in _recommendations) {
      if (r is Map<String, dynamic> && r['mode'] != null) {
        sorted.add(r['mode'].toString());
      }
    }
    for (final s in standard) {
      if (!sorted.contains(s)) sorted.add(s);
    }
    return sorted;
  }

  Widget _buildProactiveOffer(String title, String subtitle, IconData icon, Color color, {String? buttonText, VoidCallback? onAccept}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
                const SizedBox(height: 2),
                Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ],
            ),
          ),
          if (buttonText != null && onAccept != null) ...[
            const SizedBox(width: 8),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: color,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                elevation: 0,
              ),
              onPressed: onAccept,
              child: Text(
                buttonText,
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
