import 'package:flutter/material.dart';
import '../theme.dart';

/// Journey Context Banner matching JourneyContextBanner in App.jsx
/// Displays departure time, ETA, live traffic status with delay, and
/// location/ETA-aware weather along the transit corridor.
class JourneyContextBanner extends StatelessWidget {
  final Map<String, dynamic>? journey;
  final Map<String, dynamic>? traffic;
  final Map<String, dynamic>? weather;

  const JourneyContextBanner({
    super.key,
    this.journey,
    this.traffic,
    this.weather,
  });

  @override
  Widget build(BuildContext context) {
    if (journey == null && traffic == null && weather == null) {
      return const SizedBox.shrink();
    }

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final trafficLevel = (traffic?['level']?.toString().toUpperCase()) ?? 'LOW';
    final delayMin = (traffic?['delay_min'] as num?)?.toDouble() ?? 0.0;
    final trafficSource = traffic?['source']?.toString() ?? 'local';
    final trafficType = traffic?['type']?.toString() ?? 'estimated';

    Color trafficBg;
    Color trafficTextColor;
    Color trafficBorder;
    String trafficLabel;

    switch (trafficLevel) {
      case 'SEVERE':
        trafficBg = const Color(0xFFEF4444).withValues(alpha: isDark ? 0.25 : 0.12);
        trafficTextColor = const Color(0xFFEF4444);
        trafficBorder = const Color(0xFFEF4444).withValues(alpha: 0.4);
        trafficLabel = 'Severe Traffic';
        break;
      case 'HIGH':
        trafficBg = const Color(0xFFEF4444).withValues(alpha: isDark ? 0.25 : 0.12);
        trafficTextColor = const Color(0xFFEF4444);
        trafficBorder = const Color(0xFFEF4444).withValues(alpha: 0.4);
        trafficLabel = 'Heavy Traffic';
        break;
      case 'MODERATE':
        trafficBg = const Color(0xFFF59E0B).withValues(alpha: isDark ? 0.25 : 0.12);
        trafficTextColor = const Color(0xFFF59E0B);
        trafficBorder = const Color(0xFFF59E0B).withValues(alpha: 0.4);
        trafficLabel = 'Moderate Traffic';
        break;
      case 'LOW':
      default:
        trafficBg = const Color(0xFF10B981).withValues(alpha: isDark ? 0.25 : 0.12);
        trafficTextColor = const Color(0xFF10B981);
        trafficBorder = const Color(0xFF10B981).withValues(alpha: 0.4);
        trafficLabel = 'Low Traffic';
        break;
    }

    final origW = weather?['origin'] as Map<String, dynamic>?;
    final destW = weather?['destination'] as Map<String, dynamic>?;
    final checkpoints = (weather?['checkpoints'] as List<dynamic>?) ?? [];
    final advisory = weather?['advisory']?.toString();

    final sourceName = journey?['source']?.toString() ?? 'Start';
    final destName = journey?['destination']?.toString() ?? 'End';
    final depTimeStr = journey?['departure_time']?.toString() ?? 'Now';
    final etaStr = journey?['estimated_arrival_time']?.toString() ?? 'ETA';
    final durMin = journey?['estimated_duration_min']?.toString() ?? '30';

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? const Color(0xFF2D2A45) : const Color(0xFFEDE9FE),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF7C3AED).withValues(alpha: isDark ? 0.15 : 0.05),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 1. Top Row: Journey ETA & Traffic Status ───────────────────────
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: const Color(0xFF7C3AED).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Center(
                  child: Text('⏱️', style: TextStyle(fontSize: 16)),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$sourceName → $destName',
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: textColor,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Departs: $depTimeStr • Expected Arrival: ~$etaStr (~$durMin min)',
                      style: TextStyle(
                        fontSize: 11,
                        color: mutedColor,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // ── Traffic Badge Row ──────────────────────────────────────────────
          if (traffic != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: trafficBg,
                    border: Border.all(color: trafficBorder),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('🚦', style: TextStyle(fontSize: 12)),
                      const SizedBox(width: 5),
                      Text(
                        '$trafficLabel${delayMin > 0 ? " (+${delayMin.toStringAsFixed(0)}m delay)" : ""}',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w800,
                          color: trafficTextColor,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1E202C) : const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Text(
                    trafficSource == 'google'
                        ? (trafficType == 'predicted' ? 'Google Predicted Traffic' : 'Google Live Traffic')
                        : 'Local Corridor Traffic Est.',
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                      color: mutedColor,
                    ),
                  ),
                ),
              ],
            ),
          ],

          // ── 2. Middle Row: Route Weather Profile Along Corridor ─────────────
          if (weather != null && (origW != null || destW != null)) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF141724) : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(12),
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
                          const Text('🌦️', style: TextStyle(fontSize: 12)),
                          const SizedBox(width: 6),
                          Text(
                            'WEATHER ALONG ROUTE',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w900,
                              color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF475569),
                              letterSpacing: 0.4,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF3B82F6).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          weather?['type'] == 'forecast' ? 'ETA-Aware Forecast' : 'Live Conditions',
                          style: const TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF3B82F6),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Weather Timeline along corridor
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        // Origin Weather
                        if (origW != null) ...[
                          _buildWeatherPill(
                            title: 'Origin ($depTimeStr)',
                            temp: origW['temperature'],
                            rainProb: origW['rain_probability'],
                            cond: origW['condition']?.toString() ?? 'Clear',
                            isDark: isDark,
                            isDestination: false,
                          ),
                        ],

                        // Checkpoints
                        ...checkpoints.map((cp) {
                          final cpWeather = cp['weather'] as Map<String, dynamic>?;
                          return Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Padding(
                                padding: EdgeInsets.symmetric(horizontal: 4),
                                child: Icon(Icons.arrow_forward_rounded, size: 12, color: Colors.grey),
                              ),
                              _buildWeatherPill(
                                title: '${cp["name"] ?? "Midpoint"} (${cp["eta"] ?? "ETA"})',
                                temp: cpWeather?['temperature'],
                                rainProb: cpWeather?['rain_probability'],
                                cond: cpWeather?['condition']?.toString() ?? 'Clear',
                                isDark: isDark,
                                isDestination: false,
                              ),
                            ],
                          );
                        }),

                        // Destination Weather
                        if (destW != null) ...[
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 4),
                            child: Icon(Icons.arrow_forward_rounded, size: 12, color: Colors.grey),
                          ),
                          _buildWeatherPill(
                            title: 'Destination ($etaStr)',
                            temp: destW['temperature'],
                            rainProb: destW['rain_probability'],
                            cond: destW['condition']?.toString() ?? 'Clear',
                            isDark: isDark,
                            isDestination: true,
                          ),
                        ],
                      ],
                    ),
                  ),

                  // Weather Advisory Alert
                  if (advisory != null && advisory.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withValues(alpha: isDark ? 0.2 : 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.umbrella_rounded, color: Color(0xFFF59E0B), size: 14),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              advisory,
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.bold,
                                color: isDark ? const Color(0xFFFCD34D) : const Color(0xFFB45309),
                              ),
                            ),
                          ),
                        ],
                      ),
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

  Widget _buildWeatherPill({
    required String title,
    required dynamic temp,
    required dynamic rainProb,
    required String cond,
    required bool isDark,
    required bool isDestination,
  }) {
    final rain = (rainProb as num?)?.toInt() ?? 0;
    final tVal = temp != null ? '$temp°C' : '--';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: isDestination
            ? const Color(0xFF3B82F6).withValues(alpha: isDark ? 0.25 : 0.12)
            : (isDark ? const Color(0xFF1E2130) : const Color(0xFFFFFFFF)),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isDestination
              ? const Color(0xFF3B82F6).withValues(alpha: 0.4)
              : (isDark ? const Color(0xFF2C2F42) : const Color(0xFFE2E8F0)),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              color: isDestination ? const Color(0xFF3B82F6) : Colors.grey,
            ),
          ),
          const SizedBox(height: 2),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '$tVal · $cond',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              ),
              if (rain > 15) ...[
                const SizedBox(width: 4),
                Text(
                  '($rain% 🌧️)',
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF3B82F6),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
