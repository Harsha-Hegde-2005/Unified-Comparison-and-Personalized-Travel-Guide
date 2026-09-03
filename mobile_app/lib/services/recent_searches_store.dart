import 'dart:convert';
import 'package:flutter/foundation.dart';
// ignore: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;

class RecentSearchesStore {
  static final List<Map<String, String>> _recentSearches = [
    {'source': 'Hebbal', 'destination': 'Indiranagar'},
    {'source': 'Majestic', 'destination': 'Electronic City'},
    {'source': 'Whitefield', 'destination': 'MG Road'},
    {'source': 'BTM Layout', 'destination': 'Silk Board'},
    {'source': 'Jayanagar', 'destination': 'Banashankari'},
  ];

  static bool _initialized = false;

  static List<Map<String, String>> get searches {
    if (!_initialized) {
      _initFromLocalStorage();
    }
    return List.unmodifiable(_recentSearches);
  }

  static void _initFromLocalStorage() {
    _initialized = true;
    if (kIsWeb) {
      try {
        final saved = html.window.localStorage['bmtc_recent_searches_v2'];
        if (saved != null && saved.isNotEmpty) {
          final decoded = json.decode(saved) as List<dynamic>;
          if (decoded.isNotEmpty) {
            _recentSearches.clear();
            for (final item in decoded) {
              if (item is Map) {
                final src = item['source']?.toString() ?? item['from']?.toString() ?? '';
                final dst = item['destination']?.toString() ?? item['to']?.toString() ?? '';
                if (src.isNotEmpty && dst.isNotEmpty) {
                  _recentSearches.add({'source': src, 'destination': dst});
                }
              }
            }
          }
        }
      } catch (_) {}
    }
  }

  static void loadFromBackendList(List<dynamic>? backendList) {
    if (backendList == null || backendList.isEmpty) return;
    final List<Map<String, String>> fetched = [];
    for (final item in backendList) {
      if (item is Map) {
        final src = item['source']?.toString() ?? item['from']?.toString() ?? item['src']?.toString() ?? '';
        final dst = item['destination']?.toString() ?? item['to']?.toString() ?? item['dst']?.toString() ?? '';
        if (src.isNotEmpty && dst.isNotEmpty) {
          fetched.add({'source': src, 'destination': dst});
        }
      }
    }

    if (fetched.isNotEmpty) {
      _recentSearches.clear();
      for (final f in fetched) {
        addSearch(f['source']!, f['destination']!);
      }
    }
  }

  static void addSearch(String source, String destination) {
    final src = source.trim();
    final dst = destination.trim();
    if (src.isEmpty || dst.isEmpty) return;

    _recentSearches.removeWhere(
      (item) =>
          item['source']?.toLowerCase() == src.toLowerCase() &&
          item['destination']?.toLowerCase() == dst.toLowerCase(),
    );

    _recentSearches.insert(0, {'source': src, 'destination': dst});

    if (_recentSearches.length > 5) {
      _recentSearches.removeRange(5, _recentSearches.length);
    }

    _saveToLocalStorage();
  }

  static void _saveToLocalStorage() {
    if (kIsWeb) {
      try {
        html.window.localStorage['bmtc_recent_searches_v2'] = json.encode(_recentSearches);
      } catch (_) {}
    }
  }
}
