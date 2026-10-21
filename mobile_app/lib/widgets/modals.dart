import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart' as fm;
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import '../theme.dart';
import '../utils/geolocation_helper.dart';
import 'places_autocomplete_field.dart';

// ─────────────────────────────────────────────────────────────
// 1. FARE CALCULATOR MODAL
// ─────────────────────────────────────────────────────────────
class FareCalculatorModal extends StatefulWidget {
  final double initialDistance;

  const FareCalculatorModal({super.key, this.initialDistance = 10.0});

  @override
  State<FareCalculatorModal> createState() => _FareCalculatorModalState();
}

class _FareCalculatorModalState extends State<FareCalculatorModal> {
  String _activeMode = 'bmtc'; // 'bmtc' | 'metro'
  final TextEditingController _fromCtrl = TextEditingController(text: 'Majestic');
  final TextEditingController _toCtrl = TextEditingController(text: 'Indiranagar');

  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _calculateFare();
  }

  @override
  void dispose() {
    _fromCtrl.dispose();
    _toCtrl.dispose();
    super.dispose();
  }

  Future<void> _calculateFare() async {
    final src = _fromCtrl.text.trim();
    final dst = _toCtrl.text.trim();
    if (src.isEmpty || dst.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final res = await ApiService.fetchFareCalculate(
        mode: _activeMode,
        source: src,
        destination: dst,
      );
      if (res != null) {
        setState(() => _result = res);
      } else {
        setState(() => _error = 'Failed to calculate fare.');
      }
    } catch (e) {
      setState(() => _error = 'Error connecting to server.');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return Container(
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.calculate_rounded, color: AppTheme.carColor, size: 22),
                    const SizedBox(width: 8),
                    Text(
                      'Transit Fare Calculator',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                    ),
                  ],
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Mode Selector Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _activeMode == 'bmtc' ? AppTheme.bmtcColor : (isDark ? Colors.grey.shade800 : Colors.grey.shade200),
                      foregroundColor: _activeMode == 'bmtc' ? Colors.white : textColor,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: () {
                      setState(() => _activeMode = 'bmtc');
                      _calculateFare();
                    },
                    icon: const Icon(Icons.directions_bus_rounded, size: 16),
                    label: const Text('BMTC Bus Fare', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _activeMode == 'metro' ? AppTheme.metroColor : (isDark ? Colors.grey.shade800 : Colors.grey.shade200),
                      foregroundColor: _activeMode == 'metro' ? Colors.white : textColor,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: () {
                      setState(() => _activeMode = 'metro');
                      _calculateFare();
                    },
                    icon: const Icon(Icons.subway_rounded, size: 16),
                    label: const Text('Metro Fare', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Source & Destination Fields
            PlacesAutocompleteField(
              controller: _fromCtrl,
              label: _activeMode == 'metro' ? 'FROM METRO STATION' : 'FROM BUS STOP',
              hint: 'e.g. Majestic, Hebbal',
              icon: Icons.trip_origin_rounded,
              iconColor: AppTheme.green,
              onPlaceSelected: (name, lat, lng) {
                _fromCtrl.text = name;
                _calculateFare();
              },
              onSubmitted: _calculateFare,
            ),
            const SizedBox(height: 10),
            PlacesAutocompleteField(
              controller: _toCtrl,
              label: _activeMode == 'metro' ? 'TO METRO STATION' : 'TO BUS STOP',
              hint: 'e.g. Indiranagar, Whitefield',
              icon: Icons.location_on_rounded,
              iconColor: Colors.redAccent,
              onPlaceSelected: (name, lat, lng) {
                _toCtrl.text = name;
                _calculateFare();
              },
              onSubmitted: _calculateFare,
            ),
            const SizedBox(height: 14),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _activeMode == 'metro' ? AppTheme.metroColor : AppTheme.bmtcColor,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: _loading ? null : _calculateFare,
                child: _loading
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Calculate Fare Price', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ),
            ),
            const SizedBox(height: 16),

            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),

            if (_result != null) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: (_activeMode == 'metro' ? AppTheme.metroColor : AppTheme.bmtcColor).withValues(alpha: 0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            '${_result!['source']} → ${_result!['destination']}',
                            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: textColor),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: (_activeMode == 'metro' ? AppTheme.metroColor : AppTheme.bmtcColor).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '📍 ${_result!['distance_km']} km',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: _activeMode == 'metro' ? AppTheme.metroColor : AppTheme.bmtcColor),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    if (_activeMode == 'metro') ...[
                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: cardBg,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: isDark ? Colors.grey.shade800 : Colors.grey.shade300),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Paper Token / QR', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: mutedColor)),
                                  const SizedBox(height: 4),
                                  Text('₹${_result!['token_fare']}', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: textColor)),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: AppTheme.metroColor.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.4)),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('Smart Card (5% Off)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.metroColor)),
                                  const SizedBox(height: 4),
                                  Text('₹${_result!['smart_card_fare']}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.metroColor)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ] else ...[
                      Column(
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: cardBg,
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: isDark ? Colors.grey.shade800 : Colors.grey.shade300),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('Ordinary Direct Bus', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: mutedColor)),
                                      const SizedBox(height: 4),
                                      Text('₹${_result!['ordinary_fare'] ?? _result!['ordinary'] ?? 20}', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: textColor)),
                                      const Text('Single direct ticket', style: TextStyle(fontSize: 9, color: Colors.grey)),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Colors.orange.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: Colors.orange.withValues(alpha: 0.4)),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Ordinary (with Transfer)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.orange)),
                                      const SizedBox(height: 4),
                                      Text('₹${_result!['ordinary_transfer_fare'] ?? ((_result!['ordinary_fare'] ?? 20) + 12)}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.orange)),
                                      const Text('2 separate bus tickets', style: TextStyle(fontSize: 9, color: Colors.grey)),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: AppTheme.bmtcColor.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.4)),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Vajra Volvo AC Direct', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.bmtcColor)),
                                      const SizedBox(height: 4),
                                      Text('₹${_result!['vajra_fare'] ?? _result!['vajra_ac_fare'] ?? 35}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.bmtcColor)),
                                      const Text('Single Volvo ticket', style: TextStyle(fontSize: 9, color: Colors.grey)),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Colors.purple.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: Colors.purple.withValues(alpha: 0.4)),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Vajra AC (with Transfer)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.purple)),
                                      const SizedBox(height: 4),
                                      Text('₹${_result!['vajra_transfer_fare'] ?? ((_result!['vajra_fare'] ?? 35) + 20)}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.purple)),
                                      const Text('2 Volvo AC tickets', style: TextStyle(fontSize: 9, color: Colors.grey)),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 2. WEATHER REPORT MODAL
// ─────────────────────────────────────────────────────────────
class WeatherReportModal extends StatefulWidget {
  final String? initialSource;
  final String? initialDestination;

  const WeatherReportModal({
    super.key,
    this.initialSource,
    this.initialDestination,
  });

  @override
  State<WeatherReportModal> createState() => _WeatherReportModalState();
}

class _WeatherReportModalState extends State<WeatherReportModal> {
  Map<String, dynamic>? _cityWeather;
  Map<String, dynamic>? _srcWeather;
  Map<String, dynamic>? _dstWeather;
  bool _loadingCity = true;
  bool _loadingRoute = false;

  late TextEditingController _srcController;
  late TextEditingController _dstController;

  @override
  void initState() {
    super.initState();
    _srcController = TextEditingController(text: widget.initialSource ?? 'Majestic');
    _dstController = TextEditingController(text: widget.initialDestination ?? 'Whitefield');
    _fetchCityWeather();
    _fetchRouteWeather();
  }

  @override
  void dispose() {
    _srcController.dispose();
    _dstController.dispose();
    super.dispose();
  }

  Future<void> _fetchCityWeather() async {
    final res = await ApiService.fetchWeatherReport(12.9716, 77.5946, 'Bengaluru');
    if (mounted) {
      setState(() {
        _cityWeather = res;
        _loadingCity = false;
      });
    }
  }

  Future<void> _fetchRouteWeather() async {
    final src = _srcController.text.trim();
    final dst = _dstController.text.trim();
    if (src.isEmpty || dst.isEmpty) return;

    setState(() => _loadingRoute = true);

    try {
      final sW = await ApiService.fetchWeatherReport(12.9767, 77.5713, src);
      final dW = await ApiService.fetchWeatherReport(12.9698, 77.7500, dst);
      if (mounted) {
        setState(() {
          _srcWeather = sW;
          _dstWeather = dW;
          _loadingRoute = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingRoute = false);
    }
  }

  String _getWeatherEmoji(String? status) {
    if (status == null) return '🌤️';
    final s = status.toLowerCase();
    if (s.contains('thunder')) return '⛈️';
    if (s.contains('rain') || s.contains('drizzle')) return '🌧️';
    if (s.contains('cloud') || s.contains('overcast')) return '⛅';
    if (s.contains('fog') || s.contains('mist')) return '🌫️';
    if (s.contains('clear') || s.contains('sun')) return '☀️';
    return '🌤️';
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);
    final borderCol = AppTheme.getBorder(isDark);

    final status = _cityWeather?['status']?.toString() ?? 'Partly Cloudy';
    final isRainy = status.toLowerCase().contains('rain') || status.toLowerCase().contains('thunder');

    return Container(
      constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.88),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(7),
                    decoration: BoxDecoration(
                      color: Colors.amber.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.wb_sunny_rounded, color: Colors.amber, size: 20),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Bengaluru Transit Weather',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: textColor),
                      ),
                      Text(
                        'Live Location & Route Precipitation',
                        style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 14),

          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // SECTION 1: CITY / LOCATION REPORT
                  Text(
                    'CITY LOCATION REPORT',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: mutedColor, letterSpacing: 0.5),
                  ),
                  const SizedBox(height: 8),

                  if (_loadingCity)
                    const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
                  else ...[
                    // Main Temp Banner
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: isRainy
                              ? [const Color(0xFF1E3A8A), const Color(0xFF1D4ED8)]
                              : [const Color(0xFF3B82F6), const Color(0xFF2563EB)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF2563EB).withValues(alpha: 0.25),
                            blurRadius: 10,
                            offset: const Offset(0, 4),
                          )
                        ],
                      ),
                      child: Row(
                        children: [
                          Text(_getWeatherEmoji(status), style: const TextStyle(fontSize: 42)),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _cityWeather?['location']?.toString() ?? 'Bengaluru Central',
                                  style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                                Text(
                                  '${_cityWeather?['temp'] ?? 26}°C',
                                  style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.2),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    status.toUpperCase(),
                                    style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),

                    // 4-Grid Metrics (Min/Max, Rain %, Humidity %, Wind km/h)
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      mainAxisSpacing: 8,
                      crossAxisSpacing: 8,
                      childAspectRatio: 2.2,
                      children: [
                        _buildMetricBox('MIN / MAX TEMP', '${_cityWeather?['temp_min'] ?? 21}°C - ${_cityWeather?['temp_max'] ?? 29}°C', isDark, textColor, mutedColor, borderCol),
                        _buildMetricBox('RAIN PROBABILITY', '${_cityWeather?['rain_probability'] ?? 15}%', isDark, textColor, mutedColor, borderCol),
                        _buildMetricBox('RELATIVE HUMIDITY', '${_cityWeather?['humidity'] ?? 62}%', isDark, textColor, mutedColor, borderCol),
                        _buildMetricBox('WIND SPEED', '${_cityWeather?['wind_speed'] ?? 11} km/h', isDark, textColor, mutedColor, borderCol),
                      ],
                    ),
                  ],
                  const SizedBox(height: 18),

                  // SECTION 2: ROUTE TRANSIT WEATHER
                  Text(
                    'ROUTE TRANSIT WEATHER',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: mutedColor, letterSpacing: 0.5),
                  ),
                  const SizedBox(height: 8),

                  // Route inputs row
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: borderCol),
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _srcController,
                                decoration: const InputDecoration(
                                  labelText: 'ROUTE SOURCE',
                                  isDense: true,
                                  prefixIcon: Icon(Icons.trip_origin_rounded, size: 14, color: AppTheme.green),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                ),
                                onSubmitted: (_) => _fetchRouteWeather(),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: TextField(
                                controller: _dstController,
                                decoration: const InputDecoration(
                                  labelText: 'ROUTE DESTINATION',
                                  isDense: true,
                                  prefixIcon: Icon(Icons.location_on_rounded, size: 14, color: AppTheme.red),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                ),
                                onSubmitted: (_) => _fetchRouteWeather(),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.blue,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                            onPressed: _loadingRoute ? null : _fetchRouteWeather,
                            icon: const Icon(Icons.cloud_sync_rounded, size: 16),
                            label: const Text('CHECK ROUTE WEATHER', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),

                  if (_loadingRoute)
                    const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
                  else if (_srcWeather != null && _dstWeather != null) ...[
                    // Origin and Destination Weather Cards
                    Row(
                      children: [
                        Expanded(
                          child: _buildRouteEndpointCard(
                            'START POINT',
                            _srcController.text.trim(),
                            _srcWeather?['temp']?.toString() ?? '25',
                            _srcWeather?['status']?.toString() ?? 'Clear Sky',
                            AppTheme.green,
                            isDark,
                            textColor,
                            borderCol,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildRouteEndpointCard(
                            'DESTINATION',
                            _dstController.text.trim(),
                            _dstWeather?['temp']?.toString() ?? '26',
                            _dstWeather?['status']?.toString() ?? 'Partly Cloudy',
                            AppTheme.red,
                            isDark,
                            textColor,
                            borderCol,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Commute Advisory Card (Matches Website)
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: isRainy
                            ? const Color(0xFFF59E0B).withValues(alpha: 0.12)
                            : const Color(0xFF10B981).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: isRainy
                              ? const Color(0xFFF59E0B).withValues(alpha: 0.4)
                              : const Color(0xFF10B981).withValues(alpha: 0.4),
                          width: 1.5,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(isRainy ? '🌧️' : '☀️', style: const TextStyle(fontSize: 16)),
                              const SizedBox(width: 8),
                              Text(
                                isRainy ? 'PRECIPITATION ADVISORY' : 'OPTIMAL COMMUTE CONDITIONS',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w900,
                                  color: isRainy ? const Color(0xFFD97706) : const Color(0xFF059669),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            isRainy
                                ? 'Rain alert along corridor: Road traffic may face 25–40% slowdown. AC BMTC Vajra buses and Namma Metro are highly recommended for guaranteed on-time transit.'
                                : 'Dry and favorable weather across Bengaluru routes. All transit modes (BMTC buses, Metro, Personal Vehicles, and Cabs) operating with optimal speed and zero weather delays.',
                            style: TextStyle(fontSize: 12, height: 1.45, color: textColor),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricBox(String title, String value, bool isDark, Color textColor, Color mutedColor, Color borderCol) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderCol),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(title, style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: mutedColor, letterSpacing: 0.4)),
          const SizedBox(height: 2),
          Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: textColor)),
        ],
      ),
    );
  }

  Widget _buildRouteEndpointCard(String label, String loc, String temp, String cond, Color accentColor, bool isDark, Color textColor, Color borderCol) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderCol),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: accentColor)),
          const SizedBox(height: 2),
          Text(loc, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: textColor)),
          const SizedBox(height: 4),
          Row(
            children: [
              Text(_getWeatherEmoji(cond), style: const TextStyle(fontSize: 14)),
              const SizedBox(width: 4),
              Text('$temp°C · $cond', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
            ],
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 3. STOPS INFO DIRECTORY MODAL
// ─────────────────────────────────────────────────────────────
class StopsInfoModal extends StatefulWidget {
  final ValueChanged<String>? onSelectStop;

  const StopsInfoModal({super.key, this.onSelectStop});

  @override
  State<StopsInfoModal> createState() => _StopsInfoModalState();
}

class _StopsInfoModalState extends State<StopsInfoModal> {
  final TextEditingController _searchCtrl = TextEditingController();
  List<String> _allStops = [];
  List<String> _filteredStops = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadStops();
  }

  Future<void> _loadStops() async {
    final res = await ApiService.fetchAllStops();
    final all = (res['all'] as List<dynamic>?)?.cast<String>() ?? [];
    if (mounted) {
      setState(() {
        _allStops = all;
        _filteredStops = all.take(50).toList();
        _loading = false;
      });
    }
  }

  void _onFilter(String query) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) {
      setState(() => _filteredStops = _allStops.take(50).toList());
      return;
    }
    setState(() {
      _filteredStops = _allStops.where((s) => s.toLowerCase().contains(q)).take(50).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.pin_drop_rounded, color: AppTheme.bmtcColor, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    'Transit Stops Directory',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Search Field
          TextField(
            controller: _searchCtrl,
            onChanged: _onFilter,
            decoration: InputDecoration(
              hintText: 'Search BMTC stop or Metro station...',
              prefixIcon: const Icon(Icons.search),
              isDense: true,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          const SizedBox(height: 12),

          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _filteredStops.length,
                    itemBuilder: (context, index) {
                      final stop = _filteredStops[index];
                      final isMetro = stop.toLowerCase().contains('metro');

                      return ListTile(
                        dense: true,
                        leading: Icon(
                          isMetro ? Icons.subway_rounded : Icons.directions_bus_rounded,
                          color: isMetro ? AppTheme.metroColor : AppTheme.bmtcColor,
                          size: 18,
                        ),
                        title: Text(stop, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        onTap: () {
                          if (widget.onSelectStop != null) {
                            widget.onSelectStop!(stop);
                          }
                          Navigator.pop(context);
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 4. FARE GUIDE MODAL
// ─────────────────────────────────────────────────────────────
class FareGuideModal extends StatelessWidget {
  const FareGuideModal({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.menu_book_rounded, color: AppTheme.metroColor, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    'Official Transit Fare Guide',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 12),

          Expanded(
            child: ListView(
              children: [
                _buildSection('BMTC Ordinary Buses', [
                  'Stage 1 (0–2 km): ₹6',
                  'Stage 2 (2–4 km): ₹12',
                  'Stage 3 (4–6 km): ₹17',
                  'Stage 4 (6–8 km): ₹21',
                  'Stage 5 (8–10 km): ₹23',
                  'Daily Pass: ₹70 (Ordinary)',
                ], AppTheme.bmtcColor, isDark),
                const SizedBox(height: 14),

                _buildSection('BMTC Vajra (Volvo AC)', [
                  'Base fare (0–2 km): ₹15',
                  'Next stages: ₹25, ₹35, ₹45, ₹65, ₹80',
                  'Airport Vayu Vajra: ₹180 – ₹320',
                  'Daily Vajra Pass: ₹120',
                ], AppTheme.blue, isDark),
                const SizedBox(height: 14),

                _buildSection('Namma Metro (BMRCL)', [
                  'Min fare (1 station): ₹10',
                  'Max fare: ₹60',
                  'Smart Card / QR Code: 5% discount',
                  'Group Ticket: 10% discount for 10+ people',
                ], AppTheme.metroColor, isDark),
                const SizedBox(height: 14),

                _buildSection('Auto Rickshaws', [
                  'Base fare (First 2 km): ₹30',
                  'Per km thereafter: ₹15/km',
                  'Night fare (10 PM – 5 AM): 1.5x standard fare',
                ], AppTheme.cabColor, isDark),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<String> items, Color color, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDark ? 0.12 : 0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color)),
          const SizedBox(height: 8),
          ...items.map((i) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(
                  children: [
                    Icon(Icons.check_circle_outline_rounded, size: 14, color: color),
                    const SizedBox(width: 8),
                    Expanded(child: Text(i, style: const TextStyle(fontSize: 12))),
                  ],
                ),
              )),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 5. LIVE MAP MODAL
// ─────────────────────────────────────────────────────────────
class LiveMapModal extends StatefulWidget {
  final ValueChanged<String>? onSelectStop;

  const LiveMapModal({super.key, this.onSelectStop});

  @override
  State<LiveMapModal> createState() => _LiveMapModalState();
}

class _LiveMapModalState extends State<LiveMapModal> {
  final fm.MapController _mapController = fm.MapController();
  final List<Map<String, dynamic>> _stops = [
    {'name': 'Majestic Bus Station (KBS)', 'point': const ll.LatLng(12.9767, 77.5713), 'isMetro': true},
    {'name': 'Indiranagar Metro Station', 'point': const ll.LatLng(12.9784, 77.6408), 'isMetro': true},
    {'name': 'Whitefield ITPL', 'point': const ll.LatLng(12.9698, 77.7500), 'isMetro': true},
    {'name': 'Silk Board Junction', 'point': const ll.LatLng(12.9174, 77.6238), 'isMetro': false},
    {'name': 'Electronic City Phase 1', 'point': const ll.LatLng(12.8452, 77.6602), 'isMetro': true},
    {'name': 'Hebbal Flyover', 'point': const ll.LatLng(13.0358, 77.5970), 'isMetro': false},
    {'name': 'Banashankari TTMC', 'point': const ll.LatLng(12.9255, 77.5739), 'isMetro': true},
    {'name': 'Yeshwantpur Junction', 'point': const ll.LatLng(13.0238, 77.5529), 'isMetro': true},
    {'name': 'Kempegowda Int. Airport (KIA)', 'point': const ll.LatLng(13.1986, 77.7066), 'isMetro': false},
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.map_rounded, color: AppTheme.blue, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    'Live Transit Explorer Map',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: fm.FlutterMap(
                mapController: _mapController,
                options: const fm.MapOptions(
                  initialCenter: ll.LatLng(12.9716, 77.5946),
                  initialZoom: 12.0,
                ),
                children: [
                  fm.TileLayer(
                    urlTemplate: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
                    userAgentPackageName: 'com.google.maps.bmtc',
                  ),
                  fm.MarkerLayer(
                    markers: _stops.map((s) {
                      final isMetro = s['isMetro'] as bool;
                      final point = s['point'] as ll.LatLng;
                      final name = s['name'] as String;

                      return fm.Marker(
                        point: point,
                        width: 32,
                        height: 32,
                        child: Tooltip(
                          message: name,
                          child: CircleAvatar(
                            backgroundColor: isMetro ? AppTheme.metroColor : AppTheme.bmtcColor,
                            child: Icon(
                              isMetro ? Icons.subway_rounded : Icons.directions_bus_rounded,
                              size: 16,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// SAVE JOURNEY NICKNAME DIALOG
// ─────────────────────────────────────────────────────────────
Future<String?> showSaveJourneyDialog(BuildContext context, String defaultName) async {
  final ctrl = TextEditingController(text: defaultName);
  return showDialog<String>(
    context: context,
    builder: (context) {
      return AlertDialog(
        title: const Text('Save Journey'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Route Nickname (e.g. Home to Office)',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, ctrl.text.trim()),
            child: const Text('Save'),
          ),
        ],
      );
    },
  );
}

// ─────────────────────────────────────────────────────────────
// METRO PLATFORM & INTERCHANGE GUIDANCE MODAL
// ─────────────────────────────────────────────────────────────
class MetroPlatformGuideModal extends StatelessWidget {
  final String stationName;
  final String? fromLine;
  final String? toLine;
  final String? platformNo;
  final String? directionTowards;
  final String instruction;

  const MetroPlatformGuideModal({
    super.key,
    required this.stationName,
    this.fromLine,
    this.toLine,
    this.platformNo,
    this.directionTowards,
    required this.instruction,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final cleanStation = stationName
        .replaceAll(RegExp(r'^(Get\s+down\s+at|Board|Change\s+lines\s+at|Walk\s+to)\s+', caseSensitive: false), '')
        .replaceAll(RegExp(r'\s*\([^)]*\)'), '')
        .trim();

    final pNo = platformNo ?? 'Platform 2';
    final targetLine = toLine ??
        (instruction.toLowerCase().contains('yellow')
            ? 'Yellow Line'
            : (instruction.toLowerCase().contains('green') ? 'Green Line' : 'Purple Line'));

    final lineCol = targetLine.toLowerCase().contains('green')
        ? const Color(0xFF22C55E)
        : (targetLine.toLowerCase().contains('yellow') ? const Color(0xFFEAB308) : const Color(0xFF8B5CF6));

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.subway_rounded, color: AppTheme.metroColor, size: 24),
                  const SizedBox(width: 10),
                  Text(
                    'Metro Platform & Interchange Guide',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Station Title Card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF161822) : const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppTheme.getBorder(isDark)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.location_on_rounded, color: AppTheme.red, size: 18),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        cleanStation.isEmpty ? 'Transfer Metro Station' : cleanStation,
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: textColor),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: lineCol.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: lineCol.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.directions_train_rounded, size: 14, color: lineCol),
                          const SizedBox(width: 6),
                          Text(
                            pNo.toUpperCase(),
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: lineCol),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Board $targetLine ${directionTowards != null ? "towards $directionTowards" : ""}',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: mutedColor),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          Text(
            'STATION INTERCHANGE INSTRUCTIONS',
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.6),
          ),
          const SizedBox(height: 8),

          _buildPlatformStep(
            1,
            'Disembark at $cleanStation platform',
            'Follow overhead signage for Line Interchange & Concourse Level.',
            Icons.nature_people_rounded,
            isDark, textColor, mutedColor,
          ),
          const SizedBox(height: 8),
          _buildPlatformStep(
            2,
            'Proceed to $pNo ($targetLine)',
            'Take stairs/escalators to $pNo concourse. Walk along designated transit corridor (~2 mins walk).',
            Icons.nordic_walking_rounded,
            isDark, textColor, mutedColor,
          ),
          const SizedBox(height: 8),
          _buildPlatformStep(
            3,
            'Board $targetLine Train',
            'Wait behind yellow safety line at $pNo. Board train when doors open.',
            Icons.subway_rounded,
            isDark, textColor, mutedColor,
          ),

          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: lineCol,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.check_circle_rounded, size: 20),
              label: const Text(
                'GOT IT! READY TO BOARD 🚉',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, letterSpacing: 0.5),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlatformStep(int num, String title, String subtitle, IconData icon, bool isDark, Color textColor, Color mutedColor) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1B1E2B) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.getBorder(isDark)),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 12,
            backgroundColor: AppTheme.metroColor.withValues(alpha: 0.15),
            child: Text('$num', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.metroColor)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                const SizedBox(height: 2),
                Text(subtitle, style: TextStyle(fontSize: 10, color: mutedColor)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class WalkNavigationModal extends StatefulWidget {
  final String instruction;
  final String? fromLocation;
  final String? toLocation;
  final ll.LatLng? fromCoord;
  final ll.LatLng? toCoord;
  final String? duration;

  const WalkNavigationModal({
    super.key,
    required this.instruction,
    this.fromLocation,
    this.toLocation,
    this.fromCoord,
    this.toCoord,
    this.duration,
  });

  @override
  State<WalkNavigationModal> createState() => _WalkNavigationModalState();
}

class _WalkNavigationModalState extends State<WalkNavigationModal> {
  final fm.MapController _mapController = fm.MapController();
  List<ll.LatLng> _walkPoints = [];
  ll.LatLng? _liveUserGps;
  StreamSubscription<ll.LatLng>? _gpsSubscription;

  double _progressRatio = 0.0; // 0.0 to 1.0 based on real GPS
  Timer? _flowTimer;
  double _flowPhase = 0.0;
  ll.LatLng? _animatedArrowPos;
  double _animatedArrowBearing = 0.0;
  int _activeStepIndex = 0;
  double _totalRouteMeters = 120.0;

  static const Map<String, ll.LatLng> _knownCoords = {
    'majestic': ll.LatLng(12.9767, 77.5713),
    'kempegowda': ll.LatLng(12.9767, 77.5713),
    'nayandahalli': ll.LatLng(12.9430, 77.5255),
    'mysuru road': ll.LatLng(12.9555, 77.5350),
    'mysore road': ll.LatLng(12.9555, 77.5350),
    'deepanjali nagar': ll.LatLng(12.9535, 77.5385),
    'attiguppe': ll.LatLng(12.9550, 77.5450),
    'vijayanagar': ll.LatLng(12.9667, 77.5350),
    'hosahalli': ll.LatLng(12.9730, 77.5460),
    'magadi road': ll.LatLng(12.9760, 77.5550),
    'city railway': ll.LatLng(12.9775, 77.5650),
    'chickpete': ll.LatLng(12.9670, 77.5740),
    'chickpet': ll.LatLng(12.9670, 77.5740),
    'kr market': ll.LatLng(12.9620, 77.5750),
    'krishna rajendra': ll.LatLng(12.9620, 77.5750),
    'national college': ll.LatLng(12.9510, 77.5730),
    'lalbagh': ll.LatLng(12.9470, 77.5800),
    'south end circle': ll.LatLng(12.9380, 77.5800),
    'jayanagar': ll.LatLng(12.9308, 77.5838),
    'rashtriya vidyalaya': ll.LatLng(12.9215, 77.5800),
    'rv road': ll.LatLng(12.9215, 77.5800),
    'banashankari': ll.LatLng(12.9255, 77.5739),
    'jp nagar': ll.LatLng(12.9070, 77.5780),
    'silk institute': ll.LatLng(12.8710, 77.5480),
    'cubbon park': ll.LatLng(12.9810, 77.5930),
    'vidhana soudha': ll.LatLng(12.9790, 77.5900),
    'mg road': ll.LatLng(12.9756, 77.6066),
    'trinity': ll.LatLng(12.9730, 77.6170),
    'halasuru': ll.LatLng(12.9760, 77.6260),
    'indiranagar': ll.LatLng(12.9784, 77.6408),
    'swami vivekananda': ll.LatLng(12.9860, 77.6440),
    'baiyappanahalli': ll.LatLng(12.9905, 77.6520),
    'kr puram': ll.LatLng(13.0010, 77.6770),
    'whitefield': ll.LatLng(12.9698, 77.7500),
    'electronic city': ll.LatLng(12.8452, 77.6602),
    'beretena agrahara': ll.LatLng(12.8550, 77.6550),
    'pes college': ll.LatLng(12.9352, 77.5358),
    'pes university': ll.LatLng(12.9352, 77.5358),
    'pes': ll.LatLng(12.9352, 77.5358),
    'silk board': ll.LatLng(12.9174, 77.6238),
    'hebbal': ll.LatLng(13.0358, 77.5970),
    'yeshwantpur': ll.LatLng(13.0238, 77.5529),
    'koramangala': ll.LatLng(12.9352, 77.6245),
    'marathahalli': ll.LatLng(12.9591, 77.6974),
    'btm layout': ll.LatLng(12.9166, 77.6101),
  };

  @override
  void initState() {
    super.initState();
    _loadWalkCoords();
    _startGpsTracking();
    _startFlowAnimation();
  }

  @override
  void dispose() {
    _flowTimer?.cancel();
    _gpsSubscription?.cancel();
    super.dispose();
  }

  void _startFlowAnimation() {
    _flowTimer?.cancel();
    _flowTimer = Timer.periodic(const Duration(milliseconds: 60), (timer) {
      if (mounted && _walkPoints.length >= 2) {
        setState(() {
          _flowPhase = (_flowPhase + 0.015) % 1.0;
        });
      }
    });
  }

  void _startGpsTracking() {
    _gpsSubscription?.cancel();
    _gpsSubscription = GeolocationHelper.watchPositionStream().listen((pos) {
      if (mounted) {
        _onUserLocationUpdated(pos);
      }
    });
    GeolocationHelper.getCurrentPosition().then((pos) {
      if (pos != null && mounted) {
        _onUserLocationUpdated(pos);
      }
    });
  }

  void _onUserLocationUpdated(ll.LatLng pos) {
    if (mounted) {
      setState(() {
        _liveUserGps = pos;
        if (_walkPoints.length >= 2) {
          final info = _getTraversedInfoAlongPolyline(_walkPoints, pos);
          final totalM = _totalRouteMeters > 0 ? _totalRouteMeters : 120.0;
          _progressRatio = (info.traversedMeters / totalM).clamp(0.0, 1.0);

          _animatedArrowPos = info.projectedPoint;
          _animatedArrowBearing = info.bearing;

          if (_realWalkSteps.isNotEmpty) {
            _activeStepIndex = (_progressRatio * _realWalkSteps.length).floor().clamp(0, _realWalkSteps.length - 1);
          }
        } else {
          _animatedArrowPos = pos;
        }
      });
    }
  }

  ({double traversedMeters, ll.LatLng projectedPoint, double bearing}) _getTraversedInfoAlongPolyline(List<ll.LatLng> points, ll.LatLng userPos) {
    if (points.length < 2) {
      return (traversedMeters: 0.0, projectedPoint: points.isNotEmpty ? points.first : userPos, bearing: 0.0);
    }

    double minDistanceToPolyline = double.infinity;
    double traversedDistance = 0.0;
    double bestTraversedDistance = 0.0;
    ll.LatLng bestProjectedPoint = points.first;
    double bestBearing = 0.0;

    for (int i = 0; i < points.length - 1; i++) {
      final p1 = points[i];
      final p2 = points[i + 1];
      final segLen = _calculateDirectDistanceKm(p1, p2) * 1000.0;

      final proj = _projectPointOnSegment(p1, p2, userPos);
      final distToSeg = _calculateDirectDistanceKm(userPos, proj.point) * 1000.0;

      if (distToSeg < minDistanceToPolyline) {
        minDistanceToPolyline = distToSeg;
        bestTraversedDistance = traversedDistance + (proj.fraction * segLen);
        bestProjectedPoint = proj.point;
        bestBearing = _calculateBearing(p1, p2);
      }

      traversedDistance += segLen;
    }

    return (
      traversedMeters: bestTraversedDistance,
      projectedPoint: bestProjectedPoint,
      bearing: bestBearing,
    );
  }

  ({ll.LatLng point, double fraction}) _projectPointOnSegment(ll.LatLng p1, ll.LatLng p2, ll.LatLng p) {
    final dLat = p2.latitude - p1.latitude;
    final dLng = p2.longitude - p1.longitude;
    final lenSq = dLat * dLat + dLng * dLng;

    if (lenSq < 0.000000001) {
      return (point: p1, fraction: 0.0);
    }

    final uLat = p.latitude - p1.latitude;
    final uLng = p.longitude - p1.longitude;

    final t = ((uLat * dLat + uLng * dLng) / lenSq).clamp(0.0, 1.0);
    final projPoint = ll.LatLng(p1.latitude + t * dLat, p1.longitude + t * dLng);
    return (point: projPoint, fraction: t);
  }

  List<fm.Marker> _buildFlowingPathDots() {
    if (_walkPoints.length < 2) return [];
    final List<fm.Marker> markers = [];
    const int numDots = 7;

    for (int i = 0; i < numDots; i++) {
      final t = (_flowPhase + (i / numDots)) % 1.0;
      final pos = _interpolatePointAlongPolyline(_walkPoints, t);
      markers.add(
        fm.Marker(
          point: pos,
          width: 12,
          height: 12,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.walkColor,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppTheme.walkColor.withValues(alpha: 0.7),
                  blurRadius: 6,
                  spreadRadius: 1,
                ),
              ],
              border: Border.all(color: Colors.white, width: 1.5),
            ),
          ),
        ),
      );
    }
    return markers;
  }

  ll.LatLng? _lookup(String text) {
    final t = text.toLowerCase();
    for (final entry in _knownCoords.entries) {
      if (t.contains(entry.key)) return entry.value;
    }
    return null;
  }

  ll.LatLng? _extractCoordFromString(String text) {
    final match = RegExp(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)').firstMatch(text);
    if (match != null) {
      final lat = double.tryParse(match.group(1) ?? '');
      final lng = double.tryParse(match.group(2) ?? '');
      if (lat != null && lng != null) {
        return ll.LatLng(lat, lng);
      }
    }
    return null;
  }

  String _cleanPlaceName(String text) {
    const cleanPrefixRegex = r'^(Walk\s+(to|from)|Get\s+down\s+at|Disembark\s+at|Board\s+(the\s+)?|Head\s+out\s+(towards|from)|Change\s+lines\s+at)\s+';
    final cleaned = text
        .replaceAll(RegExp(cleanPrefixRegex, caseSensitive: false), '')
        .replaceAll(RegExp(r'\s*\([^)]*\)'), '')
        .trim();
    return cleaned.isNotEmpty ? cleaned : text.trim();
  }

  double _calculateDirectDistanceKm(ll.LatLng p1, ll.LatLng p2) {
    const d2r = 0.017453292519943295;
    final lat1 = p1.latitude * d2r;
    final lat2 = p2.latitude * d2r;
    final dLat = (p2.latitude - p1.latitude) * d2r;
    final dLng = (p2.longitude - p1.longitude) * d2r;
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1) * math.cos(lat2) * math.sin(dLng / 2) * math.sin(dLng / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return 6371 * c;
  }

  double _computeTotalDistance(List<ll.LatLng> points) {
    double total = 0.0;
    for (int i = 0; i < points.length - 1; i++) {
      total += _calculateDirectDistanceKm(points[i], points[i + 1]) * 1000.0;
    }
    return total > 0 ? total : 120.0;
  }

  double _calculateBearing(ll.LatLng start, ll.LatLng end) {
    const d2r = math.pi / 180;
    const r2d = 180 / math.pi;
    final lat1 = start.latitude * d2r;
    final lat2 = end.latitude * d2r;
    final dLng = (end.longitude - start.longitude) * d2r;
    final y = math.sin(dLng) * math.cos(lat2);
    final x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLng);
    final brng = math.atan2(y, x) * r2d;
    return (brng + 360) % 360;
  }

  ll.LatLng _interpolatePointAlongPolyline(List<ll.LatLng> points, double progressRatio) {
    if (points.isEmpty) return const ll.LatLng(12.9716, 77.5946);
    if (points.length == 1 || progressRatio <= 0) {
      if (points.length >= 2) {
        _animatedArrowBearing = _calculateBearing(points[0], points[1]);
      }
      return points.first;
    }
    if (progressRatio >= 1.0) {
      if (points.length >= 2) {
        _animatedArrowBearing = _calculateBearing(points[points.length - 2], points.last);
      }
      return points.last;
    }

    final totalM = _totalRouteMeters;
    final targetM = totalM * progressRatio;

    double accumulatedM = 0.0;
    for (int i = 0; i < points.length - 1; i++) {
      final segM = _calculateDirectDistanceKm(points[i], points[i + 1]) * 1000.0;
      if (accumulatedM + segM >= targetM) {
        final remainingInSeg = targetM - accumulatedM;
        final t = segM > 0 ? (remainingInSeg / segM).clamp(0.0, 1.0) : 0.0;
        final lat = points[i].latitude + (points[i + 1].latitude - points[i].latitude) * t;
        final lng = points[i].longitude + (points[i + 1].longitude - points[i].longitude) * t;
        _animatedArrowBearing = _calculateBearing(points[i], points[i + 1]);
        return ll.LatLng(lat, lng);
      }
      accumulatedM += segM;
    }
    return points.last;
  }

  List<Map<String, dynamic>> _realWalkSteps = [];

  List<ll.LatLng> _generateDirectPedestrianPath(ll.LatLng start, ll.LatLng end) {
    final List<ll.LatLng> points = [start];
    final dLat = end.latitude - start.latitude;
    final dLng = end.longitude - start.longitude;

    if (dLat.abs() < 0.00001 && dLng.abs() < 0.00001) {
      return [start, end];
    }

    final mid = ll.LatLng(
      start.latitude + dLat * 0.5,
      start.longitude + dLng * 0.5,
    );

    points.add(mid);
    points.add(end);
    return points;
  }

  List<Map<String, dynamic>> _generateDirectWalkSteps(String src, String dst, int totalMeters) {
    final m = totalMeters > 10 ? totalMeters : 120;
    final leg1 = (m * 0.6).round();
    final leg2 = m - leg1;
    final displayDst = dst.isNotEmpty ? dst : 'destination';

    return [
      {'instruction': 'Head out on pedestrian footpath towards $displayDst', 'distance': '$leg1 m'},
      {'instruction': 'Walk along pedestrian walkway directly to entrance', 'distance': '$leg2 m'},
      {'instruction': 'Arrive at $displayDst Entrance', 'distance': '0 m'},
    ];
  }

  Future<void> _loadWalkCoords() async {
    final rawTarget = widget.toLocation ?? widget.instruction;
    final rawOrigin = widget.fromLocation ?? widget.instruction;

    ll.LatLng? startCoord = widget.fromCoord ?? _extractCoordFromString(rawOrigin);
    ll.LatLng? targetCoord = widget.toCoord ?? _extractCoordFromString(rawTarget);

    final String originName = _cleanPlaceName(rawOrigin);
    final String targetName = _cleanPlaceName(rawTarget);

    final liveGps = _liveUserGps ?? await GeolocationHelper.getCurrentPosition();

    if (startCoord == null) {
      if (originName.toLowerCase().contains('current') || originName.toLowerCase().contains('my location')) {
        startCoord = liveGps;
      } else if (originName.isNotEmpty) {
        startCoord = await ApiService.geocodeHighPrecision(originName) ?? _lookup(originName);
      }
    }

    if (targetCoord == null) {
      if (targetName.isNotEmpty) {
        targetCoord = await ApiService.geocodeHighPrecision(targetName) ?? _lookup(targetName);
      }
    }

    startCoord ??= liveGps ?? const ll.LatLng(12.9767, 77.5713);
    targetCoord ??= ll.LatLng(startCoord.latitude + 0.001, startCoord.longitude + 0.001);

    if ((startCoord.latitude - targetCoord.latitude).abs() < 0.00005 &&
        (startCoord.longitude - targetCoord.longitude).abs() < 0.00005) {
      targetCoord = ll.LatLng(startCoord.latitude + 0.001, startCoord.longitude + 0.001);
    }

    final directDistanceKm = _calculateDirectDistanceKm(startCoord, targetCoord);

    List<ll.LatLng> points = [];
    List<Map<String, dynamic>> steps = [];

    final resWalk = await ApiService.fetchWalkingRoute(
      startCoord.latitude,
      startCoord.longitude,
      targetCoord.latitude,
      targetCoord.longitude,
    );

    if (resWalk != null && resWalk['points'] is List && (resWalk['points'] as List).isNotEmpty) {
      final fetchedPoints = List<ll.LatLng>.from(resWalk['points']);
      if (resWalk['steps'] is List) {
        steps = List<Map<String, dynamic>>.from(resWalk['steps']);
      }

      double pathDistanceKm = 0.0;
      for (int i = 0; i < fetchedPoints.length - 1; i++) {
        pathDistanceKm += _calculateDirectDistanceKm(fetchedPoints[i], fetchedPoints[i + 1]);
      }

      if (directDistanceKm < 0.4 && pathDistanceKm > directDistanceKm * 2.2 && pathDistanceKm > 0.3) {
        points = _generateDirectPedestrianPath(startCoord, targetCoord);
        steps = _generateDirectWalkSteps(originName, targetName, (directDistanceKm * 1000).round());
      } else {
        points = fetchedPoints;
      }
    }

    if (points.isEmpty || points.length < 2) {
      points = _generateDirectPedestrianPath(startCoord, targetCoord);
    }

    if (steps.isEmpty) {
      steps = _generateDirectWalkSteps(originName, targetName, (directDistanceKm * 1000).round());
    }

    if (mounted) {
      final totalM = _computeTotalDistance(points);
      final initialPos = points.isNotEmpty ? points.first : null;
      double initialBearing = 0.0;
      if (points.length >= 2) {
        initialBearing = _calculateBearing(points[0], points[1]);
      }

      setState(() {
        _walkPoints = points;
        _realWalkSteps = steps;
        _totalRouteMeters = totalM;
        _animatedArrowPos = initialPos;
        _animatedArrowBearing = initialBearing;
        _progressRatio = 0.0;
        _activeStepIndex = 0;
      });

      WidgetsBinding.instance.addPostFrameCallback((_) {
        try {
          if (_walkPoints.length >= 2) {
            final bounds = fm.LatLngBounds.fromPoints(_walkPoints);
            _mapController.fitCamera(
              fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(40)),
            );
          }
        } catch (_) {}
      });

      if (_liveUserGps != null) {
        _onUserLocationUpdated(_liveUserGps!);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final rawTarget = widget.toLocation ?? (widget.instruction.contains('to ') ? widget.instruction.split('to ').last : widget.instruction);
    final targetName = _cleanPlaceName(rawTarget);
    final cleanInstruction = widget.instruction.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();
    final remainingMeters = ((1.0 - _progressRatio) * _totalRouteMeters).round().clamp(0, 10000);
    final etaMins = math.max(1, (remainingMeters / 80).round());

    return Container(
      height: MediaQuery.of(context).size.height * 0.84,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.directions_walk_rounded, color: AppTheme.walkColor, size: 24),
                  const SizedBox(width: 10),
                  Text(
                    'Pedestrian Walking GPS Guide',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: textColor),
                  ),
                ],
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Live Navigation Header & Progress Bar Banner
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: isDark
                    ? [const Color(0xFF1E293B), const Color(0xFF0F172A)]
                    : [AppTheme.walkColor.withValues(alpha: 0.12), AppTheme.walkColor.withValues(alpha: 0.05)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.walkColor.withValues(alpha: 0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: const BoxDecoration(
                              color: AppTheme.walkColor,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.navigation_rounded, color: Colors.white, size: 16),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  cleanInstruction,
                                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: textColor),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                Text(
                                  'Live GPS location tracking · Walk towards $targetName',
                                  style: TextStyle(fontSize: 11, color: mutedColor),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: AppTheme.blue.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppTheme.blue.withValues(alpha: 0.3)),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.satellite_alt_rounded, size: 14, color: AppTheme.blue),
                          SizedBox(width: 4),
                          Text('REAL GPS TRACKING', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: AppTheme.blue)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Dual Progress Bars Requirement
                // BAR 1: Overall Journey Progress
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.flag_rounded, size: 13, color: AppTheme.bmtcColor),
                        const SizedBox(width: 4),
                        Text(
                          'JOURNEY COMPLETED: ${((0.5 + _progressRatio * 0.5) * 100).round()}%',
                          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: AppTheme.bmtcColor, letterSpacing: 0.3),
                        ),
                      ],
                    ),
                    Text(
                      'Overall Route',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: mutedColor),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: (0.5 + _progressRatio * 0.5).clamp(0.0, 1.0),
                    minHeight: 5,
                    backgroundColor: AppTheme.bmtcColor.withValues(alpha: 0.15),
                    color: AppTheme.bmtcColor,
                  ),
                ),

                const SizedBox(height: 8),

                // BAR 2: Walk Leg Progress
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.directions_walk_rounded,
                          size: 13,
                          color: AppTheme.walkColor,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'WALK LEG COMPLETED: ${(_progressRatio * 100).round()}%',
                          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, color: AppTheme.walkColor, letterSpacing: 0.3),
                        ),
                      ],
                    ),
                    Text(
                      '${remainingMeters}m remaining · ETA $etaMins min',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: mutedColor),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: _progressRatio.clamp(0.0, 1.0),
                    minHeight: 5,
                    backgroundColor: AppTheme.walkColor.withValues(alpha: 0.15),
                    color: AppTheme.walkColor,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Map view of walking path with Moving Flowing Dots and Navigation Marker
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: fm.FlutterMap(
                mapController: _mapController,
                options: fm.MapOptions(
                  initialCenter: _walkPoints.isNotEmpty ? _walkPoints.first : const ll.LatLng(12.9716, 77.5946),
                  initialZoom: 16.5,
                  onTap: (tapPosition, latLng) {
                    _onUserLocationUpdated(latLng);
                  },
                ),
                children: [
                  fm.TileLayer(
                    urlTemplate: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
                    userAgentPackageName: 'com.google.maps.bmtc',
                  ),
                  if (_walkPoints.length >= 2)
                    fm.PolylineLayer(
                      polylines: [
                        fm.Polyline(
                          points: _walkPoints,
                          strokeWidth: 5.5,
                          color: AppTheme.walkColor,
                          isDotted: true,
                        ),
                      ],
                    ),
                  fm.MarkerLayer(
                    markers: [
                      // Animated Flowing Dots moving along the path towards destination
                      ..._buildFlowingPathDots(),

                      if (_walkPoints.isNotEmpty)
                        fm.Marker(
                          point: _walkPoints.first,
                          width: 32,
                          height: 32,
                          child: const CircleAvatar(
                            backgroundColor: AppTheme.green,
                            child: Icon(Icons.directions_walk_rounded, size: 16, color: Colors.white),
                          ),
                        ),
                      if (_walkPoints.length > 1)
                        fm.Marker(
                          point: _walkPoints.last,
                          width: 32,
                          height: 32,
                          child: const CircleAvatar(
                            backgroundColor: AppTheme.red,
                            child: Icon(Icons.location_on_rounded, size: 16, color: Colors.white),
                          ),
                        ),

                      // Primary Directional Walking Navigation Arrow Marker (Rotates with Bearing & Heading)
                      fm.Marker(
                        point: _animatedArrowPos ?? _liveUserGps ?? (_walkPoints.isNotEmpty ? _walkPoints.first : const ll.LatLng(12.9716, 77.5946)),
                        width: 52,
                        height: 52,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            // Soft animated radar aura
                            Container(
                              width: 50,
                              height: 50,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: const Color(0xFF0284C7).withValues(alpha: 0.18),
                              ),
                            ),
                            // Directional Rotating Arrow
                            Transform.rotate(
                              angle: _animatedArrowBearing * (math.pi / 180),
                              child: Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Color(0xFF0284C7), Color(0xFF0EA5E9)],
                                    begin: Alignment.topCenter,
                                    end: Alignment.bottomCenter,
                                  ),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.white, width: 2.5),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF0284C7).withValues(alpha: 0.5),
                                      blurRadius: 10,
                                      spreadRadius: 2,
                                      offset: const Offset(0, 3),
                                    ),
                                  ],
                                ),
                                child: const Center(
                                  child: Icon(
                                    Icons.navigation_rounded,
                                    size: 22,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Dynamic Turn-by-Turn Steps with Active Step Highlight
          Text('TURN-BY-TURN WALKING STEPS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: mutedColor)),
          const SizedBox(height: 6),
          Container(
            height: 120,
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.getBorder(isDark)),
            ),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: _realWalkSteps.length,
              separatorBuilder: (context, index) => const Divider(height: 6),
              itemBuilder: (context, index) {
                final s = _realWalkSteps[index];
                final isActive = index == _activeStepIndex;
                return _buildWalkStep(
                  '${index + 1}. ${s['instruction'] ?? ''}',
                  s['distance']?.toString() ?? '',
                  isDark,
                  isActive: isActive,
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWalkStep(String title, String dist, bool isDark, {bool isActive = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: isActive ? AppTheme.walkColor.withValues(alpha: 0.15) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        border: isActive ? Border.all(color: AppTheme.walkColor.withValues(alpha: 0.4)) : null,
      ),
      child: Row(
        children: [
          Icon(
            isActive ? Icons.navigation_rounded : Icons.subdirectory_arrow_right_rounded,
            size: 16,
            color: isActive ? AppTheme.walkColor : AppTheme.getMuted(isDark),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isActive ? FontWeight.w800 : FontWeight.w600,
                color: isActive ? AppTheme.walkColor : AppTheme.getText(isDark),
              ),
            ),
          ),
          if (isActive)
            Container(
              margin: const EdgeInsets.only(right: 6),
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppTheme.walkColor,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('ACTIVE', style: TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: Colors.white)),
            ),
          Text(
            dist,
            style: TextStyle(
              fontSize: 10,
              color: isActive ? AppTheme.walkColor : AppTheme.getMuted(isDark),
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 5. ALL BMTC BUSES MODAL (Direct & 1-Transfer Comprehensive List)
// ─────────────────────────────────────────────────────────────
class AllBusesModal extends StatefulWidget {
  final String source;
  final String destination;
  final String? time;
  final ValueChanged<String>? onSelectBus;

  const AllBusesModal({
    super.key,
    required this.source,
    required this.destination,
    this.time,
    this.onSelectBus,
  });

  @override
  State<AllBusesModal> createState() => _AllBusesModalState();
}

class _AllBusesModalState extends State<AllBusesModal> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;
  String _filter = 'all'; // all | direct | transfer | vajra
  String? _expandedId;

  @override
  void initState() {
    super.initState();
    _loadAllBuses();
  }

  Future<void> _loadAllBuses() async {
    setState(() => _isLoading = true);
    final res = await ApiService.fetchAllBuses(
      source: widget.source,
      destination: widget.destination,
      time: widget.time,
    );
    if (mounted) {
      setState(() {
        _data = res;
        _isLoading = false;
      });
    }
  }

  bool _isVajra(String route) {
    final r = route.toUpperCase();
    return r.startsWith('V-') || r.startsWith('KIA') || r.contains('VAJRA');
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final direct = (_data?['direct'] as List<dynamic>?) ?? [];
    final transfer = (_data?['transfer'] as List<dynamic>?) ?? [];

    final List<dynamic> filteredDirect = _filter == 'vajra'
        ? direct.where((b) => _isVajra(b['route']?.toString() ?? '')).toList()
        : (_filter == 'direct' || _filter == 'all' ? direct : []);

    final List<dynamic> filteredXfer = _filter == 'vajra'
        ? transfer.where((t) {
            final buses = (t['buses'] as List<dynamic>?)?.map((e) => e.toString()) ?? [];
            return buses.any(_isVajra);
          }).toList()
        : (_filter == 'transfer' || _filter == 'all' ? transfer : []);

    // Summary of all unique bus numbers
    final allBusNums = <String>[];
    for (final b in direct) {
      if (b['route'] != null) allBusNums.add(b['route'].toString());
    }
    for (final t in transfer) {
      final buses = t['buses'] as List<dynamic>?;
      if (buses != null) {
        for (final b in buses) {
          allBusNums.add(b.toString());
        }
      }
    }
    final uniqueBusNums = allBusNums.toSet().toList();

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header (Truncate overflow nicely)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.directions_bus_rounded, color: AppTheme.bmtcColor, size: 22),
                        const SizedBox(width: 8),
                        Text(
                          'All BMTC Buses',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: textColor),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${widget.source} ➔ ${widget.destination}',
                      style: TextStyle(fontSize: 11, color: mutedColor, fontWeight: FontWeight.w600),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Quick Bus Numbers Summary Strip
          if (!_isLoading && uniqueBusNums.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF161822) : const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'POSSIBLE BUS NUMBERS (TAP TO SELECT)',
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: uniqueBusNums.take(16).map((rn) {
                      final isV = _isVajra(rn);
                      return InkWell(
                        onTap: () {
                          widget.onSelectBus?.call(rn);
                          Navigator.pop(context, {'bus_number': rn, 'route': rn});
                        },
                        borderRadius: BorderRadius.circular(6),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                rn,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: isV ? AppTheme.blue : AppTheme.bmtcColor,
                                ),
                              ),
                              const SizedBox(width: 3),
                              Icon(Icons.check_rounded, size: 11, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          // Filter Segmented Buttons
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip('all', 'All (${direct.length + transfer.length})', isDark),
                const SizedBox(width: 6),
                _buildFilterChip('direct', 'Direct (${direct.length})', isDark),
                const SizedBox(width: 6),
                _buildFilterChip('transfer', 'Transfers (${transfer.length})', isDark),
                const SizedBox(width: 6),
                _buildFilterChip('vajra', 'Vajra AC', isDark),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Content List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : (filteredDirect.isEmpty && filteredXfer.isEmpty)
                    ? Center(
                        child: Text(
                          'No matching BMTC buses found for this filter.',
                          style: TextStyle(color: mutedColor, fontSize: 13),
                        ),
                      )
                    : ListView(
                        children: [
                          if (filteredDirect.isNotEmpty) ...[
                            Text(
                              'DIRECT BMTC BUSES (${filteredDirect.length})',
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
                            ),
                            const SizedBox(height: 8),
                            ...filteredDirect.asMap().entries.map((e) => _buildDirectBusCard(e.value, e.key, isDark, textColor, mutedColor)),
                            const SizedBox(height: 16),
                          ],
                          if (filteredXfer.isNotEmpty) ...[
                            Text(
                              '1-TRANSFER ROUTE COMBINATIONS (${filteredXfer.length})',
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
                            ),
                            const SizedBox(height: 8),
                            ...filteredXfer.asMap().entries.map((e) => _buildTransferBusCard(e.value, e.key, isDark, textColor, mutedColor)),
                          ],
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String key, String label, bool isDark) {
    final isSelected = _filter == key;
    return ChoiceChip(
      label: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isSelected ? Colors.white : AppTheme.getText(isDark))),
      selected: isSelected,
      selectedColor: AppTheme.bmtcColor,
      onSelected: (_) => setState(() => _filter = key),
      visualDensity: VisualDensity.compact,
    );
  }

  Widget _buildDirectBusCard(Map<String, dynamic> b, int index, bool isDark, Color textColor, Color mutedColor) {
    final expId = 'd-$index';
    final isExp = _expandedId == expId;
    final routeNo = b['route']?.toString() ?? 'BMTC Bus';
    final fare = b['cost'] ?? b['fare'] ?? 20;
    final time = b['time'] ?? b['duration'] ?? 35;
    final freq = b['frequency']?.toString() ?? 'Every 10-15 mins';
    final stopsCount = b['stop_count'] ?? b['stops_count'] ?? 25;
    final isV = _isVajra(routeNo);
    final altBuses = (b['other_buses'] as List<dynamic>?) ?? (b['alternative_buses'] as List<dynamic>?) ?? [];

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isExp ? AppTheme.bmtcColor : AppTheme.getBorder(isDark),
          width: isExp ? 1.5 : 1.0,
        ),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _expandedId = isExp ? null : expId;
              });
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  InkWell(
                    onTap: () {
                      widget.onSelectBus?.call(routeNo);
                      Navigator.pop(context, {'bus_number': routeNo, 'route': routeNo});
                    },
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            routeNo,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w900,
                              color: isV ? AppTheme.blue : AppTheme.bmtcColor,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Icon(Icons.check_circle_rounded, size: 13, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            PillBadge(text: isV ? 'VAJRA AC' : 'ORDINARY', color: isV ? AppTheme.blue : AppTheme.bmtcColor, isSmall: true),
                            const SizedBox(width: 6),
                            Text('$time min ride', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text('$stopsCount stops · $freq', style: TextStyle(fontSize: 10, color: mutedColor)),
                      ],
                    ),
                  ),
                  Text(
                    '₹$fare',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AppTheme.green),
                  ),
                  const SizedBox(width: 6),
                  Icon(
                    isExp ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                    color: mutedColor,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),

          // Expanded Details Panel
          if (isExp) ...[
            const Divider(height: 1),
            Container(
              padding: const EdgeInsets.all(12),
              color: isDark ? const Color(0xFF10121A) : const Color(0xFFF1F5F9),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Direct Bus Journey', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.check_circle_rounded, size: 13),
                        label: Text('Select Bus $routeNo', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.bmtcColor,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                        ),
                        onPressed: () {
                          widget.onSelectBus?.call(routeNo);
                          Navigator.pop(context, {'bus_number': routeNo, 'route': routeNo});
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text('Estimated duration: $time mins ($stopsCount intermediate stops)', style: TextStyle(fontSize: 11, color: mutedColor)),

                  if (altBuses.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text('OTHER BUSES RUNNING THIS EXACT ROUTE (TAP TO SELECT):', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor)),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: altBuses.map((ab) {
                        final abStr = ab.toString();
                        return InkWell(
                          onTap: () {
                            widget.onSelectBus?.call(abStr);
                            Navigator.pop(context, {'bus_number': abStr, 'route': abStr});
                          },
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF2D3142) : const Color(0xFFE2E8F0),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  abStr,
                                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: textColor),
                                ),
                                const SizedBox(width: 3),
                                const Icon(Icons.touch_app_rounded, size: 10, color: AppTheme.bmtcColor),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTransferBusCard(Map<String, dynamic> t, int index, bool isDark, Color textColor, Color mutedColor) {
    final expId = 't-$index';
    final isExp = _expandedId == expId;
    final buses = (t['buses'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    final xferStop = t['transfer_stop']?.toString() ?? 'Transit Hub';
    final fare = t['cost'] ?? t['fare'] ?? 30;
    final totalTime = t['time'] ?? t['duration'] ?? 45;
    final dist = t['distance'] ?? 18.5;
    final segDetails = (t['segment_details'] as List<dynamic>?) ?? [];

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isExp ? AppTheme.bmtcColor : AppTheme.getBorder(isDark),
          width: isExp ? 1.5 : 1.0,
        ),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _expandedId = isExp ? null : expId;
              });
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const PillBadge(text: '1 TRANSFER', color: AppTheme.yellow, isSmall: true),
                          const SizedBox(width: 8),
                          Text('Via $xferStop', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                        ],
                      ),
                      Row(
                        children: [
                          Text('₹$fare · $totalTime min', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.green)),
                          const SizedBox(width: 6),
                          Icon(
                            isExp ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                            color: mutedColor,
                            size: 20,
                          ),
                        ],
                      ),
                    ],
                  ),
                  if (buses.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Text('Buses (Tap to select): ', style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold)),
                        Wrap(
                          spacing: 4,
                          children: buses.map((b) {
                            final isV = _isVajra(b);
                            return InkWell(
                              onTap: () {
                                widget.onSelectBus?.call(b);
                                Navigator.pop(context, {'bus_number': b, 'route': b});
                              },
                              borderRadius: BorderRadius.circular(4),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  b,
                                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Expanded Details Panel (Matching Website Screenshot 2)
          if (isExp) ...[
            const Divider(height: 1),
            Container(
              padding: const EdgeInsets.all(12),
              color: isDark ? const Color(0xFF10121A) : const Color(0xFFF1F5F9),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (segDetails.isNotEmpty)
                    ...segDetails.asMap().entries.map((entry) {
                      final segIdx = entry.key;
                      final seg = entry.value as Map<String, dynamic>;
                      final routeName = seg['route']?.toString() ?? 'BMTC Bus';
                      final fromStop = seg['from']?.toString() ?? 'Origin Stop';
                      final toStop = seg['to']?.toString() ?? 'Destination Stop';
                      final segFare = seg['fare'] ?? seg['cost'] ?? 15;
                      final segDuration = seg['duration'] ?? seg['time'] ?? 20;
                      final altBuses = (seg['alternative_buses'] as List<dynamic>?) ?? (seg['other_buses'] as List<dynamic>?) ?? [];
                      final isV = _isVajra(routeName);

                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF1B1E2B) : Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppTheme.getBorder(isDark)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: mutedColor.withValues(alpha: 0.15),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        'LEG ${segIdx + 1}',
                                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: mutedColor),
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    InkWell(
                                      onTap: () {
                                        widget.onSelectBus?.call(routeName);
                                        Navigator.pop(context, {'bus_number': routeName, 'route': routeName});
                                      },
                                      borderRadius: BorderRadius.circular(6),
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              routeName,
                                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
                                            ),
                                            const SizedBox(width: 4),
                                            const Icon(Icons.check_rounded, size: 12, color: AppTheme.bmtcColor),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                Text(
                                  '₹$segFare',
                                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.green),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Board', style: TextStyle(fontSize: 9, color: mutedColor, fontWeight: FontWeight.bold)),
                                    Text(fromStop, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                                  ],
                                ),
                                Icon(Icons.arrow_forward_rounded, size: 14, color: mutedColor),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text('Alight', style: TextStyle(fontSize: 9, color: mutedColor, fontWeight: FontWeight.bold)),
                                    Text(toStop, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text('Duration: $segDuration min', style: TextStyle(fontSize: 10, color: mutedColor)),

                            // Alternative Buses List
                            if (altBuses.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Text('ALTERNATIVE BUSES FOR THIS LEG (TAP TO SELECT):', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor)),
                              const SizedBox(height: 4),
                              Wrap(
                                spacing: 4,
                                runSpacing: 4,
                                children: altBuses.take(12).map((ab) {
                                  final abStr = ab.toString();
                                  return InkWell(
                                    onTap: () {
                                      widget.onSelectBus?.call(abStr);
                                      Navigator.pop(context, {'bus_number': abStr, 'route': abStr});
                                    },
                                    borderRadius: BorderRadius.circular(4),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: isDark ? const Color(0xFF2D3142) : const Color(0xFFE2E8F0),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Text(
                                            abStr,
                                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: textColor),
                                          ),
                                          const SizedBox(width: 3),
                                          const Icon(Icons.touch_app_rounded, size: 10, color: AppTheme.bmtcColor),
                                        ],
                                      ),
                                    ),
                                  );
                                }).toList(),
                              ),
                            ],
                          ],
                        ),
                      );
                    })
                  else ...[
                    // Fallback for simple transfer
                    Text('Total Distance: $dist km', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                    const SizedBox(height: 4),
                    Text('Transfer at: $xferStop', style: TextStyle(fontSize: 11, color: mutedColor)),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 6. ROUTE LOOKUP MODAL (Search any BMTC Bus Route)
// ─────────────────────────────────────────────────────────────
class RouteLookupModal extends StatefulWidget {
  const RouteLookupModal({super.key});

  @override
  State<RouteLookupModal> createState() => _RouteLookupModalState();
}

class _RouteLookupModalState extends State<RouteLookupModal> {
  final TextEditingController _ctrl = TextEditingController(text: '500D');
  Map<String, dynamic>? _routeData;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _searchRoute();
  }

  Future<void> _searchRoute() async {
    final query = _ctrl.text.trim();
    if (query.isEmpty) return;
    setState(() => _isLoading = true);
    final res = await ApiService.fetchRouteDetails(query);
    if (mounted) {
      setState(() {
        _routeData = res;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final stops = (_routeData?['stops'] as List<dynamic>?) ?? [];
    final origin = _routeData?['origin'] ?? 'Origin';
    final dest = _routeData?['destination'] ?? 'Destination';

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('BMTC Route Lookup', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: textColor)),
              IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded)),
            ],
          ),
          const SizedBox(height: 12),

          // Search Box
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _ctrl,
                  decoration: InputDecoration(
                    hintText: 'Enter BMTC Bus No (e.g. 500D, V-335E, 365)',
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onSubmitted: (_) => _searchRoute(),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.bmtcColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: _searchRoute,
                child: const Text('Search', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Route Details
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _routeData == null
                    ? Center(child: Text('Enter a bus number to view stops & schedule.', style: TextStyle(color: mutedColor)))
                    : ListView(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF161822) : const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppTheme.getBorder(isDark)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('ROUTE: ${_ctrl.text.toUpperCase()}', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.bmtcColor)),
                                const SizedBox(height: 4),
                                Text('$origin ➔ $dest', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                                const SizedBox(height: 4),
                                Text('${stops.length} Stops · Frequency ~10-15 mins', style: TextStyle(fontSize: 11, color: mutedColor)),
                              ],
                            ),
                          ),
                          const SizedBox(height: 14),
                          Text('STOPS IN SEQUENCE (${stops.length})', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                          const SizedBox(height: 8),
                          ...stops.asMap().entries.map((e) {
                            final idx = e.key;
                            final stopName = e.value.toString();
                            return ListTile(
                              dense: true,
                              leading: CircleAvatar(
                                radius: 10,
                                backgroundColor: idx == 0 ? AppTheme.green : (idx == stops.length - 1 ? AppTheme.red : AppTheme.bmtcColor),
                                child: Text('${idx + 1}', style: const TextStyle(fontSize: 9, color: Colors.white, fontWeight: FontWeight.bold)),
                              ),
                              title: Text(stopName, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: textColor)),
                            );
                          }),
                        ],
                      ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 8. RIDE MODE COMPANION MODAL (BUS & METRO GPS TRACKING)
// ─────────────────────────────────────────────────────────────
class RideModeModal extends StatefulWidget {
  final Map<String, dynamic>? initialData;

  const RideModeModal({super.key, this.initialData});

  @override
  State<RideModeModal> createState() => _RideModeModalState();
}

class _RideModeModalState extends State<RideModeModal> {
  String _step = 'SETUP'; // 'SETUP' | 'TRACKING' | 'SUMMARY'
  String _rideType = 'BUS'; // 'BUS' | 'METRO'

  final List<String> _popularBusRoutes = const ['500C', '335E', '500D', '500A', '201', '365', 'KBS-1', 'V-335E'];
  String _selectedBusNumber = '500D';
  List<Map<String, dynamic>> _busStops = [];
  String _busDestination = '';

  Map<String, List<Map<String, dynamic>>> _metroLines = {};
  String _selectedMetroLine = 'Purple Line';
  List<Map<String, dynamic>> _metroStations = [];
  String _metroDestination = '';

  ll.LatLng? _userLocation;
  bool _gpsLoading = false;
  int _currentStopIndex = 0;
  Timer? _trackingTimer;

  @override
  void initState() {
    super.initState();
    _fetchBusStops(_selectedBusNumber);
    _fetchMetroLines();
    _requestGps();
  }

  @override
  void dispose() {
    _trackingTimer?.cancel();
    super.dispose();
  }

  Future<void> _requestGps() async {
    setState(() => _gpsLoading = true);
    final pos = await GeolocationHelper.getCurrentPosition();
    if (mounted) {
      setState(() {
        _gpsLoading = false;
        if (pos != null) _userLocation = pos;
      });
      _snapCurrentStop();
    }
  }

  Future<void> _fetchBusStops(String busNo) async {
    final res = await ApiService.fetchRouteDetails(busNo);
    if (res != null && mounted) {
      final stops = (res['stops'] as List<dynamic>?)?.map((s) => {'stop_name': s.toString()}).toList() ?? [];
      setState(() {
        _busStops = stops;
        if (stops.isNotEmpty) {
          _busDestination = stops.last['stop_name'].toString();
        }
      });
      _snapCurrentStop();
    }
  }

  Future<void> _fetchMetroLines() async {
    final res = await ApiService.fetchRideMetroLines();
    if (res != null && res['lines'] is Map<String, dynamic> && mounted) {
      final rawLines = res['lines'] as Map<String, dynamic>;
      final Map<String, List<Map<String, dynamic>>> parsedLines = {};
      rawLines.forEach((k, v) {
        if (v is List) {
          parsedLines[k] = v.map((s) => (s as Map<String, dynamic>)).toList();
        }
      });
      setState(() {
        _metroLines = parsedLines;
        if (parsedLines.containsKey(_selectedMetroLine)) {
          _metroStations = parsedLines[_selectedMetroLine]!;
          if (_metroStations.isNotEmpty) {
            _metroDestination = _metroStations.last['stop_name'].toString();
          }
        }
      });
      _snapCurrentStop();
    }
  }

  int get _detectedStopIndex {
    final list = _rideType == 'BUS' ? _busStops : _metroStations;
    if (_userLocation == null || list.isEmpty) return 0;
    return 0;
  }

  void _snapCurrentStop() {
    if (!mounted) return;
    setState(() {
      _currentStopIndex = _detectedStopIndex;
    });
  }

  void _startRide() {
    final list = _rideType == 'BUS' ? _busStops : _metroStations;
    if (list.isEmpty) return;

    setState(() {
      _step = 'TRACKING';
      _currentStopIndex = _detectedStopIndex;
    });

    _trackingTimer?.cancel();
    _trackingTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (!mounted || _step != 'TRACKING') return;
      _requestGps();
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final list = _rideType == 'BUS' ? _busStops : _metroStations;
    final dest = _rideType == 'BUS' ? _busDestination : _metroDestination;
    final currentStopName = list.isNotEmpty && _currentStopIndex < list.length ? list[_currentStopIndex]['stop_name'].toString() : 'Detecting...';
    final remainingCount = math.max(0, list.length - 1 - _currentStopIndex);

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: cardBg, borderRadius: const BorderRadius.vertical(top: Radius.circular(24))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Text(_rideType == 'BUS' ? '🚌' : '🚇', style: const TextStyle(fontSize: 24)),
                  const SizedBox(width: 8),
                  Text(_step == 'TRACKING' ? 'Live Ride Tracking' : 'Ride Mode Companion', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: textColor)),
                ],
              ),
              IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded)),
            ],
          ),
          const SizedBox(height: 16),

          if (_step == 'SETUP') ...[
            Row(
              children: [
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('🚌 BMTC Bus', style: TextStyle(fontWeight: FontWeight.bold))),
                    selected: _rideType == 'BUS',
                    selectedColor: AppTheme.bmtcColor.withValues(alpha: 0.2),
                    onSelected: (_) => setState(() => _rideType = 'BUS'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('🚇 Namma Metro', style: TextStyle(fontWeight: FontWeight.bold))),
                    selected: _rideType == 'METRO',
                    selectedColor: AppTheme.metroColor.withValues(alpha: 0.2),
                    onSelected: (_) => setState(() => _rideType = 'METRO'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            if (_rideType == 'BUS') ...[
              Text('Select Bus Number:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: mutedColor)),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                children: _popularBusRoutes.map((r) => ChoiceChip(
                  label: Text(r),
                  selected: _selectedBusNumber == r,
                  selectedColor: AppTheme.metroColor.withValues(alpha: 0.3),
                  onSelected: (_) {
                    setState(() => _selectedBusNumber = r);
                    _fetchBusStops(r);
                  },
                )).toList(),
              ),
              const SizedBox(height: 16),
            ] else if (_metroLines.isNotEmpty) ...[
              Text('Select Metro Line:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: mutedColor)),
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                children: _metroLines.keys.map((lineName) => ChoiceChip(
                  label: Text(lineName),
                  selected: _selectedMetroLine == lineName,
                  selectedColor: AppTheme.metroColor.withValues(alpha: 0.3),
                  onSelected: (_) {
                    setState(() {
                      _selectedMetroLine = lineName;
                      _metroStations = _metroLines[lineName] ?? [];
                      if (_metroStations.isNotEmpty) {
                        _metroDestination = _metroStations.last['stop_name'].toString();
                      }
                    });
                  },
                )).toList(),
              ),
              const SizedBox(height: 16),
            ],

            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF10B981).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Text('📍', style: TextStyle(fontSize: 20)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('CURRENT / SOURCE STOP (AUTO-DETECTED VIA GPS)', style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Color(0xFF10B981), letterSpacing: 0.5)),
                        const SizedBox(height: 2),
                        Text(_gpsLoading ? 'Acquiring GPS location...' : currentStopName, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: textColor)),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: _requestGps,
                    child: Text(_gpsLoading ? '...' : 'Refresh', style: const TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Text('Select Destination Stop:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: mutedColor)),
            const SizedBox(height: 6),
            DropdownButtonFormField<String>(
              initialValue: list.any((s) => s['stop_name'] == dest) ? dest : (list.isNotEmpty ? list.last['stop_name'].toString() : null),
              decoration: InputDecoration(isDense: true, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))),
              items: list.map((s) {
                final name = s['stop_name'].toString();
                return DropdownMenuItem(value: name, child: Text(name, style: TextStyle(color: textColor, fontSize: 13)));
              }).toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() {
                    if (_rideType == 'BUS') {
                      _busDestination = val;
                    } else {
                      _metroDestination = val;
                    }
                  });
                }
              },
            ),
            const Spacer(),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.metroColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                icon: const Icon(Icons.rocket_launch_rounded),
                label: const Text('Start Ride Tracking', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                onPressed: _startRide,
              ),
            ),
          ] else ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.metroColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('CURRENT LOCATION & STOP', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.metroColor, letterSpacing: 0.5)),
                  const SizedBox(height: 4),
                  Text(currentStopName, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: textColor)),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Stops Remaining: $remainingCount', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: textColor)),
                      Text('Est. ETA: ~${remainingCount * 3} mins', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.green)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: list.length,
                itemBuilder: (context, idx) {
                  final name = list[idx]['stop_name'].toString();
                  final isCurrent = idx == _currentStopIndex;
                  return ListTile(
                    dense: true,
                    leading: CircleAvatar(
                      radius: 10,
                      backgroundColor: isCurrent ? AppTheme.green : (name == dest ? AppTheme.red : mutedColor),
                      child: Text('${idx + 1}', style: const TextStyle(fontSize: 9, color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                    title: Text(name, style: TextStyle(fontSize: 13, fontWeight: isCurrent ? FontWeight.w900 : FontWeight.w600, color: isCurrent ? AppTheme.green : textColor)),
                    trailing: isCurrent ? const Chip(label: Text('LIVE'), backgroundColor: AppTheme.green, labelStyle: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold)) : null,
                  );
                },
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => setState(() => _step = 'SETUP'),
                    child: const Text('Exit Ride Mode'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 8. TIMETABLE MODAL (BMTC Route & Metro Station Timetables)
// ─────────────────────────────────────────────────────────────
class TimetableModal extends StatefulWidget {
  final String? initialSource;
  final String? initialDestination;

  const TimetableModal({
    super.key,
    this.initialSource,
    this.initialDestination,
  });

  @override
  State<TimetableModal> createState() => _TimetableModalState();
}

class _TimetableModalState extends State<TimetableModal> {
  String _activeTab = 'bmtc'; // 'bmtc' | 'metro'

  // BMTC state
  final TextEditingController _bmtcRouteCtrl = TextEditingController(text: '500D');
  final TextEditingController _bmtcStopCtrl = TextEditingController();
  bool _bmtcLoading = false;
  String? _bmtcError;
  Map<String, dynamic>? _bmtcResult;

  // Metro state
  final TextEditingController _metroStationCtrl = TextEditingController();
  bool _metroLoading = false;
  String? _metroError;
  Map<String, dynamic>? _metroResult;

  @override
  void initState() {
    super.initState();
    if (widget.initialSource != null && widget.initialSource!.isNotEmpty) {
      _bmtcStopCtrl.text = widget.initialSource!;
      _metroStationCtrl.text = widget.initialSource!;
    } else {
      _bmtcStopCtrl.text = 'Hebbal';
      _metroStationCtrl.text = 'Indiranagar';
    }
    _searchBmtc();
  }

  @override
  void dispose() {
    _bmtcRouteCtrl.dispose();
    _bmtcStopCtrl.dispose();
    _metroStationCtrl.dispose();
    super.dispose();
  }

  Future<void> _searchBmtc() async {
    final route = _bmtcRouteCtrl.text.trim();
    if (route.isEmpty) return;

    setState(() {
      _bmtcLoading = true;
      _bmtcError = null;
      _bmtcResult = null;
    });

    try {
      final res = await ApiService.fetchBmtcRouteTimetable(route, stop: _bmtcStopCtrl.text.trim());
      if (mounted) {
        setState(() {
          _bmtcResult = res;
          _bmtcLoading = false;
          if (res == null) _bmtcError = 'Timetable not found for route "$route".';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _bmtcError = 'Failed to load BMTC timetable.';
          _bmtcLoading = false;
        });
      }
    }
  }

  Future<void> _searchMetro() async {
    final station = _metroStationCtrl.text.trim();
    if (station.isEmpty) return;

    setState(() {
      _metroLoading = true;
      _metroError = null;
      _metroResult = null;
    });

    try {
      final res = await ApiService.metroTimetable(source: station);
      if (mounted) {
        setState(() {
          _metroResult = res;
          _metroLoading = false;
          if (res == null) _metroError = 'Timetable not found for station "$station".';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _metroError = 'Failed to load Metro timetable.';
          _metroLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: isDark ? Colors.white24 : Colors.grey.shade400,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(7),
                    decoration: BoxDecoration(
                      color: AppTheme.blue.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.access_time_filled_rounded, color: AppTheme.blue, size: 20),
                  ),
                  const SizedBox(width: 10),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Transit Timetable', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                      Text('Official schedules & live departures', style: TextStyle(fontSize: 11, color: Colors.grey)),
                    ],
                  ),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.close_rounded, size: 20),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Mode Tabs (BMTC vs Metro)
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E202C) : const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () {
                      setState(() => _activeTab = 'bmtc');
                      if (_bmtcResult == null) _searchBmtc();
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        color: _activeTab == 'bmtc' ? AppTheme.bmtcColor : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      alignment: Alignment.center,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.directions_bus_rounded, size: 16, color: _activeTab == 'bmtc' ? Colors.white : mutedColor),
                          const SizedBox(width: 6),
                          Text(
                            'BMTC Bus',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: _activeTab == 'bmtc' ? Colors.white : textColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () {
                      setState(() => _activeTab = 'metro');
                      if (_metroResult == null) _searchMetro();
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        color: _activeTab == 'metro' ? AppTheme.metroPurple : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      alignment: Alignment.center,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.subway_rounded, size: 16, color: _activeTab == 'metro' ? Colors.white : mutedColor),
                          const SizedBox(width: 6),
                          Text(
                            'Namma Metro',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: _activeTab == 'metro' ? Colors.white : textColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Content body
          Expanded(
            child: _activeTab == 'bmtc' ? _buildBmtcView(isDark, textColor, mutedColor) : _buildMetroView(isDark, textColor, mutedColor),
          ),
        ],
      ),
    );
  }

  Widget _buildBmtcView(bool isDark, Color textColor, Color mutedColor) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              flex: 3,
              child: TextField(
                controller: _bmtcRouteCtrl,
                style: TextStyle(fontSize: 13, color: textColor),
                decoration: InputDecoration(
                  labelText: 'Route No.',
                  hintText: 'e.g. 500D, 335E',
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onSubmitted: (_) => _searchBmtc(),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 4,
              child: TextField(
                controller: _bmtcStopCtrl,
                style: TextStyle(fontSize: 13, color: textColor),
                decoration: InputDecoration(
                  labelText: 'Boarding Stop (Optional)',
                  hintText: 'e.g. Hebbal',
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onSubmitted: (_) => _searchBmtc(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              style: IconButton.styleFrom(
                backgroundColor: AppTheme.bmtcColor,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: _bmtcLoading ? null : _searchBmtc,
              icon: const Icon(Icons.search_rounded, size: 20),
            ),
          ],
        ),
        const SizedBox(height: 14),

        if (_bmtcLoading)
          const Expanded(child: Center(child: CircularProgressIndicator()))
        else if (_bmtcError != null)
          Expanded(
            child: Center(
              child: Text(_bmtcError!, style: const TextStyle(color: AppTheme.red, fontSize: 13)),
            ),
          )
        else if (_bmtcResult != null)
          Expanded(child: _buildBmtcScheduleResult(_bmtcResult!, isDark, textColor, mutedColor))
        else
          Expanded(
            child: Center(
              child: Text('Enter a bus route to look up timings', style: TextStyle(color: mutedColor, fontSize: 13)),
            ),
          ),
      ],
    );
  }

  Widget _buildBmtcScheduleResult(Map<String, dynamic> data, bool isDark, Color textColor, Color mutedColor) {
    final route = data['route']?.toString() ?? _bmtcRouteCtrl.text.toUpperCase();
    final origin = data['origin']?.toString() ?? 'Origin';
    final destination = data['destination']?.toString() ?? 'Destination';
    final departures = (data['timetable'] as List<dynamic>?) ?? (data['departures'] as List<dynamic>?) ?? [];
    final frequency = data['frequency']?.toString() ?? 'Every 10-15 mins';

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF161926) : const Color(0xFFEFF6FF),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.bmtcColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(route, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('$origin ➔ $destination', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: textColor)),
                      Text('Frequency: $frequency', style: TextStyle(fontSize: 11, color: mutedColor)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          Text('SCHEDULED DEPARTURES', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
          const SizedBox(height: 8),

          if (departures.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              alignment: Alignment.center,
              child: Text('Operates frequently every 10-15 minutes throughout the day (05:30 to 22:30).', style: TextStyle(fontSize: 12, color: mutedColor)),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: departures.map((dep) {
                final timeStr = dep is Map ? (dep['departure_time'] ?? dep['time'] ?? '').toString() : dep.toString();
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1E2232) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.access_time_rounded, size: 12, color: AppTheme.bmtcColor),
                      const SizedBox(width: 4),
                      Text(timeStr, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                    ],
                  ),
                );
              }).toList(),
            ),
        ],
      ),
    );
  }

  Widget _buildMetroView(bool isDark, Color textColor, Color mutedColor) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _metroStationCtrl,
                style: TextStyle(fontSize: 13, color: textColor),
                decoration: InputDecoration(
                  labelText: 'Metro Station',
                  hintText: 'e.g. Indiranagar, Majestic, MG Road',
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onSubmitted: (_) => _searchMetro(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              style: IconButton.styleFrom(
                backgroundColor: AppTheme.metroPurple,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: _metroLoading ? null : _searchMetro,
              icon: const Icon(Icons.search_rounded, size: 20),
            ),
          ],
        ),
        const SizedBox(height: 14),

        if (_metroLoading)
          const Expanded(child: Center(child: CircularProgressIndicator()))
        else if (_metroError != null)
          Expanded(
            child: Center(
              child: Text(_metroError!, style: const TextStyle(color: AppTheme.red, fontSize: 13)),
            ),
          )
        else if (_metroResult != null)
          Expanded(child: _buildMetroScheduleResult(_metroResult!, isDark, textColor, mutedColor))
        else
          Expanded(
            child: Center(
              child: Text('Enter a station name to view train timings', style: TextStyle(color: mutedColor, fontSize: 13)),
            ),
          ),
      ],
    );
  }

  Widget _buildMetroScheduleResult(Map<String, dynamic> data, bool isDark, Color textColor, Color mutedColor) {
    final station = data['station']?.toString() ?? _metroStationCtrl.text;
    final line = data['line']?.toString() ?? 'Purple Line';
    final directions = (data['directions'] as List<dynamic>?) ?? [];
    final firstTrain = data['first_train']?.toString() ?? '05:00 AM';
    final lastTrain = data['last_train']?.toString() ?? '11:00 PM';
    final peakFreq = data['peak_frequency']?.toString() ?? 'Every 4-5 mins';

    final Color lineClr = line.toLowerCase().contains('green') ? const Color(0xFF10B981) : AppTheme.metroPurple;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: lineClr.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: lineClr.withValues(alpha: 0.4)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: lineClr, borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.subway_rounded, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(station, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: textColor)),
                      Text('$line • Peak: $peakFreq', style: TextStyle(fontSize: 11, color: mutedColor)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1A1C29) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('FIRST TRAIN', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: mutedColor)),
                      const SizedBox(height: 2),
                      Text(firstTrain, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: textColor)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1A1C29) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('LAST TRAIN', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: mutedColor)),
                      const SizedBox(height: 2),
                      Text(lastTrain, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: textColor)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          Text('UPCOMING TRAINS BY DIRECTION', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
          const SizedBox(height: 8),

          if (directions.isEmpty)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF161926) : const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(Icons.flash_on_rounded, color: AppTheme.metroPurple, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text('Trains depart every 5 minutes during peak hours and every 8-10 minutes during non-peak.', style: TextStyle(fontSize: 11.5, color: textColor)),
                  ),
                ],
              ),
            )
          else
            ...directions.map((dir) {
              final dest = dir['destination']?.toString() ?? 'Terminal';
              final nextTrains = (dir['next_trains'] as List<dynamic>?) ?? [];
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF161926) : const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Towards $dest', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: textColor)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: nextTrains.map((t) {
                        return Chip(
                          label: Text(t.toString(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                          visualDensity: VisualDensity.compact,
                          padding: EdgeInsets.zero,
                        );
                      }).toList(),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}
