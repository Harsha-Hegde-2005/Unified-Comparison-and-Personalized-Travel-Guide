// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:latlong2/latlong.dart';
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

class GeolocationHelper {
  /// Fetch current single GPS position with high accuracy and reliable timeouts
  static Future<LatLng?> getCurrentPosition() async {
    if (kIsWeb) {
      try {
        final pos = await html.window.navigator.geolocation
            .getCurrentPosition(enableHighAccuracy: true)
            .timeout(const Duration(seconds: 10));
        final lat = pos.coords?.latitude?.toDouble();
        final lng = pos.coords?.longitude?.toDouble();
        if (lat != null && lng != null) {
          return LatLng(lat, lng);
        }
      } catch (_) {
        // Fallback retry with low accuracy / network positioning
        try {
          final pos = await html.window.navigator.geolocation
              .getCurrentPosition(enableHighAccuracy: false)
              .timeout(const Duration(seconds: 5));
          final lat = pos.coords?.latitude?.toDouble();
          final lng = pos.coords?.longitude?.toDouble();
          if (lat != null && lng != null) {
            return LatLng(lat, lng);
          }
        } catch (_) {}
      }
    }
    // Default fallback coordinates (Majestic Central Hub, Bengaluru)
    return const LatLng(12.9716, 77.5946);
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
