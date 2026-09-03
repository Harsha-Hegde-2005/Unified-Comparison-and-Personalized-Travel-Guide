import 'dart:async';
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
  const WeatherReportModal({super.key});

  @override
  State<WeatherReportModal> createState() => _WeatherReportModalState();
}

class _WeatherReportModalState extends State<WeatherReportModal> {
  Map<String, dynamic>? _weather;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  Future<void> _fetchWeather() async {
    final res = await ApiService.fetchWeatherReport(12.9716, 77.5946, 'Bengaluru');
    if (mounted) {
      setState(() {
        _weather = res;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);

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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.wb_sunny_rounded, color: Colors.amber, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    'Bengaluru Transit Weather',
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
          const SizedBox(height: 16),

          if (_loading)
            const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator()))
          else ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  const Icon(Icons.cloud_queue_rounded, size: 48, color: Colors.white),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${_weather?['temperature'] ?? 26}°C · ${_weather?['condition'] ?? 'Partly Cloudy'}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Humidity: ${_weather?['humidity'] ?? 65}% · Wind: ${_weather?['wind_speed'] ?? 12} km/h',
                          style: const TextStyle(color: Colors.white70, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Advisory box
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.blue.withValues(alpha: isDark ? 0.15 : 0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.blue.withValues(alpha: 0.3)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline_rounded, color: AppTheme.blue, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _weather?['advisory'] ??
                          'Pleasant weather in Bengaluru. Namma Metro and AC Vajra buses are operating normally with standard headway.',
                      style: TextStyle(fontSize: 13, color: textColor, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 20),
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
  final String? duration;

  const WalkNavigationModal({
    super.key,
    required this.instruction,
    this.fromLocation,
    this.toLocation,
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
  }

  @override
  void dispose() {
    _gpsSubscription?.cancel();
    super.dispose();
  }

  void _startGpsTracking() {
    _gpsSubscription = GeolocationHelper.watchPositionStream().listen((pos) {
      if (mounted) {
        setState(() {
          _liveUserGps = pos;
        });
      }
    });
    GeolocationHelper.getCurrentPosition().then((pos) {
      if (pos != null && mounted) {
        setState(() {
          _liveUserGps = pos;
        });
      }
    });
  }

  ll.LatLng? _lookup(String text) {
    final t = text.toLowerCase();
    for (final entry in _knownCoords.entries) {
      if (t.contains(entry.key)) return entry.value;
    }
    return null;
  }

  List<Map<String, dynamic>> _realWalkSteps = [];

  List<ll.LatLng> _generateCurvedStreetPolyline(ll.LatLng start, ll.LatLng end) {
    final List<ll.LatLng> points = [start];
    final dLat = end.latitude - start.latitude;
    final dLng = end.longitude - start.longitude;

    if (dLat.abs() < 0.0001 && dLng.abs() < 0.0001) {
      return [
        start,
        ll.LatLng(start.latitude + 0.001, start.longitude + 0.001),
        ll.LatLng(start.latitude + 0.002, start.longitude + 0.003),
      ];
    }

    final corner1 = ll.LatLng(start.latitude + (dLat * 0.1), start.longitude + (dLng * 0.65));
    final corner2 = ll.LatLng(start.latitude + (dLat * 0.85), start.longitude + (dLng * 0.65));

    for (int i = 1; i <= 3; i++) {
      final t = i / 3.0;
      points.add(ll.LatLng(
        start.latitude + (corner1.latitude - start.latitude) * t,
        start.longitude + (corner1.longitude - start.longitude) * t,
      ));
    }

    for (int i = 1; i <= 3; i++) {
      final t = i / 3.0;
      points.add(ll.LatLng(
        corner1.latitude + (corner2.latitude - corner1.latitude) * t,
        corner1.longitude + (corner2.longitude - corner1.longitude) * t,
      ));
    }

    for (int i = 1; i <= 2; i++) {
      final t = i / 2.0;
      points.add(ll.LatLng(
        corner2.latitude + (end.latitude - corner2.latitude) * t,
        corner2.longitude + (end.longitude - corner2.longitude) * t,
      ));
    }

    points.add(end);
    return points;
  }

  Future<void> _loadWalkCoords() async {
    final rawTarget = widget.toLocation ?? widget.instruction;
    final rawOrigin = widget.fromLocation ?? widget.instruction;

    final String cleanPrefixRegex = r'^(Walk\s+(to|from)|Get\s+down\s+at|Disembark\s+at|Board\s+(the\s+)?|Head\s+out\s+(towards|from)|Change\s+lines\s+at)\s+';
    String targetName = rawTarget
        .replaceAll(RegExp(cleanPrefixRegex, caseSensitive: false), '')
        .replaceAll(RegExp(r'\s*\([^)]*\)'), '')
        .trim();
    String originName = rawOrigin
        .replaceAll(RegExp(cleanPrefixRegex, caseSensitive: false), '')
        .replaceAll(RegExp(r'\s*\([^)]*\)'), '')
        .trim();

    // Live GPS position for user tracking overlay
    final liveGps = _liveUserGps ?? await GeolocationHelper.getCurrentPosition();

    ll.LatLng? startCoord;
    ll.LatLng? targetCoord;

    // Resolve leg origin coordinate: ONLY use liveGps if originName explicitly contains "current" or "my location"!
    if (originName.toLowerCase().contains('current') || originName.toLowerCase().contains('my location')) {
      startCoord = liveGps;
    } else if (originName.isNotEmpty) {
      startCoord = await ApiService.geocodeHighPrecision(originName) ?? _lookup(originName);
    }

    // Resolve leg destination coordinate
    if (targetName.isNotEmpty) {
      targetCoord = await ApiService.geocodeHighPrecision(targetName) ?? _lookup(targetName);
    }

    // Fallbacks
    startCoord ??= liveGps ?? const ll.LatLng(12.9767, 77.5713);
    targetCoord ??= ll.LatLng(startCoord.latitude + 0.003, startCoord.longitude + 0.003);

    // Guarantee distinct coordinates so bounds distance > 0
    if ((startCoord.latitude - targetCoord.latitude).abs() < 0.0001 &&
        (startCoord.longitude - targetCoord.longitude).abs() < 0.0001) {
      targetCoord = ll.LatLng(startCoord.latitude + 0.003, startCoord.longitude + 0.003);
    }

    // Fetch actual road-following street walking polyline via OSRM Foot API
    final resWalk = await ApiService.fetchWalkingRoute(
      startCoord.latitude,
      startCoord.longitude,
      targetCoord.latitude,
      targetCoord.longitude,
    );

    List<ll.LatLng> points = [];
    List<Map<String, dynamic>> steps = [];

    if (resWalk != null && resWalk['points'] is List && (resWalk['points'] as List).isNotEmpty) {
      points = List<ll.LatLng>.from(resWalk['points']);
      if (resWalk['steps'] is List) {
        steps = List<Map<String, dynamic>>.from(resWalk['steps']);
      }
    }

    if (points.isEmpty || points.length < 5) {
      points = _generateCurvedStreetPolyline(startCoord, targetCoord);
    }

    if (steps.isEmpty) {
      steps = [
        {'instruction': 'Head out on pedestrian footpath towards $targetName', 'distance': '120 m'},
        {'instruction': 'Walk along main road towards station platform entrance', 'distance': '850 m'},
        {'instruction': 'Cross zebra pedestrian walkway', 'distance': '50 m'},
        {'instruction': 'Arrive at $targetName Entrance Gate', 'distance': '30 m'},
      ];
    }

    if (mounted) {
      setState(() {
        _walkPoints = points;
        _realWalkSteps = steps;
      });

      WidgetsBinding.instance.addPostFrameCallback((_) {
        try {
          if (_walkPoints.length >= 2) {
            final f = _walkPoints.first;
            final l = _walkPoints.last;
            if ((f.latitude - l.latitude).abs() > 0.0001 || (f.longitude - l.longitude).abs() > 0.0001) {
              final bounds = fm.LatLngBounds.fromPoints(_walkPoints);
              _mapController.fitCamera(
                fm.CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(40)),
              );
            }
          }
        } catch (_) {}
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final targetName = widget.toLocation ?? (widget.instruction.contains('to ') ? widget.instruction.split('to ').last : widget.instruction);

    return Container(
      height: MediaQuery.of(context).size.height * 0.82,
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
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.walkColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.navigation_rounded, color: AppTheme.walkColor, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.instruction,
                        style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
                      ),
                      Text(
                        'Live walking path to $targetName',
                        style: TextStyle(fontSize: 10, color: mutedColor),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Map view of walking path
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: fm.FlutterMap(
                mapController: _mapController,
                options: fm.MapOptions(
                  initialCenter: _walkPoints.isNotEmpty ? _walkPoints.first : const ll.LatLng(12.9716, 77.5946),
                  initialZoom: 15.5,
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
                          strokeWidth: 5.0,
                          color: AppTheme.walkColor,
                          isDotted: true,
                        ),
                      ],
                    ),
                  fm.MarkerLayer(
                    markers: [
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
                      if (_liveUserGps != null)
                        fm.Marker(
                          point: _liveUserGps!,
                          width: 34,
                          height: 34,
                          child: Container(
                            decoration: BoxDecoration(
                              color: AppTheme.blue,
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 2),
                              boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 6)],
                            ),
                            child: const Icon(Icons.my_location_rounded, size: 16, color: Colors.white),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Dynamic Turn-by-Turn Steps
          Text('TURN-BY-TURN WALKING STEPS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: mutedColor)),
          const SizedBox(height: 6),
          Container(
            height: 120,
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.getBorder(isDark)),
            ),
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: _realWalkSteps.length,
              separatorBuilder: (context, index) => const Divider(height: 10),
              itemBuilder: (context, index) {
                final s = _realWalkSteps[index];
                return _buildWalkStep(
                  '${index + 1}. ${s['instruction'] ?? ''}',
                  s['distance']?.toString() ?? '',
                  isDark,
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWalkStep(String title, String dist, bool isDark) {
    return Row(
      children: [
        const Icon(Icons.subdirectory_arrow_right_rounded, size: 16, color: AppTheme.walkColor),
        const SizedBox(width: 8),
        Expanded(
          child: Text(title, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.getText(isDark))),
        ),
        Text(dist, style: TextStyle(fontSize: 10, color: AppTheme.getMuted(isDark), fontWeight: FontWeight.bold)),
      ],
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

  const AllBusesModal({
    super.key,
    required this.source,
    required this.destination,
    this.time,
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
                    'POSSIBLE BUS NUMBERS CONNECTING YOUR STOPS',
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: uniqueBusNums.take(16).map((rn) {
                      final isV = _isVajra(rn);
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          rn,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: isV ? AppTheme.blue : AppTheme.bmtcColor,
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
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      routeNo,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w900,
                        color: isV ? AppTheme.blue : AppTheme.bmtcColor,
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
                      Text('Fare: ₹$fare', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.green)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text('Estimated duration: $time mins ($stopsCount intermediate stops)', style: TextStyle(fontSize: 11, color: mutedColor)),

                  if (altBuses.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text('OTHER BUSES RUNNING THIS EXACT ROUTE:', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor)),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: altBuses.map((ab) {
                        final abStr = ab.toString();
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF2D3142) : const Color(0xFFE2E8F0),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            abStr,
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: textColor),
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
                        Text('Buses: ', style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold)),
                        Wrap(
                          spacing: 4,
                          children: buses.map((b) {
                            final isV = _isVajra(b);
                            return Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                b,
                                style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
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
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: (isV ? AppTheme.blue : AppTheme.bmtcColor).withValues(alpha: 0.15),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        routeName,
                                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: isV ? AppTheme.blue : AppTheme.bmtcColor),
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
                              Text('ALTERNATIVE BUSES FOR THIS LEG:', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mutedColor)),
                              const SizedBox(height: 4),
                              Wrap(
                                spacing: 4,
                                runSpacing: 4,
                                children: altBuses.take(12).map((ab) {
                                  final abStr = ab.toString();
                                  return Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: isDark ? const Color(0xFF2D3142) : const Color(0xFFE2E8F0),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      abStr,
                                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: textColor),
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
