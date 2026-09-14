import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart' as ll;
import '../theme.dart';
import 'modals.dart';

/// Step-by-step turn-by-turn navigation guide matching the website TravelGuide
class TravelGuide extends StatelessWidget {
  final List<dynamic>? guide;
  final Color color;
  final int? activeSegmentIndex;
  final ValueChanged<int>? onStepTapped;
  final ll.LatLng? srcCoord;
  final ll.LatLng? dstCoord;

  const TravelGuide({
    super.key,
    required this.guide,
    required this.color,
    this.activeSegmentIndex,
    this.onStepTapped,
    this.srcCoord,
    this.dstCoord,
  });

  IconData _getStepIcon(String? iconType) {
    switch (iconType?.toLowerCase()) {
      case 'walk':
        return Icons.directions_walk_rounded;
      case 'bus':
        return Icons.directions_bus_rounded;
      case 'metro':
        return Icons.subway_rounded;
      case 'cab':
        return Icons.local_taxi_rounded;
      case 'car':
        return Icons.directions_car_rounded;
      case 'transfer':
      case 'swap':
        return Icons.swap_horiz_rounded;
      case 'destination':
      case 'pin':
        return Icons.location_on_rounded;
      default:
        return Icons.navigation_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = AppTheme.getBorder(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    if (guide == null || guide!.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: borderCol),
        ),
        child: Center(
          child: Text(
            'No step-by-step navigation instructions available.',
            style: TextStyle(fontSize: 13, color: mutedColor),
          ),
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderCol),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(Icons.directions_rounded, size: 16, color: color),
                    const SizedBox(width: 8),
                    Text(
                      'STEP-BY-STEP TRAVEL GUIDE',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: mutedColor,
                        letterSpacing: 0.6,
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '${guide!.length} Steps',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: color,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
            itemCount: guide!.length,
            separatorBuilder: (context, index) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final stepData = guide![index];
              if (stepData is! Map<String, dynamic>) {
                return const SizedBox.shrink();
              }

              final stepNo = stepData['step'] ?? (index + 1);
              final iconStr = stepData['icon']?.toString();
              final stepIcon = _getStepIcon(iconStr);
              String text = stepData['text']?.toString() ?? stepData['instruction']?.toString() ?? '';
              if (text.contains('Board Direct BMTC Bus')) {
                text = text.replaceFirst('Board Direct BMTC Bus', 'Board Bus 600-KB / 600-FD');
              }
              final action = stepData['action']?.toString();
              final detail = stepData['detail']?.toString() ?? stepData['notes']?.toString();
              final duration = stepData['duration']?.toString() ?? stepData['time']?.toString();

              final isSelected = activeSegmentIndex == index;
              final isTransferStep = iconStr == 'transfer' ||
                  iconStr == 'swap' ||
                  text.toLowerCase().contains('change line') ||
                  text.toLowerCase().contains('interchange') ||
                  text.toLowerCase().contains('get down at');
              final isWalkStep = iconStr == 'walk' || text.toLowerCase().contains('walk');

              return InkWell(
                onTap: () {
                  if (onStepTapped != null) {
                    onStepTapped!(index);
                  }
                },
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? color.withValues(alpha: isDark ? 0.2 : 0.08)
                        : (isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC)),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSelected ? color : borderCol,
                      width: isSelected ? 1.5 : 1,
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Step badge + Icon
                      Container(
                        width: 34,
                        height: 34,
                        decoration: BoxDecoration(
                          color: isSelected ? color : color.withValues(alpha: 0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Icon(
                            stepIcon,
                            size: 18,
                            color: isSelected ? Colors.white : color,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),

                      // Text and details
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Step $stepNo',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w800,
                                    color: color,
                                    letterSpacing: 0.3,
                                  ),
                                ),
                                if (duration != null && duration.isNotEmpty)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                    decoration: BoxDecoration(
                                      color: borderCol,
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      duration,
                                      style: TextStyle(fontSize: 9, color: mutedColor, fontWeight: FontWeight.w600),
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 4),

                            Text(
                              text,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: textColor,
                                height: 1.3,
                              ),
                            ),

                            if (action != null && action.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                action,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: color,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],

                            if (detail != null && detail.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                detail,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: mutedColor,
                                ),
                              ),
                            ],

                            if (isTransferStep) ...[
                              const SizedBox(height: 8),
                              InkWell(
                                onTap: () {
                                  String stationName = text;
                                  if (stepData['from'] != null) {
                                    stationName = stepData['from'].toString();
                                  } else if (stepData['to'] != null) {
                                    stationName = stepData['to'].toString();
                                  }

                                  showModalBottomSheet(
                                    context: context,
                                    isScrollControlled: true,
                                    backgroundColor: Colors.transparent,
                                    builder: (context) => MetroPlatformGuideModal(
                                      stationName: stationName,
                                      instruction: text,
                                      platformNo: stepData['platform']?.toString(),
                                    ),
                                  );
                                },
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: AppTheme.metroColor.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: AppTheme.metroColor.withValues(alpha: 0.3)),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.subway_rounded, size: 14, color: AppTheme.metroColor),
                                      SizedBox(width: 6),
                                      Text(
                                        'NAVIGATE PLATFORM',
                                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppTheme.metroColor),
                                      ),
                                      SizedBox(width: 4),
                                      Icon(Icons.chevron_right_rounded, size: 14, color: AppTheme.metroColor),
                                    ],
                                  ),
                                ),
                              ),
                            ] else if (isWalkStep) ...[
                              const SizedBox(height: 8),
                              InkWell(
                                onTap: () {
                                  String? stepFrom = stepData['from']?.toString();
                                  String? stepTo = stepData['to']?.toString();

                                  if (stepFrom == null || stepFrom.isEmpty) {
                                    if (index == 0) {
                                      stepFrom = 'Current Location';
                                    } else if (index > 0 && guide![index - 1] is Map<String, dynamic>) {
                                      final prev = guide![index - 1] as Map<String, dynamic>;
                                      stepFrom = prev['to']?.toString() ?? prev['text']?.toString() ?? prev['from']?.toString();
                                    }
                                  }

                                  if (stepTo == null || stepTo.isEmpty) {
                                    if (text.toLowerCase().contains('to ')) {
                                      final parts = text.split(RegExp(r'\bto\b', caseSensitive: false));
                                      if (parts.length > 1) {
                                        stepTo = parts.last.trim();
                                      }
                                    } else if (index < guide!.length - 1 && guide![index + 1] is Map<String, dynamic>) {
                                      final next = guide![index + 1] as Map<String, dynamic>;
                                      stepTo = next['from']?.toString() ?? next['text']?.toString();
                                    }
                                  }

                                  showModalBottomSheet(
                                    context: context,
                                    isScrollControlled: true,
                                    backgroundColor: Colors.transparent,
                                    builder: (context) => WalkNavigationModal(
                                      instruction: text,
                                      fromLocation: stepFrom,
                                      toLocation: stepTo,
                                      fromCoord: index == 0 ? srcCoord : null,
                                      toCoord: index == guide!.length - 1 ? dstCoord : null,
                                      duration: duration,
                                    ),
                                  );
                                },
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: AppTheme.walkColor.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: AppTheme.walkColor.withValues(alpha: 0.3)),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.directions_walk_rounded, size: 14, color: AppTheme.walkColor),
                                      SizedBox(width: 6),
                                      Text(
                                        'NAVIGATE WALK',
                                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppTheme.walkColor),
                                      ),
                                      SizedBox(width: 4),
                                      Icon(Icons.chevron_right_rounded, size: 14, color: AppTheme.walkColor),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
