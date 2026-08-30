import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Central API service that mirrors every endpoint used by the website frontend.
/// All methods are static. The [baseUrl] can be updated at runtime from the
/// Settings dialog so physical-device users can point to a remote server.
class ApiService {
  // ── Base URL ──────────────────────────────────────────────────────────────

  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://localhost:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  static String baseUrl = defaultBaseUrl;

  // ── Auth state ────────────────────────────────────────────────────────────

  static String? token;
  static String? loggedInUsername;

  static Map<String, String> get authHeaders => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  // ── Helpers ───────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>?> _get(String path) async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl$path'))
          .timeout(const Duration(seconds: 12));
      if (res.statusCode == 200) {
        return json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<Map<String, dynamic>?> _getAuth(String path) async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl$path'), headers: authHeaders)
          .timeout(const Duration(seconds: 12));
      if (res.statusCode == 200) {
        return json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<Map<String, dynamic>?> _post(String path, Map<String, dynamic> body) async {
    try {
      final res = await http
          .post(
            Uri.parse('$baseUrl$path'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode(body),
          )
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) {
        return json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<Map<String, dynamic>?> _postAuth(String path, Map<String, dynamic> body) async {
    try {
      final res = await http
          .post(
            Uri.parse('$baseUrl$path'),
            headers: authHeaders,
            body: json.encode(body),
          )
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) {
        return json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> _deleteAuth(String path) async {
    try {
      final res = await http
          .delete(Uri.parse('$baseUrl$path'), headers: authHeaders)
          .timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // AUTH  (/api/auth/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    final url = Uri.parse('$baseUrl/api/auth/login');
    try {
      final res = await http
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'username': username, 'password': password}),
          )
          .timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        token = data['access_token'];
        loggedInUsername = data['username'];
        return {'success': true, 'username': loggedInUsername};
      } else {
        final err = json.decode(res.body);
        return {'success': false, 'error': err['detail'] ?? 'Invalid credentials'};
      }
    } catch (e) {
      return {'success': false, 'error': 'Cannot connect to backend'};
    }
  }

  static Future<Map<String, dynamic>> signup({
    required String username,
    required String password,
  }) async {
    final url = Uri.parse('$baseUrl/api/auth/signup');
    try {
      final res = await http
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'username': username, 'password': password}),
          )
          .timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        token = data['access_token'];
        loggedInUsername = data['username'];
        return {'success': true, 'username': loggedInUsername};
      } else {
        final err = json.decode(res.body);
        return {'success': false, 'error': err['detail'] ?? 'Registration failed'};
      }
    } catch (e) {
      return {'success': false, 'error': 'Cannot connect to backend'};
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CHATBOT  (/api/chatbot/query)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> queryChatbot({
    required String message,
    required List<Map<String, dynamic>> history,
    double? latitude,
    double? longitude,
    String? timeStr,
    String? weatherStr,
  }) async {
    return _post('/api/chatbot/query', {
      'message': message,
      'history': history,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
      if (timeStr != null) 'time': timeStr,
      if (weatherStr != null) 'weather': weatherStr,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // COMPARE  (/api/compare)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> compareRoutes({
    required String source,
    required String destination,
    String? time,
    String preference = 'cost',
    String? vehicle,
  }) async {
    return _post('/api/compare', {
      'source': source,
      'destination': destination,
      if (time != null) 'time': time,
      'preference': preference,
      if (vehicle != null) 'vehicle': vehicle,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // BMTC JOURNEY  (/api/bmtc/plan)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> bmtcPlan({
    required String source,
    required String destination,
    String? time,
    String preference = 'cost',
  }) async {
    return _post('/api/bmtc/plan', {
      'source': source,
      'destination': destination,
      if (time != null) 'time': time,
      'preference': preference,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ALL BUSES  (/api/bmtc/all-buses)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchAllBuses({
    required String source,
    required String destination,
    String? time,
  }) async {
    return _post('/api/bmtc/all-buses', {
      'source': source,
      'destination': destination,
      if (time != null) 'time': time,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // METRO  (/api/metro/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> metroTimetable({
    String source = '',
    String time = '',
  }) async {
    final params = <String>[];
    if (source.isNotEmpty) params.add('source=${Uri.encodeComponent(source)}');
    if (time.isNotEmpty) params.add('time=${Uri.encodeComponent(time)}');
    final qs = params.isEmpty ? '' : '?${params.join('&')}';
    return _get('/api/timetable/metro$qs');
  }

  static Future<Map<String, dynamic>?> metroStations() async =>
      _get('/api/metro/stations');

  static Future<Map<String, dynamic>?> metroLineInfo(String station) async =>
      _get('/api/metro/line-info?station=${Uri.encodeComponent(station)}');

  static Future<Map<String, dynamic>?> metroPlan({
    required String source,
    required String destination,
    String? time,
  }) async {
    return _post('/api/metro/plan', {
      'source': source,
      'destination': destination,
      if (time != null) 'time': time,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // BMTC ROUTES / TIMETABLE / STOPS  (/api/bmtc/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchAllRoutes({String q = ''}) async {
    final qs = q.isNotEmpty ? '?q=${Uri.encodeComponent(q)}' : '';
    return _get('/api/bmtc/routes$qs');
  }

  static Future<Map<String, dynamic>?> fetchRouteDetails(String route) async =>
      _get('/api/bmtc/route-search?route=${Uri.encodeComponent(route)}');

  static Future<Map<String, dynamic>?> fetchRouteTimetable(String route, [String? stop]) async {
    final sp = stop != null ? '&stop=${Uri.encodeComponent(stop)}' : '';
    return _get('/api/bmtc/route-timetable?route=${Uri.encodeComponent(route)}$sp');
  }

  static Future<Map<String, dynamic>?> fetchBmtcStops() async =>
      _get('/api/bmtc/stops');

  static Future<Map<String, dynamic>?> fetchStopArrivals(String stop, {int limit = 20}) async =>
      _get('/api/bmtc/stop-arrivals?stop=${Uri.encodeComponent(stop)}&limit=$limit');

  // ═══════════════════════════════════════════════════════════════════════════
  // STOPS / COORDINATES  (/api/stops/*)
  // ═══════════════════════════════════════════════════════════════════════════

  /// Returns combined BMTC + Metro stop list (mirrors apiStops() in frontend)
  static Future<Map<String, dynamic>> fetchAllStops() async {
    try {
      final futures = await Future.wait([
        _get('/api/bmtc/stops'),
        _get('/api/metro/stations'),
      ]);
      final bmtcStops = (futures[0]?['stops'] as List<dynamic>?)?.cast<String>() ?? [];
      final rawMetro = (futures[1]?['stations'] as List<dynamic>?)?.cast<String>() ?? [];
      final metroStations = rawMetro.map((s) =>
          s.endsWith(' Metro Station') ? s : '$s Metro Station').toList();
      final all = {...bmtcStops, ...metroStations}.toList()..sort();
      return {'all': all, 'bmtc': bmtcStops, 'metro': metroStations};
    } catch (_) {
      return {'all': [], 'bmtc': [], 'metro': []};
    }
  }

  static Future<Map<String, dynamic>?> fetchStopCoords(List<String> stops) async {
    return _post('/api/stops/coords', {'stops': stops});
  }

  static Future<Map<String, dynamic>?> fetchNearbyStops(double lat, double lng) async =>
      _get('/api/stops/nearby?lat=$lat&lng=$lng');

  // ═══════════════════════════════════════════════════════════════════════════
  // CAB  (/api/cab/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchCabProviders() async =>
      _get('/api/cab/providers');

  static Future<Map<String, dynamic>?> estimateCab({
    required double srcLat,
    required double srcLng,
    required double dstLat,
    required double dstLng,
  }) async {
    return _post('/api/cab/estimate', {
      'src_lat': srcLat,
      'src_lng': srcLng,
      'dst_lat': dstLat,
      'dst_lng': dstLng,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // VEHICLE (personal)  (/api/vehicle/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchVehicleList() async =>
      _get('/api/vehicle/list');

  static Future<Map<String, dynamic>?> estimateVehicle({
    required String vehicleName,
    required String source,
    required String destination,
  }) async {
    return _post('/api/vehicle/estimate', {
      'vehicle_name': vehicleName,
      'source': source,
      'destination': destination,
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // WEATHER  (/api/weather/report)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchWeatherReport(
    double lat,
    double lng, [
    String name = 'Bengaluru',
  ]) async =>
      _get('/api/weather/report?lat=$lat&lng=$lng&location_name=${Uri.encodeComponent(name)}');

  // ═══════════════════════════════════════════════════════════════════════════
  // PLACES  (/api/places/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> placesAutocomplete(String query) async =>
      _get('/api/places/autocomplete?query=${Uri.encodeComponent(query)}');

  static Future<Map<String, dynamic>?> placesDetails(String placeId) async =>
      _get('/api/places/details?placeId=${Uri.encodeComponent(placeId)}');

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFIG  (/api/config/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchConfig() async =>
      _get('/api/config');

  static Future<String?> fetchGoogleMapsKey() async {
    final res = await _get('/api/config/google-maps-key');
    return res?['key'] as String?;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // USER DASHBOARD  (/api/user/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchDashboard() async =>
      _getAuth('/api/user/dashboard');

  // journeys
  static Future<Map<String, dynamic>?> saveJourney(Map<String, dynamic> journey) async =>
      _postAuth('/api/user/journey', journey);

  static Future<bool> deleteJourney(int journeyId) async =>
      _deleteAuth('/api/user/journey/$journeyId');

  // vehicles
  static Future<List<dynamic>?> fetchVehicles() async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl/api/user/vehicles'), headers: authHeaders)
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        return json.decode(res.body) as List<dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> addVehicle(String name, String fuelType, double efficiency) async {
    final res = await _postAuth('/api/user/vehicles', {
      'name': name,
      'fuel_type': fuelType,
      'efficiency': efficiency,
    });
    return res != null;
  }

  static Future<bool> deleteVehicle(int id) async =>
      _deleteAuth('/api/user/vehicles/$id');

  // documents
  static Future<List<dynamic>?> fetchDocuments() async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl/api/user/documents'), headers: authHeaders)
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        return json.decode(res.body) as List<dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> deleteDocument(int docId) async =>
      _deleteAuth('/api/user/documents/$docId');

  // ═══════════════════════════════════════════════════════════════════════════
  // HEALTH CHECK
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<bool> checkHealth() async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl/api/health'))
          .timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
