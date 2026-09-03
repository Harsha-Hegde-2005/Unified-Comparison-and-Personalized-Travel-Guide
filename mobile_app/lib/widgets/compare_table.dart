import 'package:flutter/material.dart';
import '../theme.dart';

/// Side-by-side mode comparison matrix table matching CompareTable in App.jsx
class CompareTable extends StatelessWidget {
  final Map<String, dynamic> results;
  final String? selectedMode;
  final ValueChanged<String>? onSelectMode;

  const CompareTable({
    super.key,
    required this.results,
    this.selectedMode,
    this.onSelectMode,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = AppTheme.getBorder(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final List<Map<String, dynamic>> rows = [];
    final modes = ['bmtc', 'metro', 'cab', 'namma_yatri', 'uber', 'ola', 'rapido', 'car', 'multimodal', 'bicycle', 'walk'];
    for (final k in results.keys) {
      if (!modes.contains(k) && results[k]?['available'] == true) {
        modes.add(k);
      }
    }

    for (final m in modes) {
      final data = results[m] as Map<String, dynamic>?;
      if (data == null || data['available'] != true) continue;

      var cost = data['cost'] ?? 0;
      var time = data['time'] ?? 0;
      var dist = (data['distance'] as num?)?.toDouble() ?? 0.0;
      var transfers = data['transfers'] ?? 0;
      var emissions = (data['emissions'] as num?)?.toDouble() ?? 0.0;

      // Extract specific provider / option details if available
      if ((m == 'cab' || m == 'namma_yatri' || m == 'uber' || m == 'ola' || m == 'rapido') &&
          data['all_estimates'] is List &&
          (data['all_estimates'] as List).isNotEmpty) {
        final firstEst = (data['all_estimates'] as List).first as Map<String, dynamic>;
        cost = firstEst['cost'] ?? cost;
        time = firstEst['time'] ?? time;
      }
      if (m == 'multimodal' && data['all_options'] is List && (data['all_options'] as List).isNotEmpty) {
        final firstOpt = (data['all_options'] as List).first as Map<String, dynamic>;
        cost = firstOpt['cost'] ?? cost;
        time = firstOpt['time'] ?? time;
        transfers = firstOpt['transfers'] ?? transfers;
      }

      String comfort = '⭐⭐⭐';
      if (m == 'cab' || m == 'car' || m == 'namma_yatri' || m == 'uber' || m == 'ola' || m == 'rapido') {
        comfort = '⭐⭐⭐⭐⭐';
      } else if (m == 'metro') {
        comfort = '⭐⭐⭐⭐';
      } else if (m == 'bicycle' || m == 'walk') {
        comfort = '⭐⭐';
      }

      rows.add({
        'key': m,
        'label': AppTheme.getModeLabel(m),
        'color': AppTheme.getModeColor(m),
        'icon': AppTheme.getModeIcon(m),
        'cost': cost,
        'time': time,
        'dist': dist,
        'transfers': transfers,
        'comfort': comfort,
        'emissions': emissions,
      });
    }

    if (rows.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderCol),
        ),
        child: Center(
          child: Text('No comparison data available.', style: TextStyle(color: mutedColor)),
        ),
      );
    }

    // Find fastest and cheapest
    int minCost = 999999;
    int minTime = 999999;
    for (final r in rows) {
      final c = r['cost'] as int;
      final t = r['time'] as int;
      if (c > 0 && c < minCost) minCost = c;
      if (t > 0 && t < minTime) minTime = t;
    }

    return Container(
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
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.table_chart_rounded, size: 16, color: Color(0xFF7C5CFF)),
                    const SizedBox(width: 8),
                    Text(
                      'TRANSIT COMPARISON MATRIX',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: mutedColor,
                        letterSpacing: 0.6,
                      ),
                    ),
                  ],
                ),
                Text(
                  '${rows.length} Modes Compared',
                  style: TextStyle(fontSize: 11, color: mutedColor, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            child: DataTable(
              columnSpacing: 22,
              horizontalMargin: 16,
              headingRowHeight: 40,
              dataRowMinHeight: 48,
              dataRowMaxHeight: 56,
              headingTextStyle: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: mutedColor,
              ),
              columns: const [
                DataColumn(label: Text('MODE')),
                DataColumn(label: Text('TIME')),
                DataColumn(label: Text('COST')),
                DataColumn(label: Text('WALK / DIST')),
                DataColumn(label: Text('TRANSFERS')),
                DataColumn(label: Text('COMFORT')),
                DataColumn(label: Text('ACTION')),
              ],
              rows: rows.map((r) {
                final modeKey = r['key'] as String;
                final isSelected = selectedMode == modeKey;
                final color = r['color'] as Color;
                final isCheapest = r['cost'] == minCost && minCost < 999999;
                final isFastest = r['time'] == minTime && minTime < 999999;

                return DataRow(
                  selected: isSelected,
                  onSelectChanged: (_) {
                    if (onSelectMode != null) onSelectMode!(modeKey);
                  },
                  cells: [
                    // Mode
                    DataCell(
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(r['icon'] as IconData, size: 16, color: color),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            r['label'] as String,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: textColor,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Time
                    DataCell(
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${r['time']} min',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: isFastest ? FontWeight.w800 : FontWeight.w600,
                              color: isFastest ? AppTheme.green : textColor,
                            ),
                          ),
                          if (isFastest) ...[
                            const SizedBox(width: 4),
                            const PillBadge(text: 'FASTEST', color: AppTheme.green, isSmall: true),
                          ],
                        ],
                      ),
                    ),

                    // Cost
                    DataCell(
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            r['cost'] == 0 ? 'FREE' : '₹${r['cost']}',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: isCheapest ? FontWeight.w800 : FontWeight.w600,
                              color: isCheapest ? AppTheme.green : textColor,
                            ),
                          ),
                          if (isCheapest && r['cost'] != 0) ...[
                            const SizedBox(width: 4),
                            const PillBadge(text: 'CHEAPEST', color: AppTheme.green, isSmall: true),
                          ],
                        ],
                      ),
                    ),

                    // Walk / Dist
                    DataCell(
                      Text(
                        '${r['dist']} km',
                        style: TextStyle(fontSize: 12, color: mutedColor),
                      ),
                    ),

                    // Transfers
                    DataCell(
                      Text(
                        r['transfers'] == 0 ? 'Direct' : '${r['transfers']} transfer(s)',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: r['transfers'] == 0 ? AppTheme.green : mutedColor,
                        ),
                      ),
                    ),

                    // Comfort
                    DataCell(
                      Text(
                        r['comfort'] as String,
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),

                    // Action
                    DataCell(
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isSelected ? color : color.withValues(alpha: 0.12),
                          foregroundColor: isSelected ? Colors.white : color,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          minimumSize: const Size(60, 28),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: BorderSide(color: color.withValues(alpha: 0.3)),
                          ),
                        ),
                        onPressed: () {
                          if (onSelectMode != null) onSelectMode!(modeKey);
                        },
                        child: Text(
                          isSelected ? 'Selected' : 'Select',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
                        ),
                      ),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
