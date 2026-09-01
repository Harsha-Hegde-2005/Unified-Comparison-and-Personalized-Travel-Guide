import 'package:flutter/material.dart';
import '../theme.dart';

/// Linear station timeline component matching the website's LinearRouteMap (---o---o---)
class LinearRouteMap extends StatelessWidget {
  final List<dynamic>? segments;
  final String? activeMode;

  const LinearRouteMap({
    super.key,
    required this.segments,
    this.activeMode,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = AppTheme.getBorder(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    if (segments == null || segments!.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: borderCol),
        ),
        child: Center(
          child: Text(
            'Select a route option to view the station timeline',
            style: TextStyle(fontSize: 13, color: mutedColor),
          ),
        ),
      );
    }

    final List<Color> segmentColors = [
      const Color(0xFFF97316),
      const Color(0xFF3B82F6),
      const Color(0xFFEC4899),
      const Color(0xFF14B8A6),
      const Color(0xFFEAB308),
      const Color(0xFFEF4444),
    ];

    // Collect all stops from all segments in order
    final List<_TimelineStop> stopsList = [];
    int transitSegmentIdx = 0;

    for (int idx = 0; idx < segments!.length; idx++) {
      final seg = segments![idx];
      if (seg is! Map<String, dynamic>) continue;

      final type = seg['type']?.toString().toLowerCase() ?? '';
      final routeName = seg['route']?.toString() ?? '';
      final isWalk = type == 'walk' || routeName.toLowerCase().contains('walk');
      final isMetro = type == 'metro';

      Color color;
      if (isMetro) {
        final rLow = routeName.toLowerCase();
        if (rLow.contains('green')) {
          color = const Color(0xFF22C55E);
        } else if (rLow.contains('purple')) {
          color = const Color(0xFF8B5CF6);
        } else if (rLow.contains('yellow')) {
          color = const Color(0xFFEAB308);
        } else {
          color = const Color(0xFF8B5CF6);
        }
      } else if (isWalk) {
        color = const Color(0xFF6B7A99);
      } else {
        color = segmentColors[transitSegmentIdx % segmentColors.length];
        transitSegmentIdx++;
      }

      final rawStops = seg['stops'] as List<dynamic>? ?? [];
      final List<String> segStops = [];
      if (rawStops.isNotEmpty) {
        for (final s in rawStops) {
          segStops.add(s.toString());
        }
      } else {
        final from = seg['from']?.toString();
        final to = seg['to']?.toString();
        if (from != null && to != null) {
          segStops.addAll([from, to]);
        }
      }

      for (int sIdx = 0; sIdx < segStops.length; sIdx++) {
        final stopName = segStops[sIdx];
        if (stopsList.isNotEmpty && stopsList.last.name == stopName) {
          stopsList.last.isTransfer = true;
          stopsList.last.nextColor = color;
          stopsList.last.nextRoute = routeName.isNotEmpty ? routeName : 'Walk';
          continue;
        }

        stopsList.add(_TimelineStop(
          name: stopName,
          color: color,
          route: routeName.isNotEmpty ? routeName : (isWalk ? 'Walk' : 'Transit'),
          isFirst: stopsList.isEmpty,
          isLast: false,
          isTransfer: sIdx == 0 && stopsList.isNotEmpty,
          isWalk: isWalk,
        ));
      }
    }

    if (stopsList.isNotEmpty) {
      stopsList.last.isLast = true;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderCol),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
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
                  const Icon(Icons.linear_scale_rounded, size: 16, color: Color(0xFF7C5CFF)),
                  const SizedBox(width: 6),
                  Text(
                    'LINEAR STATION TIMELINE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: mutedColor,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppTheme.getAccent(isDark).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '${stopsList.length} stops',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.getAccent(isDark),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Horizontal scrollable track
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: stopsList.map((stop) {
                final isEndpoint = stop.isFirst || stop.isLast;
                final lineColor = stop.nextColor ?? stop.color;
                final routeLabel = stop.nextRoute ?? stop.route;

                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Node with label above and below
                    SizedBox(
                      width: 100,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Station name above
                          SizedBox(
                            height: 32,
                            child: Text(
                              stop.name,
                              textAlign: TextAlign.center,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: isEndpoint || stop.isTransfer ? 11 : 10,
                                fontWeight: isEndpoint || stop.isTransfer
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                color: isEndpoint || stop.isTransfer ? textColor : mutedColor,
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),

                          // Node Circle
                          Container(
                            width: isEndpoint ? 18 : (stop.isTransfer ? 16 : 12),
                            height: isEndpoint ? 18 : (stop.isTransfer ? 16 : 12),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: isEndpoint
                                  ? stop.color
                                  : (stop.isTransfer ? cardBg : stop.color),
                              border: Border.all(
                                color: stop.color,
                                width: isEndpoint ? 3 : 2.5,
                              ),
                              boxShadow: isEndpoint
                                  ? [
                                      BoxShadow(
                                        color: stop.color.withValues(alpha: 0.4),
                                        blurRadius: 6,
                                        spreadRadius: 2,
                                      ),
                                    ]
                                  : null,
                            ),
                            child: isEndpoint
                                ? Center(
                                    child: Container(
                                      width: 4,
                                      height: 4,
                                      decoration: const BoxDecoration(
                                        color: Colors.white,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                  )
                                : null,
                          ),
                          const SizedBox(height: 6),

                          // Subtitle tag below node
                          Text(
                            stop.isFirst
                                ? 'START'
                                : (stop.isLast
                                    ? 'DESTINATION'
                                    : (stop.isTransfer ? 'TRANSFER' : 'STOP')),
                            style: TextStyle(
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                              color: stop.color,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Connecting line between nodes
                    if (!stop.isLast)
                      Container(
                        width: 54,
                        alignment: Alignment.center,
                        child: Stack(
                          clipBehavior: Clip.none,
                          alignment: Alignment.center,
                          children: [
                            Container(
                              height: stop.isWalk ? 2 : 4,
                              decoration: BoxDecoration(
                                color: lineColor,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                            Positioned(
                              top: -16,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 5,
                                  vertical: 1,
                                ),
                                decoration: BoxDecoration(
                                  color: cardBg,
                                  border: Border.all(
                                    color: lineColor.withValues(alpha: 0.5),
                                    width: 1,
                                  ),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  routeLabel,
                                  style: TextStyle(
                                    fontSize: 8.5,
                                    fontWeight: FontWeight.w800,
                                    color: lineColor,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                );
              }).toList(),
            ),
          ),

          Center(
            child: Text(
              '↔ Scroll horizontally to view all intermediate stops',
              style: TextStyle(fontSize: 10, color: mutedColor),
            ),
          ),
        ],
      ),
    );
  }
}

class _TimelineStop {
  final String name;
  final Color color;
  final String route;
  final bool isFirst;
  bool isLast;
  bool isTransfer;
  final bool isWalk;
  Color? nextColor;
  String? nextRoute;

  _TimelineStop({
    required this.name,
    required this.color,
    required this.route,
    required this.isFirst,
    required this.isLast,
    required this.isTransfer,
    required this.isWalk,
  });
}
