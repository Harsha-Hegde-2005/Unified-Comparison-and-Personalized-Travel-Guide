import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

/// Reusable Google Places & Transit Stops autocomplete search field with reliable tap selection
class PlacesAutocompleteField extends StatefulWidget {
  final TextEditingController controller;
  final String label;
  final String? hint;
  final IconData icon;
  final Color iconColor;
  final ValueChanged<String>? onChanged;
  final Function(String placeName, double? lat, double? lng)? onPlaceSelected;
  final VoidCallback? onSubmitted;

  const PlacesAutocompleteField({
    super.key,
    required this.controller,
    required this.label,
    this.hint,
    this.icon = Icons.location_on_rounded,
    this.iconColor = AppTheme.bmtcColor,
    this.onChanged,
    this.onPlaceSelected,
    this.onSubmitted,
  });

  @override
  State<PlacesAutocompleteField> createState() => _PlacesAutocompleteFieldState();
}

class _PlacesAutocompleteFieldState extends State<PlacesAutocompleteField> {
  final FocusNode _focusNode = FocusNode();
  final LayerLink _layerLink = LayerLink();
  OverlayEntry? _overlayEntry;
  List<Map<String, dynamic>> _suggestions = [];
  bool _isLoading = false;
  Timer? _debounce;
  bool _isSelecting = false;

  @override
  void initState() {
    super.initState();
    _focusNode.addListener(() {
      if (!_focusNode.hasFocus && !_isSelecting) {
        Future.delayed(const Duration(milliseconds: 150), () {
          if (!_isSelecting && mounted) {
            _hideOverlay();
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _hideOverlay();
    _focusNode.dispose();
    super.dispose();
  }

  void _onTextChanged(String val) {
    if (widget.onChanged != null) widget.onChanged!(val);

    _debounce?.cancel();
    final query = val.trim();
    if (query.length < 2) {
      _hideOverlay();
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 200), () async {
      if (!mounted) return;
      setState(() => _isLoading = true);
      final res = await ApiService.placesAutocomplete(query);
      if (!mounted) return;

      final rawList = res?['suggestions'] as List<dynamic>? ?? [];
      final List<Map<String, dynamic>> parsed = [];

      for (final item in rawList) {
        if (item is Map<String, dynamic>) {
          parsed.add(item);
        }
      }

      // Fallback to local stop search if empty
      if (parsed.isEmpty) {
        final stopsRes = await ApiService.fetchAllStops();
        final all = (stopsRes['all'] as List<dynamic>?)?.cast<String>() ?? [];
        final matched = all
            .where((s) => s.toLowerCase().contains(query.toLowerCase()))
            .take(6)
            .toList();

        for (final m in matched) {
          parsed.add({
            'mainText': m,
            'secondaryText': m.toLowerCase().contains('metro') ? 'Namma Metro Station' : 'BMTC Bus Stop',
            'placeId': 'stop_$m',
          });
        }
      }

      setState(() {
        _isLoading = false;
        _suggestions = parsed;
      });

      if (_suggestions.isNotEmpty && _focusNode.hasFocus) {
        _showOverlay();
      } else {
        _hideOverlay();
      }
    });
  }

  Future<void> _selectSuggestion(Map<String, dynamic> item) async {
    _isSelecting = true;
    final mainText = item['mainText']?.toString() ?? item['fullText']?.toString() ?? '';
    widget.controller.text = mainText;
    _hideOverlay();

    double? lat = (item['lat'] as num?)?.toDouble();
    double? lng = (item['lng'] as num?)?.toDouble();

    final placeId = item['placeId']?.toString();
    if ((lat == null || lng == null) && placeId != null && !placeId.startsWith('stop_') && !placeId.startsWith('free_')) {
      final details = await ApiService.placesDetails(placeId);
      final d = details?['details'] as Map<String, dynamic>?;
      if (d != null) {
        lat = (d['lat'] as num?)?.toDouble();
        lng = (d['lng'] as num?)?.toDouble();
      }
    }

    if (lat == null || lng == null) {
      final highRes = await ApiService.geocodeHighPrecision(mainText);
      if (highRes != null) {
        lat = highRes.latitude;
        lng = highRes.longitude;
      }
    }

    if (widget.onPlaceSelected != null) {
      widget.onPlaceSelected!(mainText, lat, lng);
    }
    if (widget.onSubmitted != null) {
      widget.onSubmitted!();
    }

    _isSelecting = false;
  }

  void _showOverlay() {
    _hideOverlay();
    final overlay = Overlay.of(context);
    final renderBox = context.findRenderObject() as RenderBox?;
    if (renderBox == null) return;
    final size = renderBox.size;

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final borderCol = AppTheme.getBorder(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    _overlayEntry = OverlayEntry(
      builder: (context) => Positioned(
        width: size.width,
        child: CompositedTransformFollower(
          link: _layerLink,
          showWhenUnlinked: false,
          offset: Offset(0, size.height + 4),
          child: Material(
            elevation: 10,
            color: cardBg,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              constraints: const BoxConstraints(maxHeight: 230),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: borderCol),
              ),
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(vertical: 4),
                shrinkWrap: true,
                itemCount: _suggestions.length,
                separatorBuilder: (context, index) => Divider(height: 1, color: borderCol),
                itemBuilder: (context, index) {
                  final item = _suggestions[index];
                  final mainText = item['mainText']?.toString() ?? '';
                  final secText = item['secondaryText']?.toString() ?? 'Bengaluru';
                  final isMetro = mainText.toLowerCase().contains('metro') || secText.toLowerCase().contains('metro');

                  return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTapDown: (_) {
                      _isSelecting = true;
                    },
                    onTap: () => _selectSuggestion(item),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: (isMetro ? AppTheme.metroColor : AppTheme.bmtcColor).withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(
                              isMetro ? Icons.subway_rounded : Icons.location_on_rounded,
                              size: 16,
                              color: isMetro ? AppTheme.metroColor : AppTheme.bmtcColor,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  mainText,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                    color: textColor,
                                  ),
                                ),
                                if (secText.isNotEmpty)
                                  Text(
                                    secText,
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: mutedColor,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                          const Icon(Icons.north_west_rounded, size: 14, color: Colors.grey),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );

    overlay.insert(_overlayEntry!);
  }

  void _hideOverlay() {
    _overlayEntry?.remove();
    _overlayEntry = null;
  }

  @override
  Widget build(BuildContext context) {
    return CompositedTransformTarget(
      link: _layerLink,
      child: TextFormField(
        controller: widget.controller,
        focusNode: _focusNode,
        onChanged: _onTextChanged,
        onFieldSubmitted: (_) {
          _hideOverlay();
          if (widget.onSubmitted != null) widget.onSubmitted!();
        },
        decoration: InputDecoration(
          labelText: widget.label,
          hintText: widget.hint,
          isDense: true,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
          prefixIcon: Icon(widget.icon, color: widget.iconColor, size: 18),
          suffixIcon: _isLoading
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: Center(
                    child: SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                )
              : (widget.controller.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 16),
                      onPressed: () {
                        widget.controller.clear();
                        _hideOverlay();
                        if (widget.onChanged != null) widget.onChanged!('');
                      },
                    )
                  : null),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }
}
