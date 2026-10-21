import 'package:flutter/material.dart';
import '../theme.dart';

// ─────────────────────────────────────────────────────────────
// 1. CHATBOT MULTIMODAL COMPARISON DASHBOARD (Matching Website)
// ─────────────────────────────────────────────────────────────
class ChatComparisonDashboard extends StatefulWidget {
  final Map<String, dynamic> data;
  final ValueChanged<String> onSelectRoute;
  final ValueChanged<String> onSendMessage;

  const ChatComparisonDashboard({
    super.key,
    required this.data,
    required this.onSelectRoute,
    required this.onSendMessage,
  });

  @override
  State<ChatComparisonDashboard> createState() => _ChatComparisonDashboardState();
}

class _ChatComparisonDashboardState extends State<ChatComparisonDashboard> {
  String? _expandedMode;

  static const Map<String, String> _modeIcons = {
    'bmtc': '🚌',
    'metro': '🚇',
    'multimodal': '🔀',
    'ola': '🚕',
    'uber': '🚙',
    'rapido': '🏍️',
    'namma_yatri': '🛺',
    'car': '🚗',
    'bike': '🛵',
  };

  static const Map<String, String> _modeLabels = {
    'bmtc': 'BMTC Bus',
    'metro': 'Namma Metro',
    'multimodal': 'Bus + Metro',
    'ola': 'Ola Cab',
    'uber': 'Uber Cab',
    'rapido': 'Rapido Ride',
    'namma_yatri': 'Namma Yatri',
    'car': 'Personal Car',
    'bike': 'Personal Bike',
  };

  static const Map<String, Color> _modeColors = {
    'bmtc': Color(0xFF3B82F6),
    'metro': Color(0xFF10B981),
    'multimodal': Color(0xFFEC4899),
    'ola': Color(0xFFF5C518),
    'uber': Color(0xFF94A3B8),
    'rapido': Color(0xFFA855F7),
    'namma_yatri': Color(0xFFF97316),
    'car': Color(0xFF22C55E),
    'bike': Color(0xFF14B8A6),
  };

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final rawOptions = widget.data['options'] as List<dynamic>? ?? [];
    if (rawOptions.isEmpty) return const SizedBox.shrink();

    final destination = widget.data['destination']?.toString() ?? 'Destination';
    final rawPlaces = widget.data['places'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Mode Options Cards
        ...rawOptions.map((item) {
          if (item is! Map<String, dynamic>) return const SizedBox.shrink();
          final mode = item['mode']?.toString() ?? 'bmtc';
          final isExpanded = _expandedMode == mode;
          final color = _modeColors[mode] ?? const Color(0xFF64748B);
          final label = _modeLabels[mode] ?? mode;
          final icon = _modeIcons[mode] ?? '🚗';

          final cost = item['cost']?.toString() ?? '0';
          final time = item['time']?.toString() ?? '0';
          final dist = item['details']?['distance'] ?? item['distance'] ?? item['walking_distance'] ?? 0;
          final walkDist = item['walking_distance'] ?? 0;
          final co2Kg = (item['co2_kg'] as num?)?.toDouble() ?? 0.0;
          final co2Grams = (co2Kg * 1000).toStringAsFixed(0);
          final isPersonal = mode == 'car' || mode == 'bike';
          final fuelNeeded = item['details']?['fuel_needed'] ?? item['fuel_needed'] ?? 0;
          final score = (item['score'] as num?)?.toDouble();
          final explanation = item['explanation']?.toString();
          final legs = item['legs'] as List<dynamic>?;

          return Container(
            margin: const EdgeInsets.only(top: 8),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF121420) : const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isExpanded ? color : (isDark ? const Color(0xFF272A3D) : const Color(0xFFE2E8F0)),
                width: isExpanded ? 1.5 : 1.0,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: isDark ? 0.25 : 0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              children: [
                // Header row
                InkWell(
                  onTap: () {
                    setState(() {
                      _expandedMode = isExpanded ? null : mode;
                    });
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Text(icon, style: const TextStyle(fontSize: 18)),
                            const SizedBox(width: 8),
                            Text(
                              label,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                color: textColor,
                              ),
                            ),
                            if (score != null) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: color.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  '${score.round()}% Match',
                                  style: TextStyle(
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.w800,
                                    color: color,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        Row(
                          children: [
                            Text(
                              '₹$cost',
                              style: TextStyle(
                                fontSize: 13.5,
                                fontWeight: FontWeight.w900,
                                color: textColor,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Icon(
                              isExpanded ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                              size: 16,
                              color: mutedColor,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                // Quick stats grid
                Padding(
                  padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF08090F) : const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('🕒 $time min', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                            Text('📏 $dist km', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                            if (isPersonal)
                              Text('⛽ $fuelNeeded L', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor))
                            else
                              Text('🚶 $walkDist km', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('🌿 CO₂: ${co2Grams}g', style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold)),
                            if (isPersonal)
                              const Text('* Estimated', style: TextStyle(fontSize: 9, color: Color(0xFFF5C518), fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                // Expanded breakdown & Select button
                if (isExpanded) ...[
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Divider(height: 1),
                        const SizedBox(height: 8),
                        if (explanation != null)
                          Text(
                            explanation,
                            style: TextStyle(fontSize: 11, color: mutedColor, height: 1.4),
                          ),

                        // Multi-stop leg breakdown
                        if (legs != null && legs.length > 1) ...[
                          const SizedBox(height: 8),
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: isDark ? const Color(0xFF08090F) : const Color(0xFFEFF6FF),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'ITINERARY BREAKDOWN',
                                  style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: mutedColor),
                                ),
                                const SizedBox(height: 4),
                                ...legs.asMap().entries.map((entry) {
                                  final idx = entry.key;
                                  final leg = entry.value as Map<String, dynamic>;
                                  final lSrc = leg['from_stop'] ?? leg['source'] ?? 'Stop ${idx + 1}';
                                  final lDst = leg['to_stop'] ?? leg['destination'] ?? 'Stop ${idx + 2}';
                                  final lCost = leg['cost'] ?? 0;
                                  final lTime = leg['time'] ?? 0;
                                  return Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 2),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Text('📍 Leg ${idx + 1}: $lSrc → $lDst', style: TextStyle(fontSize: 10.5, color: textColor), overflow: TextOverflow.ellipsis),
                                        ),
                                        Text('₹$lCost · ${lTime}m', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: textColor)),
                                      ],
                                    ),
                                  );
                                }),
                              ],
                            ),
                          ),
                        ],
                        const SizedBox(height: 10),

                        // Select & Draw Route button
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: color,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              padding: const EdgeInsets.symmetric(vertical: 10),
                            ),
                            icon: const Icon(Icons.map_rounded, size: 16),
                            label: const Text('Select & Draw Route 🗺️', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800)),
                            onPressed: () => widget.onSelectRoute(mode),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          );
        }),

        const SizedBox(height: 10),

        // Explore Nearby Category Chips Row
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _buildCategoryChip('🏛️ Tourist Spots', 'attraction', destination, isDark, textColor),
              _buildCategoryChip('🍔 Restaurants', 'restaurant', destination, isDark, textColor),
              _buildCategoryChip('☕ Cafes', 'cafe', destination, isDark, textColor),
              _buildCategoryChip('🏨 Hotels', 'hotel', destination, isDark, textColor),
              _buildCategoryChip('🛍️ Shopping', 'mall', destination, isDark, textColor),
              _buildCategoryChip('🏥 Hospitals', 'hospital', destination, isDark, textColor),
            ],
          ),
        ),

        // Display embedded places if returned with travel query
        if (rawPlaces.isNotEmpty) ...[
          const SizedBox(height: 8),
          ChatNearbyPlacesDashboard(
            data: {
              'places': rawPlaces,
              'location': destination,
              'is_live': !(widget.data['is_estimated'] == true),
            },
            onSelectPlace: (place) {
              final name = place['name']?.toString() ?? 'Destination';
              final src = widget.data['source']?.toString() ?? 'Current Location';
              widget.onSelectRoute(name);
            },
          ),
        ],
      ],
    );
  }

  Widget _buildCategoryChip(String label, String cat, String dest, bool isDark, Color textColor) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ActionChip(
        backgroundColor: isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9),
        side: BorderSide(color: isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        label: Text(label, style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: textColor)),
        onPressed: () => widget.onSendMessage('Explore $cat near $dest'),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 2. NEARBY PLACES DASHBOARD (Matching Website)
// ─────────────────────────────────────────────────────────────
class ChatNearbyPlacesDashboard extends StatelessWidget {
  final Map<String, dynamic> data;
  final ValueChanged<Map<String, dynamic>> onSelectPlace;

  const ChatNearbyPlacesDashboard({
    super.key,
    required this.data,
    required this.onSelectPlace,
  });

  static const Map<String, String> _categoryEmojis = {
    'restaurant': '🍔',
    'cafe': '☕',
    'hotel': '🏨',
    'hospital': '🏥',
    'mall': '🛍️',
    'atm': '🏧',
    'petrol_pump': '⛽',
    'bus_stop': '🚌',
    'metro_station': '🚇',
    'attraction': '🏛️',
  };

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final places = (data['places'] as List<dynamic>?) ?? [];
    final location = data['location']?.toString() ?? 'Bengaluru';
    final isLive = data['is_live'] == true;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF121420) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '📍 EXPLORE NEAR $location'.toUpperCase(),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF3B82F6)),
              ),
              if (!isLive)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF5C518).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text('Verified', style: TextStyle(fontSize: 8.5, color: Color(0xFFF5C518), fontWeight: FontWeight.bold)),
                ),
            ],
          ),
          const SizedBox(height: 10),

          if (places.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text('No nearby places found.', style: TextStyle(fontSize: 12, color: mutedColor)),
              ),
            )
          else
            ...places.take(5).map((p) {
              if (p is! Map<String, dynamic>) return const SizedBox.shrink();
              final name = p['name']?.toString() ?? 'Place';
              final cat = p['category']?.toString().toLowerCase() ?? 'restaurant';
              final emoji = _categoryEmojis[cat] ?? '📍';
              final rating = p['rating']?.toString();
              final address = p['address']?.toString() ?? '';
              final dist = p['distance_km'] ?? p['distance'];
              final distStr = dist != null ? '~${(dist as num).toStringAsFixed(1)} km' : '';

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF08090F) : Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: isDark ? const Color(0xFF1E2440) : const Color(0xFFE2E8F0)),
                ),
                child: Row(
                  children: [
                    Text(emoji, style: const TextStyle(fontSize: 22)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(name, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                          if (address.isNotEmpty)
                            Text(address, style: TextStyle(fontSize: 10.5, color: mutedColor), maxLines: 1, overflow: TextOverflow.ellipsis),
                          Row(
                            children: [
                              if (rating != null) ...[
                                const Icon(Icons.star_rounded, color: Colors.amber, size: 13),
                                const SizedBox(width: 2),
                                Text(rating, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: textColor)),
                                const SizedBox(width: 8),
                              ],
                              if (distStr.isNotEmpty)
                                Text(distStr, style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.blue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        minimumSize: const Size(0, 30),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: () => onSelectPlace(p),
                      child: const Text('Directions', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold)),
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

// ─────────────────────────────────────────────────────────────
// 3. TRAFFIC STATUS QUERY CARD (Matching Website)
// ─────────────────────────────────────────────────────────────
class ChatTrafficQueryCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback? onTap;

  const ChatTrafficQueryCard({
    super.key,
    required this.data,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final level = data['congestion_level']?.toString().toLowerCase() ?? 'moderate';
    final isHeavy = level == 'heavy';
    final isMod = level == 'moderate';

    final Color statusColor = isHeavy
        ? const Color(0xFFEF4444)
        : isMod
            ? const Color(0xFFF5C518)
            : const Color(0xFF22C55E);

    final String statusEmoji = isHeavy ? '🔴' : isMod ? '🟡' : '🟢';
    final String statusTitle = isHeavy
        ? 'Heavy Traffic'
        : isMod
            ? 'Moderate Traffic'
            : 'Traffic Clear';

    final driveTime = data['drive_time_min'];
    final transitTime = data['transit_time'];
    final src = data['source']?.toString();
    final dst = data['destination']?.toString();

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: statusColor.withValues(alpha: isDark ? 0.12 : 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: statusColor.withValues(alpha: 0.35)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(statusEmoji, style: const TextStyle(fontSize: 28)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    statusTitle,
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: textColor),
                  ),
                  if (src != null && dst != null)
                    Text('$src → $dst', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                  if (driveTime != null)
                    Text('Drive time: ~$driveTime mins', style: TextStyle(fontSize: 11, color: mutedColor)),
                  if (transitTime != null)
                    Text('Public transit: ~$transitTime mins', style: TextStyle(fontSize: 11, color: mutedColor)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, color: Colors.grey, size: 20),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 4. NEAREST STOPS CARD (Matching Website)
// ─────────────────────────────────────────────────────────────
class ChatNearestStopsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final ValueChanged<String>? onSelectStop;

  const ChatNearestStopsCard({
    super.key,
    required this.data,
    this.onSelectStop,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final nearest = data['nearest'] as Map<String, dynamic>? ?? {};
    final bmtcStops = (nearest['bmtc'] as List<dynamic>?) ?? [];
    final metroStops = (nearest['metro'] as List<dynamic>?) ?? [];

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF0D1624) : const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.near_me_rounded, color: Color(0xFF3B82F6), size: 16),
              SizedBox(width: 6),
              Text('NEARBY TRANSIT STOPS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF3B82F6))),
            ],
          ),
          const SizedBox(height: 8),

          if (bmtcStops.isEmpty && metroStops.isEmpty)
            Text('No nearby transit stops found.', style: TextStyle(fontSize: 11, color: mutedColor))
          else ...[
            ...bmtcStops.take(2).map((item) {
              final name = (item is List && item.isNotEmpty) ? item[0].toString() : item.toString();
              final dist = (item is List && item.length > 1) ? (item[1] as num).toStringAsFixed(2) : null;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(child: Text('🚌 $name', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold, color: textColor), overflow: TextOverflow.ellipsis)),
                    if (dist != null)
                      Text('$dist km', style: TextStyle(fontSize: 10.5, color: mutedColor, fontWeight: FontWeight.bold)),
                  ],
                ),
              );
            }),
            ...metroStops.take(2).map((item) {
              final name = (item is List && item.isNotEmpty) ? item[0].toString() : item.toString();
              final dist = (item is List && item.length > 1) ? (item[1] as num).toStringAsFixed(2) : null;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(child: Text('🚇 $name Metro', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold, color: textColor), overflow: TextOverflow.ellipsis)),
                    if (dist != null)
                      Text('$dist km', style: TextStyle(fontSize: 10.5, color: mutedColor, fontWeight: FontWeight.bold)),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────
// 5. WEATHER QUERY CARD (Matching Website)
// ─────────────────────────────────────────────────────────────
class ChatWeatherCard extends StatelessWidget {
  final Map<String, dynamic> data;

  const ChatWeatherCard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final weather = data['weather']?.toString().toLowerCase() ?? 'clear';
    final isRain = weather.contains('rain') || weather.contains('storm');
    final timeStr = data['time']?.toString() ?? 'Today';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isRain
            ? const Color(0xFF3B82F6).withValues(alpha: isDark ? 0.15 : 0.08)
            : Colors.amber.withValues(alpha: isDark ? 0.15 : 0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isRain ? const Color(0xFF3B82F6).withValues(alpha: 0.4) : Colors.amber.withValues(alpha: 0.4),
        ),
      ),
      child: Row(
        children: [
          Text(isRain ? '🌧️' : '☀️', style: const TextStyle(fontSize: 28)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isRain ? 'Rain Forecast Alert' : 'Clear Weather Forecast',
                  style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w900, color: textColor),
                ),
                Text('Forecast for $timeStr • Condition: ${weather.toUpperCase()}', style: TextStyle(fontSize: 11, color: mutedColor)),
                if (isRain)
                  const Text('Expect road speeds to drop ~35%. Metro recommended.', style: TextStyle(fontSize: 10, color: Color(0xFF3B82F6), fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
