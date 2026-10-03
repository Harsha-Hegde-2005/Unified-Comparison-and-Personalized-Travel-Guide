import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart' as ll;
import 'package:shared_preferences/shared_preferences.dart';

/// Central API service that mirrors every endpoint used by the website frontend.
/// All methods are static. The [baseUrl] can be updated at runtime from the
/// Settings dialog so physical-device users can point to a remote server.
class ApiService {
  // ── Base URL ──────────────────────────────────────────────────────────────

  static String get defaultBaseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;
    if (kIsWeb) return 'http://localhost:8000';
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://192.168.0.103:8000';
    return 'http://127.0.0.1:8000';
  }

  static String baseUrl = defaultBaseUrl;

  // ── Auth state ────────────────────────────────────────────────────────────

  static String? token;
  static String? loggedInUsername;

  static Map<String, String> get authHeaders => {
        'Content-Type': 'application/json',
        'Bypass-Tunnel-Reminder': 'true',
        'User-Agent': 'BMTC_Mobile_App',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  static Future<void> saveSession(String userToken, String username) async {
    token = userToken;
    loggedInUsername = username;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_token', userToken);
      await prefs.setString('logged_in_username', username);
      await prefs.setBool('is_logged_in', true);
    } catch (_) {}
  }

  static Future<String?> loadSavedSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final isLoggedIn = prefs.getBool('is_logged_in') ?? false;
      if (isLoggedIn) {
        token = prefs.getString('user_token');
        loggedInUsername = prefs.getString('logged_in_username') ?? 'Commuter';
        return loggedInUsername;
      }
    } catch (_) {}
    return null;
  }

  static Future<void> logoutSession() async {
    token = null;
    loggedInUsername = null;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('user_token');
      await prefs.remove('logged_in_username');
      await prefs.setBool('is_logged_in', false);
    } catch (_) {}
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>?> _get(String path) async {
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
            headers: authHeaders,
            body: json.encode(body),
          )
          .timeout(const Duration(seconds: 45));
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
    bool isRetry = false,
  }) async {
    final url = Uri.parse('$baseUrl/api/auth/login');
    try {
      final res = await http
          .post(
            url,
            headers: authHeaders,
            body: json.encode({'username': username, 'password': password}),
          )
          .timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final userToken = data['access_token'] as String;
        final uName = data['username'] as String;
        await saveSession(userToken, uName);
        return {'success': true, 'username': loggedInUsername};
      } else {
        final err = json.decode(res.body);
        return {'success': false, 'error': err['detail'] ?? 'Invalid credentials'};
      }
    } catch (e) {
      if (!isRetry) {
        final reconnected = await checkHealth();
        if (reconnected) {
          return login(username: username, password: password, isRetry: true);
        }
      }
      return {'success': false, 'error': 'Cannot connect to backend server ($baseUrl)'};
    }
  }

  static Future<Map<String, dynamic>> signup({
    required String username,
    required String password,
    bool isRetry = false,
  }) async {
    final url = Uri.parse('$baseUrl/api/auth/signup');
    try {
      final res = await http
          .post(
            url,
            headers: authHeaders,
            body: json.encode({'username': username, 'password': password}),
          )
          .timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final userToken = data['access_token'] as String;
        final uName = data['username'] as String;
        await saveSession(userToken, uName);
        return {'success': true, 'username': loggedInUsername};
      } else {
        final err = json.decode(res.body);
        return {'success': false, 'error': err['detail'] ?? 'Registration failed'};
      }
    } catch (e) {
      if (!isRetry) {
        final reconnected = await checkHealth();
        if (reconnected) {
          return signup(username: username, password: password, isRetry: true);
        }
      }
      return {'success': false, 'error': 'Cannot connect to backend server ($baseUrl)'};
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
    final Map<String, dynamic> body = {
      'message': message,
      'history': history,
    };
    if (latitude != null) body['latitude'] = latitude;
    if (longitude != null) body['longitude'] = longitude;
    if (timeStr != null) body['time'] = timeStr;
    if (weatherStr != null) body['weather'] = weatherStr;
    return _post('/api/chatbot/query', body);
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
    final Map<String, dynamic> body = {
      'source': source,
      'destination': destination,
      'preference': preference,
    };
    if (time != null && time.isNotEmpty) body['time'] = time;
    if (vehicle != null && vehicle.isNotEmpty) body['vehicle'] = vehicle;
    return _post('/api/compare', body);
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
    final Map<String, dynamic> body = {
      'source': source,
      'destination': destination,
      'preference': preference,
    };
    if (time != null) body['time'] = time;
    return _post('/api/bmtc/plan', body);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ALL BUSES  (/api/bmtc/all-buses)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchAllBuses({
    required String source,
    required String destination,
    String? time,
  }) async {
    final Map<String, dynamic> body = {
      'source': source,
      'destination': destination,
    };
    if (time != null) body['time'] = time;
    return _post('/api/bmtc/all-buses', body);
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
    final Map<String, dynamic> body = {
      'source': source,
      'destination': destination,
    };
    if (time != null) body['time'] = time;
    return _post('/api/metro/plan', body);
  }
  static Future<Map<String, dynamic>?> fetchRideMetroLines() async =>
      _get('/api/ride/metro/lines');

  static Future<Map<String, dynamic>?> fetchRideBusRoutes() async =>
      _get('/api/ride/bus/routes');

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

  static Future<Map<String, dynamic>?> fetchStopsInfo({String? query, double? lat, double? lng}) async {
    final params = <String>[];
    if (query != null && query.isNotEmpty) params.add('query=${Uri.encodeComponent(query)}');
    if (lat != null) params.add('lat=$lat');
    if (lng != null) params.add('lng=$lng');
    final qs = params.isNotEmpty ? '?${params.join('&')}' : '';
    return _get('/api/stops/info$qs');
  }

  static Future<Map<String, dynamic>?> fetchBmtcBusesForStop(String stop) async =>
      _get('/api/stops/bmtc-buses?stop=${Uri.encodeComponent(stop)}');

  static Future<Map<String, dynamic>?> fetchFareCalculate({required String mode, required String source, required String destination}) async {
    return _get('/api/fare/calculate?mode=$mode&source=${Uri.encodeComponent(source)}&destination=${Uri.encodeComponent(destination)}');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STOPS / COORDINATES  (/api/stops/*)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>>? _stopsFuture;
  static Map<String, dynamic>? _cachedStops;

  /// Returns combined BMTC + Metro stop list (mirrors apiStops() in frontend)
  static Future<Map<String, dynamic>> fetchAllStops() async {
    if (_cachedStops != null && (_cachedStops!['all'] as List).isNotEmpty) {
      return _cachedStops!;
    }
    _stopsFuture ??= (() async {
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
        _cachedStops = {'all': all, 'bmtc': bmtcStops, 'metro': metroStations};
        return _cachedStops!;
      } catch (_) {
        return {'all': [], 'bmtc': [], 'metro': []};
      }
    })();
    return _stopsFuture!;
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
  // PEDESTRIAN WALKING ROUTE (OSRM Foot API)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<Map<String, dynamic>?> fetchWalkingRoute(
    double srcLat,
    double srcLng,
    double dstLat,
    double dstLng,
  ) async {
    try {
      final url = Uri.parse(
        'https://router.project-osrm.org/route/v1/foot/$srcLng,$srcLat;$dstLng,$dstLat?overview=full&geometries=geojson&steps=true',
      );
      final res = await http.get(url).timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final routes = data['routes'] as List<dynamic>?;
        if (routes != null && routes.isNotEmpty) {
          final route = routes.first as Map<String, dynamic>;
          final geometry = route['geometry'] as Map<String, dynamic>?;
          final coords = geometry?['coordinates'] as List<dynamic>?;

          final List<ll.LatLng> points = [];
          if (coords != null) {
            for (final c in coords) {
              if (c is List && c.length >= 2) {
                final lng = (c[0] as num).toDouble();
                final lat = (c[1] as num).toDouble();
                points.add(ll.LatLng(lat, lng));
              }
            }
          }

          final List<Map<String, dynamic>> steps = [];
          final legs = route['legs'] as List<dynamic>?;
          if (legs != null && legs.isNotEmpty) {
            final legSteps = legs.first['steps'] as List<dynamic>?;
            if (legSteps != null) {
              for (final s in legSteps) {
                if (s is Map<String, dynamic>) {
                  final name = s['name']?.toString() ?? '';
                  final maneuver = s['maneuver'] as Map<String, dynamic>?;
                  final type = maneuver?['type']?.toString() ?? 'walk';
                  final modifier = maneuver?['modifier']?.toString() ?? '';
                  final dist = (s['distance'] as num?)?.toDouble() ?? 0.0;

                  String instr = 'Walk ahead';
                  if (type == 'depart') {
                    instr = name.isNotEmpty ? 'Head out on $name' : 'Head out towards destination';
                  } else if (type == 'turn') {
                    instr = 'Turn $modifier ${name.isNotEmpty ? "onto $name" : ""}';
                  } else if (type == 'arrive') {
                    instr = 'Arrive at destination entrance';
                  } else if (name.isNotEmpty) {
                    instr = 'Walk on $name';
                  }

                  steps.add({
                    'instruction': instr,
                    'distance': '${dist.toStringAsFixed(0)} m',
                  });
                }
              }
            }
          }

          return {
            'points': points,
            'steps': steps,
            'distance': route['distance'],
            'duration': route['duration'],
          };
        }
      }
    } catch (_) {}
    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ROAD GEOMETRY POLYLINE (Turn-by-turn Street Routing)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<List<ll.LatLng>> fetchRoadPolyline(
    List<ll.LatLng> waypoints, {
    String profile = 'driving',
  }) async {
    if (waypoints.length < 2) return waypoints;
    try {
      final waypointStr = waypoints
          .map((pt) => '${pt.longitude},${pt.latitude}')
          .join(';');
      final mode = (profile == 'walk' || profile == 'foot') ? 'foot' : 'driving';
      final url = Uri.parse(
        'https://router.project-osrm.org/route/v1/$mode/$waypointStr?overview=full&geometries=geojson',
      );
      final res = await http.get(url).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final routes = data['routes'] as List<dynamic>?;
        if (routes != null && routes.isNotEmpty) {
          final route = routes.first as Map<String, dynamic>;
          final geometry = route['geometry'] as Map<String, dynamic>?;
          final coords = geometry?['coordinates'] as List<dynamic>?;

          final List<ll.LatLng> roadPoints = [];
          if (coords != null) {
            for (final c in coords) {
              if (c is List && c.length >= 2) {
                final lng = (c[0] as num).toDouble();
                final lat = (c[1] as num).toDouble();
                roadPoints.add(ll.LatLng(lat, lng));
              }
            }
          }
          if (roadPoints.length >= 2) {
            return roadPoints;
          }
        }
      }
    } catch (_) {}
    return waypoints;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HIGH-PRECISION FORWARD GEOCODING (Place Name -> Exact Lat, Lng)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<ll.LatLng?> geocodeHighPrecision(String locationName) async {
    final query = locationName.trim();
    if (query.isEmpty) return null;

    // 0. High-precision direct coordinate parsing (e.g. "12.9716, 77.5946" or "Location (12.9716, 77.5946)")
    final coordMatch = RegExp(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)').firstMatch(query);
    if (coordMatch != null) {
      final lat = double.tryParse(coordMatch.group(1)!);
      final lng = double.tryParse(coordMatch.group(2)!);
      if (lat != null && lng != null) {
        return ll.LatLng(lat, lng);
      }
    }

    // 1. Try backend stop coordinates first
    try {
      final res = await fetchStopCoords([query]);
      final coords = res?['coordinates'] as Map<String, dynamic>?;
      if (coords != null && coords.containsKey(query)) {
        final c = coords[query] as Map<String, dynamic>;
        final lat = (c['lat'] as num?)?.toDouble();
        final lng = (c['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          return ll.LatLng(lat, lng);
        }
      }
    } catch (_) {}

    // 2. High-precision Nominatim OSM Geocoding
    try {
      final searchQuery = query.toLowerCase().contains('bengaluru') || query.toLowerCase().contains('bangalore')
          ? query
          : '$query, Bengaluru, Karnataka, India';
      final url = Uri.parse(
        'https://nominatim.openstreetmap.org/search?q=${Uri.encodeComponent(searchQuery)}&format=json&limit=1',
      );
      final res = await http.get(
        url,
        headers: {'User-Agent': 'BMTC_Commuter_App/1.0'},
      ).timeout(const Duration(seconds: 4));

      if (res.statusCode == 200) {
        final list = json.decode(res.body) as List<dynamic>?;
        if (list != null && list.isNotEmpty) {
          final item = list.first as Map<String, dynamic>;
          final lat = double.tryParse(item['lat']?.toString() ?? '');
          final lng = double.tryParse(item['lon']?.toString() ?? '');
          if (lat != null && lng != null) {
            return ll.LatLng(lat, lng);
          }
        }
      }
    } catch (_) {}

    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // REVERSE GEOCODING (Coordinates -> Place Name)
  // ═══════════════════════════════════════════════════════════════════════════

  static Future<String?> reverseGeocode(double lat, double lng) async {
    try {
      final url = Uri.parse(
        'https://nominatim.openstreetmap.org/reverse?format=json&lat=$lat&lon=$lng&zoom=18&addressdetails=1',
      );
      final res = await http.get(
        url,
        headers: {'User-Agent': 'BMTC_Commuter_App/1.0'},
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final display = data['display_name']?.toString();
        final address = data['address'] as Map<String, dynamic>?;

        if (address != null) {
          final place = address['suburb'] ??
              address['neighbourhood'] ??
              address['amenity'] ??
              address['road'] ??
              address['city_district'];
          if (place != null && place.toString().isNotEmpty) {
            return '$place, Bengaluru';
          }
        }
        if (display != null && display.isNotEmpty) {
          final parts = display.split(',');
          return parts.take(2).join(',').trim();
        }
      }
    } catch (_) {}
    return '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
  }

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
  static Future<bool> saveJourney({
    required String fromStop,
    required String toStop,
    required String mode,
    required int cost,
    required int duration,
    required double distance,
    bool isSaved = false,
    String? customName,
  }) async {
    final now = DateTime.now();
    final today = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    final res = await _postAuth('/api/user/journey', {
      'from_stop': fromStop,
      'to_stop': toStop,
      'mode': mode,
      'cost': cost,
      'duration': duration,
      'distance': distance,
      'date': today,
      'is_saved': isSaved,
      'custom_name': customName,
    });
    return res != null;
  }

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

  static Future<bool> addDocument(String docType, String docNumber, String expiryDate, {List<int>? bytes, String? filename}) async {
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/api/user/documents'));
      req.headers.addAll(authHeaders);
      req.fields['doc_type'] = docType;
      req.fields['doc_number'] = docNumber;
      req.fields['expiry_date'] = expiryDate;

      final fileBytes = bytes ?? [65, 66, 67, 68];
      final fname = filename ?? '${docType.replaceAll(RegExp(r'\s+'), '_')}.pdf';
      req.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fname));

      final streamedRes = await req.send().timeout(const Duration(seconds: 12));
      final res = await http.Response.fromStream(streamedRes);
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> deleteDocument(int docId) async =>
      _deleteAuth('/api/user/documents/$docId');

  // ═══════════════════════════════════════════════════════════════════════════
  // HEALTH CHECK & AUTO FAILOVER
  // ═══════════════════════════════════════════════════════════════════════════

  static final List<String> candidateUrls = [
    'https://light-hairs-go.loca.lt',
    'http://192.168.0.103:8000',
    'http://localhost:8000',
  ];

  static Future<bool> _testUrl(String targetUrl) async {
    try {
      final res = await http.get(
        Uri.parse('$targetUrl/api/cab/providers'),
        headers: authHeaders,
      ).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> checkHealth() async {
    if (await _testUrl(baseUrl)) return true;

    for (final candidate in candidateUrls) {
      if (candidate != baseUrl && await _testUrl(candidate)) {
        baseUrl = candidate;
        debugPrint("ApiService auto-switched active baseUrl to: $baseUrl");
        return true;
      }
    }
    return false;
  }
}
