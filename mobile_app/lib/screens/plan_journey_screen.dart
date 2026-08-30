import 'dart:async';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart' as ll;
import '../services/api_service.dart';
import 'route_details_screen.dart';

class PlanJourneyScreen extends StatefulWidget {
  const PlanJourneyScreen({super.key});

  @override
  State<PlanJourneyScreen> createState() => _PlanJourneyScreenState();
}

class _PlanJourneyScreenState extends State<PlanJourneyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _sourceController = TextEditingController(text: 'Majestic');
  final _destController = TextEditingController(text: 'Indiranagar');
  final _timeController = TextEditingController();

  String _preference = 'cost';
  bool _isLoading = false;
  Map<String, dynamic>? _results;
  String? _errorMessage;

  ll.LatLng? _srcCoord;
  ll.LatLng? _dstCoord;

  final FocusNode _sourceFocusNode = FocusNode();
  final FocusNode _destFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    // Default time is "Now"
    final now = DateTime.now();
    _timeController.text = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";

    // Auto-resolve Majestic and Indiranagar coordinates on start
    _resolveAndPin('Majestic', true);
    _resolveAndPin('Indiranagar', false);
  }

  @override
  void dispose() {
    _sourceFocusNode.dispose();
    _destFocusNode.dispose();
    _sourceController.dispose();
    _destController.dispose();
    _timeController.dispose();
    super.dispose();
  }

  Future<void> _resolveAndPin(String input, bool isSource) async {
    final query = input.trim();
    if (query.isEmpty) return;

    final autocompleteRes = await ApiService.placesAutocomplete(query);
    if (autocompleteRes != null && autocompleteRes['suggestions'] is List) {
      final list = autocompleteRes['suggestions'] as List;
      if (list.isNotEmpty) {
        final first = list.first as Map<String, dynamic>;
        final placeId = first['placeId']?.toString();
        if (placeId != null) {
          if (placeId.startsWith('free_')) {
            final lat = first['lat'] != null ? (first['lat'] as num).toDouble() : null;
            final lng = first['lng'] != null ? (first['lng'] as num).toDouble() : null;
            if (lat != null && lng != null) {
              setState(() {
                if (isSource) {
                  _srcCoord = ll.LatLng(lat, lng);
                } else {
                  _dstCoord = ll.LatLng(lat, lng);
                }
              });
            }
          } else {
            final details = await ApiService.placesDetails(placeId);
            final d = details?['details'] as Map<String, dynamic>?;
            if (d != null) {
              final lat = d['lat'] != null ? (d['lat'] as num).toDouble() : null;
              final lng = d['lng'] != null ? (d['lng'] as num).toDouble() : null;
              if (lat != null && lng != null) {
                setState(() {
                  if (isSource) {
                    _srcCoord = ll.LatLng(lat, lng);
                  } else {
                    _dstCoord = ll.LatLng(lat, lng);
                  }
                });
              }
            }
          }
        }
      }
    }
  }

  Future<void> _doSearch() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _results = null;
      _errorMessage = null;
    });

    final res = await ApiService.compareRoutes(
      source: _sourceController.text.trim(),
      destination: _destController.text.trim(),
      time: _timeController.text.trim(),
      preference: _preference,
    ).timeout(const Duration(seconds: 45), onTimeout: () => null);

    setState(() {
      _isLoading = false;
      if (res != null) {
        _results = res;
      } else {
        _errorMessage = 'Failed to fetch route options. Is the backend running?';
      }
    });
  }

  Future<void> _saveJourney(Map<String, dynamic> opt) async {
    await ApiService.saveJourney({
      'from': _sourceController.text.trim(),
      'to': _destController.text.trim(),
      'time': _timeController.text.trim(),
      'mode': opt['mode'],
      'duration': opt['time'],
      'cost': opt['cost'],
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('🎉 Journey saved successfully!'),
          backgroundColor: Color(0xFF7C5CFF),
        ),
      );
    }
  }

  IconData _getIconForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return Icons.directions_bus;
      case 'metro':
        return Icons.subway;
      case 'cab':
        return Icons.local_taxi;
      case 'car':
        return Icons.directions_car;
      case 'multimodal':
        return Icons.shuffle;
      default:
        return Icons.directions;
    }
  }

  String _getLabelForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return 'BMTC Bus';
      case 'metro':
        return 'Namma Metro';
      case 'cab':
        return 'Cab / Auto';
      case 'car':
        return 'Personal Vehicle';
      case 'multimodal':
        return 'Multimodal Journey';
      default:
        return mode.toUpperCase();
    }
  }

  List<Map<String, dynamic>> _getParsedOptions() {
    if (_results == null) return [];
    final recommendations = _results!['recommendations'] as List<dynamic>? ?? [];
    final resultsMap = _results!['results'] as Map<String, dynamic>? ?? {};

    final List<Map<String, dynamic>> list = [];
    for (final rec in recommendations) {
      if (rec is! Map<String, dynamic>) continue;
      final mode = rec['mode']?.toString();
      if (mode == null) continue;
      final modeData = resultsMap[mode] as Map<String, dynamic>?;
      if (modeData == null || modeData['available'] != true) continue;

      var time = modeData['time'] ?? 0;
      var cost = modeData['cost'] ?? 0;
      var distance = modeData['distance'] ?? 0.0;
      var guide = modeData['guide'] as List<dynamic>?;
      var segments = modeData['segments'] as List<dynamic>?;
      final transfers = modeData['transfers'] ?? 0;

      if (mode == 'cab' && modeData['all_estimates'] is List && (modeData['all_estimates'] as List).isNotEmpty) {
        final firstEst = (modeData['all_estimates'] as List).first as Map<String, dynamic>;
        time = firstEst['time'] ?? time;
        cost = firstEst['cost'] ?? cost;
        distance = firstEst['distance'] ?? distance;
        guide = firstEst['guide'] as List<dynamic>? ?? guide;
        segments = firstEst['segments'] as List<dynamic>? ?? segments;
      }

      if (mode == 'multimodal' && modeData['all_options'] is List && (modeData['all_options'] as List).isNotEmpty) {
        final firstOpt = (modeData['all_options'] as List).first as Map<String, dynamic>;
        time = firstOpt['time'] ?? time;
        cost = firstOpt['cost'] ?? cost;
        distance = firstOpt['distance'] ?? distance;
        guide = firstOpt['guide'] as List<dynamic>? ?? guide;
        segments = firstOpt['segments'] as List<dynamic>? ?? segments;
      }

      list.add({
        'mode': mode,
        'time': time,
        'cost': cost,
        'distance': distance,
        'transfers': transfers,
        'guide': guide,
        'segments': segments,
        'explanation': rec['explanation'] ?? '',
        'score': rec['score'] ?? 0.0,
        'rank': rec['rank'] ?? 0,
        'emissions': rec['emissions'] ?? 0.0,
      });
    }
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;
    final accentPurple = const Color(0xFF7C5CFF);

    final recommendations = _results?['recommendations'] as List<dynamic>?;
    final bestOverall = (recommendations != null && recommendations.isNotEmpty)
        ? (recommendations.first as Map<String, dynamic>)['mode']?.toString()
        : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Plan Journey', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: cardBgColor,
        elevation: 1,
      ),
      body: Column(
        children: [
          // FormCard sits at the top
          Card(
            margin: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            color: cardBgColor,
            elevation: 4,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: RawAutocomplete<Map<String, dynamic>>(
                            textEditingController: _sourceController,
                            focusNode: _sourceFocusNode,
                            optionsBuilder: (TextEditingValue textEditingValue) async {
                              if (textEditingValue.text.length < 2) {
                                return const Iterable<Map<String, dynamic>>.empty();
                              }
                              final res = await ApiService.placesAutocomplete(textEditingValue.text);
                              if (res == null) return const Iterable<Map<String, dynamic>>.empty();
                              final suggestions = res['suggestions'] as List<dynamic>?;
                              if (suggestions == null) return const Iterable<Map<String, dynamic>>.empty();
                              return suggestions.map((s) => s as Map<String, dynamic>);
                            },
                            optionsViewBuilder: (BuildContext context, AutocompleteOnSelected<Map<String, dynamic>> onSelected, Iterable<Map<String, dynamic>> options) {
                              return Align(
                                alignment: Alignment.topLeft,
                                child: Material(
                                  elevation: 4.0,
                                  borderRadius: BorderRadius.circular(10),
                                  color: Theme.of(context).cardColor,
                                  child: SizedBox(
                                    width: MediaQuery.of(context).size.width * 0.4,
                                    child: ListView.builder(
                                      padding: EdgeInsets.zero,
                                      shrinkWrap: true,
                                      itemCount: options.length,
                                      itemBuilder: (BuildContext context, int index) {
                                        final option = options.elementAt(index);
                                        return ListTile(
                                          dense: true,
                                          title: Text(option['mainText'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                          subtitle: Text(option['secondaryText'] ?? '', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                          onTap: () => onSelected(option),
                                        );
                                      },
                                    ),
                                  ),
                                ),
                              );
                            },
                            fieldViewBuilder: (BuildContext context, TextEditingController textEditingController, FocusNode focusNode, VoidCallback onFieldSubmitted) {
                              return TextFormField(
                                controller: textEditingController,
                                focusNode: focusNode,
                                decoration: InputDecoration(
                                  labelText: 'FROM',
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  prefixIcon: const Icon(Icons.trip_origin, color: Colors.green, size: 18),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                validator: (v) => v!.trim().isEmpty ? 'Required' : null,
                              );
                            },
                            onSelected: (Map<String, dynamic> selection) async {
                              final fullText = selection['fullText']?.toString() ?? selection['mainText']?.toString() ?? '';
                              _sourceController.text = fullText;
                              final placeId = selection['placeId']?.toString();
                              if (placeId != null) {
                                if (placeId.startsWith('free_')) {
                                  final lat = selection['lat'] != null ? (selection['lat'] as num).toDouble() : null;
                                  final lng = selection['lng'] != null ? (selection['lng'] as num).toDouble() : null;
                                  if (lat != null && lng != null) {
                                    setState(() {
                                      _srcCoord = ll.LatLng(lat, lng);
                                    });
                                  }
                                } else {
                                  final details = await ApiService.placesDetails(placeId);
                                  final d = details?['details'] as Map<String, dynamic>?;
                                  if (d != null) {
                                    final lat = d['lat'] != null ? (d['lat'] as num).toDouble() : null;
                                    final lng = d['lng'] != null ? (d['lng'] as num).toDouble() : null;
                                    if (lat != null && lng != null) {
                                      setState(() {
                                        _srcCoord = ll.LatLng(lat, lng);
                                      });
                                    }
                                  }
                                }
                              }
                            },
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          child: GestureDetector(
                            onTap: () {
                              final tmp = _sourceController.text;
                              _sourceController.text = _destController.text;
                              _destController.text = tmp;
                              final tmpC = _srcCoord;
                              _srcCoord = _dstCoord;
                              _dstCoord = tmpC;
                            },
                            child: CircleAvatar(
                              radius: 16,
                              backgroundColor: accentPurple.withAlpha(26),
                              child: Icon(Icons.swap_horiz, color: accentPurple, size: 18),
                            ),
                          ),
                        ),
                        Expanded(
                          child: RawAutocomplete<Map<String, dynamic>>(
                            textEditingController: _destController,
                            focusNode: _destFocusNode,
                            optionsBuilder: (TextEditingValue textEditingValue) async {
                              if (textEditingValue.text.length < 2) {
                                return const Iterable<Map<String, dynamic>>.empty();
                              }
                              final res = await ApiService.placesAutocomplete(textEditingValue.text);
                              if (res == null) return const Iterable<Map<String, dynamic>>.empty();
                              final suggestions = res['suggestions'] as List<dynamic>?;
                              if (suggestions == null) return const Iterable<Map<String, dynamic>>.empty();
                              return suggestions.map((s) => s as Map<String, dynamic>);
                            },
                            optionsViewBuilder: (BuildContext context, AutocompleteOnSelected<Map<String, dynamic>> onSelected, Iterable<Map<String, dynamic>> options) {
                              return Align(
                                alignment: Alignment.topLeft,
                                child: Material(
                                  elevation: 4.0,
                                  borderRadius: BorderRadius.circular(10),
                                  color: Theme.of(context).cardColor,
                                  child: SizedBox(
                                    width: MediaQuery.of(context).size.width * 0.4,
                                    child: ListView.builder(
                                      padding: EdgeInsets.zero,
                                      shrinkWrap: true,
                                      itemCount: options.length,
                                      itemBuilder: (BuildContext context, int index) {
                                        final option = options.elementAt(index);
                                        return ListTile(
                                          dense: true,
                                          title: Text(option['mainText'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                          subtitle: Text(option['secondaryText'] ?? '', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                          onTap: () => onSelected(option),
                                        );
                                      },
                                    ),
                                  ),
                                ),
                              );
                            },
                            fieldViewBuilder: (BuildContext context, TextEditingController textEditingController, FocusNode focusNode, VoidCallback onFieldSubmitted) {
                              return TextFormField(
                                controller: textEditingController,
                                focusNode: focusNode,
                                decoration: InputDecoration(
                                  labelText: 'TO',
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  prefixIcon: const Icon(Icons.location_on, color: Colors.red, size: 18),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                validator: (v) => v!.trim().isEmpty ? 'Required' : null,
                              );
                            },
                            onSelected: (Map<String, dynamic> selection) async {
                              final fullText = selection['fullText']?.toString() ?? selection['mainText']?.toString() ?? '';
                              _destController.text = fullText;
                              final placeId = selection['placeId']?.toString();
                              if (placeId != null) {
                                if (placeId.startsWith('free_')) {
                                  final lat = selection['lat'] != null ? (selection['lat'] as num).toDouble() : null;
                                  final lng = selection['lng'] != null ? (selection['lng'] as num).toDouble() : null;
                                  if (lat != null && lng != null) {
                                    setState(() {
                                      _dstCoord = ll.LatLng(lat, lng);
                                    });
                                  }
                                } else {
                                  final details = await ApiService.placesDetails(placeId);
                                  final d = details?['details'] as Map<String, dynamic>?;
                                  if (d != null) {
                                    final lat = d['lat'] != null ? (d['lat'] as num).toDouble() : null;
                                    final lng = d['lng'] != null ? (d['lng'] as num).toDouble() : null;
                                    if (lat != null && lng != null) {
                                      setState(() {
                                        _dstCoord = ll.LatLng(lat, lng);
                                      });
                                    }
                                  }
                                }
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final time = await showTimePicker(
                                context: context,
                                initialTime: TimeOfDay.now(),
                              );
                              if (time != null) {
                                setState(() {
                                  _timeController.text = "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}";
                                });
                              }
                            },
                            child: IgnorePointer(
                              child: TextFormField(
                                controller: _timeController,
                                decoration: InputDecoration(
                                  labelText: 'Time',
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  prefixIcon: const Icon(Icons.access_time, size: 18),
                                  suffixIcon: TextButton(
                                    onPressed: () {
                                      final now = DateTime.now();
                                      setState(() {
                                        _timeController.text = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";
                                      });
                                    },
                                    child: const Text('Now', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                  ),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            initialValue: _preference,
                            isDense: true,
                            decoration: InputDecoration(
                              labelText: 'Preference',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'cost', child: Text('Cost')),
                              DropdownMenuItem(value: 'time', child: Text('Fastest')),
                              DropdownMenuItem(value: 'convenience', child: Text('Ease')),
                            ],
                            onChanged: (v) => setState(() => _preference = v!),
                          ),
                        ),
                        const SizedBox(width: 8),
                        SizedBox(
                          height: 42,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF7C5CFF), Color(0xFF5B21B6)],
                              ),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.transparent,
                                shadowColor: Colors.transparent,
                                padding: const EdgeInsets.symmetric(horizontal: 14),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                              onPressed: _isLoading ? null : _doSearch,
                              child: _isLoading
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                                  : const Icon(Icons.search, color: Colors.white, size: 20),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),

          // Scrollable Route Options List
          Expanded(
            child: _buildResultsView(isDark, accentPurple, bestOverall),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsView(bool isDark, Color accentPurple, String? bestOverall) {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 12),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    if (_results == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.directions_outlined, color: Colors.grey.withAlpha(128), size: 64),
            const SizedBox(height: 12),
            const Text(
              'Enter source & destination to plan your journey',
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
          ],
        ),
      );
    }

    final parsedOptions = _getParsedOptions();

    if (parsedOptions.isEmpty) {
      return const Center(
        child: Text('No routes found for this journey.', style: TextStyle(color: Colors.grey)),
      );
    }

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      children: [
        if (bestOverall != null) ...[
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF7C5CFF), Color(0xFF5B21B6)]),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.star, color: Colors.amber, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '⭐ Recommended Best Option: ${_getLabelForMode(bestOverall)}',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
        ],

        Text(
          '🔄 Available Transport Options',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: isDark ? Colors.white : Colors.black87,
          ),
        ),
        const SizedBox(height: 8),

        ...parsedOptions.map((opt) {
          final mode = opt['mode']?.toString() ?? '';
          final duration = opt['time'] ?? 0;
          final cost = opt['cost'] ?? 0;
          final walk = opt['distance'] ?? 0.0;
          final isBest = bestOverall == mode;

          return Card(
            color: isDark ? const Color(0xFF1E2130) : Colors.white,
            margin: const EdgeInsets.symmetric(vertical: 6),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: isBest
                  ? const BorderSide(color: Color(0xFF7C5CFF), width: 2)
                  : BorderSide.none,
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(14),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => RouteDetailsScreen(
                      source: _sourceController.text.trim(),
                      destination: _destController.text.trim(),
                      option: opt,
                      srcCoord: _srcCoord,
                      dstCoord: _dstCoord,
                    ),
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: accentPurple.withAlpha(26),
                      child: Icon(_getIconForMode(mode), color: accentPurple),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                _getLabelForMode(mode),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                              if (isBest) ...[
                                const SizedBox(width: 8),
                                const Icon(Icons.star, color: Colors.amber, size: 14),
                              ],
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '⏱️ $duration min  |  ₹$cost  |  🚶 ${walk}km',
                            style: const TextStyle(fontSize: 12, color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.bookmark_add_outlined, size: 20),
                      color: accentPurple,
                      onPressed: () => _saveJourney(opt),
                    ),
                    Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey[400]),
                  ],
                ),
              ),
            ),
          );
        }),
        const SizedBox(height: 24),
      ],
    );
  }
}
