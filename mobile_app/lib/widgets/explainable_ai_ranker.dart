import 'package:flutter/material.dart';
import '../theme.dart';

/// U-Transit AI Smart Ranker & Explainable AI (XAI) Component
/// Mirrors App.jsx lines 8280-8485:
/// - Rank badges (#1, #2, #3, #4)
/// - Match % badges (e.g. 95% MATCH)
/// - Cost, Time, Transfers, and CO2 emissions
/// - Dynamic Gemini-powered "Why recommended" explanation
/// - Transparency data source tags (Traffic, Weather, BMTC, Tariff, OSRM)
/// - Expandable cab provider breakdowns (Namma Yatri, Ola, Uber, Rapido)
/// - Interactive mode selection
class ExplainableAiRankerCard extends StatefulWidget {
  final List<dynamic> recommendations;
  final Map<String, dynamic> results;
  final String? selectedMode;
  final ValueChanged<String> onSelectMode;

  const ExplainableAiRankerCard({
    super.key,
    required this.recommendations,
    required this.results,
    required this.selectedMode,
    required this.onSelectMode,
  });

  @override
  State<ExplainableAiRankerCard> createState() => _ExplainableAiRankerCardState();
}

class _ExplainableAiRankerCardState extends State<ExplainableAiRankerCard> {
  int? _expandedIndex;

  @override
  Widget build(BuildContext context) {
    if (widget.recommendations.isEmpty) return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? const Color(0xFF6D28D9).withValues(alpha: 0.3) : const Color(0xFFEDE9FE),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF7C3AED).withValues(alpha: isDark ? 0.25 : 0.08),
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Header with Gemini badge
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(10),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF7C3AED).withValues(alpha: 0.35),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: const Center(
                      child: Text('🤖', style: TextStyle(fontSize: 18)),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'U-Transit AI Smart Ranker',
                        style: TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 15,
                          color: textColor,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'EXPLAINABLE AI & TOP-K ROUTING',
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.w800,
                          color: isDark ? const Color(0xFFA78BFA) : const Color(0xFF7C3AED),
                          letterSpacing: 0.6,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF7C3AED).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.3),
                    width: 1,
                  ),
                ),
                child: const Text(
                  '✨ Gemini Powered',
                  style: TextStyle(
                    color: Color(0xFF7C3AED),
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 2. Top-K Recommendations List (up to 4)
          ...widget.recommendations.take(4).toList().asMap().entries.map((entry) {
            final idx = entry.key;
            final rec = entry.value as Map<String, dynamic>;
            final mode = rec['mode']?.toString() ?? 'bmtc';
            final score = rec['score'] ?? 90;
            final isSelected = widget.selectedMode == mode;
            final isExpanded = _expandedIndex == idx;

            // Mode config
            final modeColor = AppTheme.getModeColor(mode);
            final modeIcon = AppTheme.getModeIcon(mode);
            final modeLabel = AppTheme.getModeLabel(mode);

            // Fetch actual journey data from results
            final actualData = widget.results[mode] as Map<String, dynamic>? ?? {};
            final cost = actualData['cost'] ?? rec['cost'] ?? 0;
            final time = actualData['time'] ?? rec['time'] ?? 0;
            final transfers = actualData['transfers'] ?? rec['transfers'] ?? 0;
            final emissions = (rec['emissions'] as num?)?.toDouble() ??
                (actualData['emissions'] as num?)?.toDouble() ??
                0.0;
            final explanation = rec['explanation']?.toString() ??
                'Optimal trade-off for current Bengaluru traffic conditions.';
            final dataSources = rec['data_sources'] as Map<String, dynamic>?;

            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              decoration: BoxDecoration(
                color: isSelected
                    ? (isDark ? const Color(0xFF1E1B4B) : const Color(0xFFF5F3FF))
                    : (isDark ? const Color(0xFF161822) : const Color(0xFFFAFAFD)),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isSelected
                      ? const Color(0xFF7C3AED)
                      : (isDark ? const Color(0xFF2D3142) : const Color(0xFFEEF0F6)),
                  width: isSelected ? 1.8 : 1.0,
                ),
                boxShadow: isSelected
                    ? [
                        BoxShadow(
                          color: const Color(0xFF7C3AED).withValues(alpha: 0.15),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ]
                    : null,
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () => widget.onSelectMode(mode),
                  borderRadius: BorderRadius.circular(16),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Main row
                        Row(
                          children: [
                            // Rank Badge (#1, #2, #3, #4)
                            Container(
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: idx == 0
                                    ? const LinearGradient(
                                        colors: [Color(0xFFFEF08A), Color(0xFFFDE047)],
                                        begin: Alignment.topLeft,
                                        end: Alignment.bottomRight,
                                      )
                                    : null,
                                color: idx != 0
                                    ? (isDark ? const Color(0xFF272A38) : const Color(0xFFF3F4F6))
                                    : null,
                                border: Border.all(
                                  color: idx == 0
                                      ? const Color(0xFFEAB308)
                                      : (isDark ? const Color(0xFF3F445B) : const Color(0xFFE5E7EB)),
                                  width: 1,
                                ),
                              ),
                              child: Center(
                                child: Text(
                                  '#${idx + 1}',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w900,
                                    fontSize: 12,
                                    color: idx == 0
                                        ? const Color(0xFF854D0E)
                                        : (isDark ? Colors.white70 : const Color(0xFF4B5563)),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),

                            // Mode Icon Container
                            Container(
                              width: 38,
                              height: 38,
                              decoration: BoxDecoration(
                                color: modeColor.withValues(alpha: isDark ? 0.25 : 0.12),
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: modeColor.withValues(alpha: 0.3)),
                              ),
                              child: Icon(modeIcon, size: 20, color: modeColor),
                            ),
                            const SizedBox(width: 10),

                            // Mode Label & Match Badge
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(
                                        modeLabel,
                                        style: TextStyle(
                                          fontWeight: FontWeight.w900,
                                          fontSize: 14,
                                          color: textColor,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: modeColor.withValues(alpha: 0.15),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          '$score% MATCH',
                                          style: TextStyle(
                                            color: modeColor,
                                            fontSize: 9,
                                            fontWeight: FontWeight.w900,
                                            letterSpacing: 0.3,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),

                                  // Quick Metrics: Cost, Time, Transfers, Emissions
                                  Row(
                                    children: [
                                      Text('💰 ₹$cost', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                                      const SizedBox(width: 8),
                                      Text('🕒 $time min', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: mutedColor)),
                                      const SizedBox(width: 8),
                                      Text('🎯 $transfers xfer', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: mutedColor)),
                                      if (emissions > 0) ...[
                                        const SizedBox(width: 8),
                                        Text('🌿 ${emissions.toInt()}g', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.green)),
                                      ],
                                    ],
                                  ),
                                ],
                              ),
                            ),

                            // Expand details button
                            InkWell(
                              onTap: () {
                                setState(() {
                                  _expandedIndex = isExpanded ? null : idx;
                                });
                              },
                              borderRadius: BorderRadius.circular(8),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                                child: Icon(
                                  isExpanded ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                                  color: mutedColor,
                                  size: 20,
                                ),
                              ),
                            ),

                            // Radio circle
                            Container(
                              width: 22,
                              height: 22,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isSelected ? const Color(0xFF7C3AED) : Colors.transparent,
                                border: Border.all(
                                  color: isSelected
                                      ? const Color(0xFF7C3AED)
                                      : (isDark ? Colors.white38 : Colors.grey.shade400),
                                  width: 2,
                                ),
                              ),
                              child: isSelected
                                  ? const Icon(Icons.check_rounded, size: 14, color: Colors.white)
                                  : null,
                            ),
                          ],
                        ),

                        // 3. Why recommended (Always visible or expanded)
                        Container(
                          margin: const EdgeInsets.only(top: 10),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: isDark ? const Color(0xFF1E2130) : Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border(
                              left: BorderSide(color: modeColor, width: 3.5),
                              top: BorderSide(color: isDark ? const Color(0xFF2E3348) : const Color(0xFFF1F1F5)),
                              right: BorderSide(color: isDark ? const Color(0xFF2E3348) : const Color(0xFFF1F1F5)),
                              bottom: BorderSide(color: isDark ? const Color(0xFF2E3348) : const Color(0xFFF1F1F5)),
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              RichText(
                                text: TextSpan(
                                  style: TextStyle(fontSize: 11.5, color: isDark ? Colors.white70 : const Color(0xFF4B5563), height: 1.3),
                                  children: [
                                    const TextSpan(
                                      text: 'Why recommended: ',
                                      style: TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                    TextSpan(text: explanation),
                                  ],
                                ),
                              ),

                              // Data source transparency tags
                              if (dataSources != null || isExpanded) ...[
                                const SizedBox(height: 6),
                                Divider(height: 1, color: isDark ? Colors.white10 : Colors.black12),
                                const SizedBox(height: 6),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 4,
                                  children: [
                                    Text('📊 Sources:', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: mutedColor)),
                                    if (dataSources?['traffic'] != null)
                                      Text('🚦 ${dataSources!['traffic']}', style: TextStyle(fontSize: 9.5, color: mutedColor)),
                                    if (dataSources?['weather'] != null)
                                      Text('🌧️ ${dataSources!['weather']}', style: TextStyle(fontSize: 9.5, color: mutedColor)),
                                    if (dataSources?['bmtc'] != null)
                                      Text('🚌 ${dataSources!['bmtc']}', style: TextStyle(fontSize: 9.5, color: mutedColor)),
                                    if (dataSources?['fare'] != null)
                                      Text('🚕 ${dataSources!['fare']}', style: TextStyle(fontSize: 9.5, color: mutedColor)),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),

                        // 4. If expanded & cab mode: show available cab providers
                        if (isExpanded && mode == 'cab' && actualData['all_estimates'] is List) ...[
                          const SizedBox(height: 10),
                          Text(
                            'AVAILABLE CAB & AUTO PROVIDERS',
                            style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: (actualData['all_estimates'] as List<dynamic>).take(5).map((est) {
                              if (est is! Map) return const SizedBox.shrink();
                              final p = est['provider']?.toString() ?? 'Cab';
                              final c = est['cost'] ?? 0;
                              final t = est['time'] ?? 0;
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: isDark ? const Color(0xFF242738) : const Color(0xFFF1F5F9),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: AppTheme.getBorder(isDark)),
                                ),
                                child: Text(
                                  '$p: ₹$c · $t min',
                                  style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: textColor),
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
