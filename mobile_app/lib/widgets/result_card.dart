import 'package:flutter/material.dart';
import '../theme.dart';

/// Rich Transit Result Card matching ResultCard in App.jsx
class ResultCard extends StatelessWidget {
  final String modeKey;
  final Map<String, dynamic> data;
  final bool isSelected;
  final VoidCallback onSelect;
  final Map<String, dynamic>? selectedCabVehicle;
  final ValueChanged<Map<String, dynamic>>? onSelectCabVehicle;
  final Map<String, dynamic>? selectedMultimodalOption;
  final ValueChanged<Map<String, dynamic>>? onSelectMultimodalOption;
  final VoidCallback? onSaveJourney;
  final VoidCallback? onNavigate;
  final VoidCallback? onViewTimeline;

  const ResultCard({
    super.key,
    required this.modeKey,
    required this.data,
    required this.isSelected,
    required this.onSelect,
    this.selectedCabVehicle,
    this.onSelectCabVehicle,
    this.selectedMultimodalOption,
    this.onSelectMultimodalOption,
    this.onSaveJourney,
    this.onNavigate,
    this.onViewTimeline,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = isSelected
        ? AppTheme.getModeColor(modeKey)
        : AppTheme.getBorder(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);
    final modeColor = AppTheme.getModeColor(modeKey);

    var time = data['time'] ?? 0;
    var cost = data['cost'] ?? 0;
    var distance = (data['distance'] as num?)?.toDouble() ?? 0.0;
    final transfers = data['transfers'] ?? 0;
    final emissions = (data['emissions'] as num?)?.toDouble() ?? 0.0;

    // Apply cab sub-selection override
    if (modeKey == 'cab' && selectedCabVehicle != null) {
      cost = selectedCabVehicle!['cost'] ?? cost;
      time = selectedCabVehicle!['time'] ?? time;
      distance = (selectedCabVehicle!['distance'] as num?)?.toDouble() ?? distance;
    }

    // Apply multimodal sub-selection override
    if (modeKey == 'multimodal' && selectedMultimodalOption != null) {
      cost = selectedMultimodalOption!['cost'] ?? cost;
      time = selectedMultimodalOption!['time'] ?? time;
      distance = (selectedMultimodalOption!['distance'] as num?)?.toDouble() ?? distance;
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: borderCol,
          width: isSelected ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: isSelected
                ? modeColor.withValues(alpha: isDark ? 0.25 : 0.12)
                : Colors.black.withValues(alpha: isDark ? 0.15 : 0.03),
            blurRadius: isSelected ? 12 : 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onSelect,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Header with Icon, Title, and Badges
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: modeColor.withValues(alpha: isDark ? 0.2 : 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: modeColor.withValues(alpha: 0.3)),
                      ),
                      child: Icon(
                        AppTheme.getModeIcon(modeKey),
                        color: modeColor,
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                AppTheme.getModeLabel(modeKey),
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                  color: textColor,
                                ),
                              ),
                              const SizedBox(width: 8),
                              if (isSelected)
                                PillBadge(
                                  text: 'SELECTED',
                                  color: modeColor,
                                  isSmall: true,
                                ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _getModeSubtitle(modeKey, data),
                            style: TextStyle(
                              fontSize: 11,
                              color: mutedColor,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Transfers badge
                    PillBadge(
                      text: transfers == 0 ? 'DIRECT' : '$transfers TRANSFERS',
                      color: transfers == 0 ? AppTheme.green : AppTheme.yellow,
                      isSmall: true,
                    ),
                  ],
                ),

                const SizedBox(height: 14),

                // 2. Metrics Bar (Time, Cost, Distance, Emissions)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMetricItem(
                        icon: Icons.access_time_rounded,
                        value: '$time min',
                        label: 'TRAVEL TIME',
                        color: modeColor,
                        textColor: textColor,
                        mutedColor: mutedColor,
                      ),
                      Container(width: 1, height: 28, color: AppTheme.getBorder(isDark)),
                      _buildMetricItem(
                        icon: Icons.currency_rupee_rounded,
                        value: cost == 0 ? 'FREE' : '₹$cost',
                        label: 'EST. FARE',
                        color: AppTheme.green,
                        textColor: textColor,
                        mutedColor: mutedColor,
                      ),
                      Container(width: 1, height: 28, color: AppTheme.getBorder(isDark)),
                      _buildMetricItem(
                        icon: Icons.directions_walk_rounded,
                        value: '$distance km',
                        label: 'DISTANCE',
                        color: AppTheme.blue,
                        textColor: textColor,
                        mutedColor: mutedColor,
                      ),
                      if (emissions > 0) ...[
                        Container(width: 1, height: 28, color: AppTheme.getBorder(isDark)),
                        _buildMetricItem(
                          icon: Icons.eco_rounded,
                          value: '${emissions.toInt()}g',
                          label: 'CO2',
                          color: AppTheme.green,
                          textColor: textColor,
                          mutedColor: mutedColor,
                        ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 14),

                // 3. Mode Specific Details
                if (modeKey == 'cab') ...[
                  _buildCabOptions(context, isDark, textColor, mutedColor),
                ] else if (modeKey == 'multimodal') ...[
                  _buildMultimodalOptions(context, isDark, textColor, mutedColor),
                ] else if (modeKey == 'bmtc') ...[
                  _buildBmtcDetails(isDark, textColor, mutedColor),
                ] else if (modeKey == 'metro') ...[
                  _buildMetroDetails(isDark, textColor, mutedColor),
                ] else if (modeKey == 'car') ...[
                  _buildCarDetails(isDark, textColor, mutedColor),
                ] else if (modeKey == 'bicycle' || modeKey == 'walk') ...[
                  _buildEcoDetails(isDark, textColor, mutedColor),
                ],

                const SizedBox(height: 14),

                // 4. Action Buttons (Timeline, Navigation, Save)
                Row(
                  children: [
                    if (onViewTimeline != null)
                      Expanded(
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: modeColor,
                            side: BorderSide(color: modeColor.withValues(alpha: 0.4)),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          onPressed: onViewTimeline,
                          icon: const Icon(Icons.linear_scale_rounded, size: 16),
                          label: const Text('Timeline', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    const SizedBox(width: 8),
                    if (onNavigate != null)
                      Expanded(
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: modeColor,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            elevation: 0,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          onPressed: onNavigate,
                          icon: const Icon(Icons.navigation_rounded, size: 16),
                          label: const Text('🚀 Start Nav', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900)),
                        ),
                      ),
                    const SizedBox(width: 8),
                    if (onSaveJourney != null)
                      IconButton.filledTonal(
                        style: IconButton.styleFrom(
                          backgroundColor: modeColor.withValues(alpha: 0.12),
                          foregroundColor: modeColor,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: onSaveJourney,
                        icon: const Icon(Icons.bookmark_add_outlined, size: 18),
                        tooltip: 'Save Route',
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetricItem({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
    required Color textColor,
    required Color mutedColor,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 3),
            Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w800,
                color: textColor,
              ),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w700,
            color: mutedColor,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }

  String _getModeSubtitle(String mode, Map<String, dynamic> d) {
    switch (mode) {
      case 'bmtc':
        final busNo = d['bus_number'] ?? d['route'] ?? 'Ordinary · Vajra AC';
        return 'Bus Route: $busNo';
      case 'metro':
        return 'Purple Line · Green Line · Yellow Line';
      case 'cab':
        return 'Namma Yatri · Ola · Uber · Rapido';
      case 'car':
        return 'Fuel + Estimated Parking';
      case 'multimodal':
        return d['route_summary'] ?? 'Bus + Metro + Auto combos';
      case 'bicycle':
        return 'Eco-friendly & healthy';
      case 'walk':
        return 'Healthy & 100% zero carbon';
      default:
        return '';
    }
  }

  // ── Cab multi-provider options ─────────────────────────────────────────────
  Widget _buildCabOptions(BuildContext context, bool isDark, Color textColor, Color mutedColor) {
    final estimates = data['all_estimates'] as List<dynamic>? ?? [];
    if (estimates.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'COMPARE CAB & AUTO PROVIDERS',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w800,
            color: mutedColor,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: estimates.map((est) {
            if (est is! Map<String, dynamic>) return const SizedBox.shrink();
            final name = est['name']?.toString() ?? est['provider']?.toString() ?? 'Cab';
            final c = est['cost'] ?? 0;
            final t = est['time'] ?? 0;
            final isCurrent = (selectedCabVehicle?['name'] == name ||
                selectedCabVehicle?['provider'] == name);

            return InkWell(
              onTap: () {
                if (onSelectCabVehicle != null) onSelectCabVehicle!(est);
              },
              borderRadius: BorderRadius.circular(10),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: isCurrent
                      ? AppTheme.cabColor.withValues(alpha: isDark ? 0.25 : 0.12)
                      : (isDark ? const Color(0xFF161822) : const Color(0xFFF1F5F9)),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isCurrent ? AppTheme.cabColor : AppTheme.getBorder(isDark),
                    width: isCurrent ? 1.5 : 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      name.toLowerCase().contains('auto')
                          ? Icons.electric_rickshaw_rounded
                          : (name.toLowerCase().contains('bike')
                              ? Icons.two_wheeler_rounded
                              : Icons.local_taxi_rounded),
                      size: 14,
                      color: isCurrent ? AppTheme.cabColor : mutedColor,
                    ),
                    const SizedBox(width: 6),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          name,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: isCurrent ? AppTheme.cabColor : textColor,
                          ),
                        ),
                        Text(
                          '₹$c · $t min',
                          style: TextStyle(
                            fontSize: 10,
                            color: isCurrent ? textColor : mutedColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ── Multimodal combo options ───────────────────────────────────────────────
  Widget _buildMultimodalOptions(BuildContext context, bool isDark, Color textColor, Color mutedColor) {
    final allOpts = data['all_options'] as List<dynamic>? ?? [];
    if (allOpts.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'MULTIMODAL TRANSIT COMBINATIONS',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w800,
            color: mutedColor,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 8),
        Column(
          children: allOpts.map((opt) {
            if (opt is! Map<String, dynamic>) return const SizedBox.shrink();
            final summary = opt['route_summary']?.toString() ?? 'Transit Option';
            final c = opt['cost'] ?? 0;
            final t = opt['time'] ?? 0;
            final tr = opt['transfers'] ?? 0;
            final isCurrent = selectedMultimodalOption?['route_summary'] == summary;

            return InkWell(
              onTap: () {
                if (onSelectMultimodalOption != null) onSelectMultimodalOption!(opt);
              },
              borderRadius: BorderRadius.circular(10),
              child: Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: isCurrent
                      ? AppTheme.multimodalColor.withValues(alpha: isDark ? 0.25 : 0.12)
                      : (isDark ? const Color(0xFF161822) : const Color(0xFFF1F5F9)),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isCurrent ? AppTheme.multimodalColor : AppTheme.getBorder(isDark),
                    width: isCurrent ? 1.5 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      isCurrent ? Icons.radio_button_checked : Icons.radio_button_off,
                      size: 16,
                      color: isCurrent ? AppTheme.multimodalColor : mutedColor,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        summary,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: isCurrent ? AppTheme.multimodalColor : textColor,
                        ),
                      ),
                    ),
                    Text(
                      '₹$c · $t min ($tr trans)',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: isCurrent ? textColor : mutedColor,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ── BMTC Bus details ───────────────────────────────────────────────────────
  Widget _buildBmtcDetails(bool isDark, Color textColor, Color mutedColor) {
    final wait = data['waiting_time'] ?? 5;
    final freq = data['frequency'] ?? 'Every 10-15 mins';
    final isVajra = (data['route']?.toString().toUpperCase().startsWith('V-') ?? false) ||
        (data['route']?.toString().toUpperCase().startsWith('KIA') ?? false);

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              PillBadge(
                text: isVajra ? 'VAJRA AC' : 'ORDINARY',
                color: isVajra ? AppTheme.blue : AppTheme.bmtcColor,
                isSmall: true,
              ),
              const SizedBox(width: 8),
              Text(
                'Wait: ~$wait min',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor),
              ),
            ],
          ),
          Text(
            freq.toString(),
            style: TextStyle(fontSize: 11, color: mutedColor),
          ),
        ],
      ),
    );
  }

  // ── Metro details ──────────────────────────────────────────────────────────
  Widget _buildMetroDetails(bool isDark, Color textColor, Color mutedColor) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const PillBadge(text: 'PURPLE / GREEN', color: AppTheme.metroColor, isSmall: true),
              const SizedBox(width: 8),
              Text(
                'Platform Interchanges Active',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor),
              ),
            ],
          ),
          Text(
            'Every 5-8 min',
            style: TextStyle(fontSize: 11, color: mutedColor),
          ),
        ],
      ),
    );
  }

  // ── Car details ────────────────────────────────────────────────────────────
  Widget _buildCarDetails(bool isDark, Color textColor, Color mutedColor) {
    final fuel = data['fuel_cost'] ?? ((data['cost'] ?? 100) * 0.7).toInt();
    final parking = data['parking_cost'] ?? 30;

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            'Estimated Fuel: ₹$fuel',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor),
          ),
          Text(
            'Parking: ~₹$parking',
            style: TextStyle(fontSize: 11, color: mutedColor),
          ),
        ],
      ),
    );
  }

  // ── Eco (Bicycle & Walk) details ───────────────────────────────────────────
  Widget _buildEcoDetails(bool isDark, Color textColor, Color mutedColor) {
    final calories = ((data['distance'] ?? 2.0) * 45).toInt();

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.local_fire_department_rounded, size: 14, color: AppTheme.red),
              const SizedBox(width: 4),
              Text(
                '~$calories kcal burned',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor),
              ),
            ],
          ),
          const PillBadge(text: '100% ZERO CARBON', color: AppTheme.green, isSmall: true),
        ],
      ),
    );
  }
}
