// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:latlong2/latlong.dart';
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

class GeolocationHelper {
  /// Fetch current single GPS position with strict 2-second timeout
  static Future<LatLng?> getCurrentPosition() async {
    if (kIsWeb) {
      try {
        final pos = await html.window.navigator.geolocation
            .getCurrentPosition()
            .timeout(const Duration(milliseconds: 2000));
        final lat = pos.coords?.latitude?.toDouble();
        final lng = pos.coords?.longitude?.toDouble();
        if (lat != null && lng != null) {
          return LatLng(lat, lng);
        }
      } catch (_) {}
    }
    // Instant fallback coordinates (PES University / City Center)
    return const LatLng(12.9352, 77.5358);
  }

  /// Watch live continuous GPS position stream
  static Stream<LatLng> watchPositionStream() {
    final controller = StreamController<LatLng>.broadcast();

    if (kIsWeb) {
      try {
        final watchStream = html.window.navigator.geolocation.watchPosition();
        watchStream.listen((pos) {
          final lat = pos.coords?.latitude?.toDouble();
          final lng = pos.coords?.longitude?.toDouble();
          if (lat != null && lng != null && !controller.isClosed) {
            controller.add(LatLng(lat, lng));
          }
        });
      } catch (_) {}
    }

    return controller.stream;
  }
}
