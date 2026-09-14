// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'web_helper/web_helper.dart';

class GeolocationHelper {
  /// Fetch current single GPS position with high accuracy and reliable timeouts
  static Future<LatLng?> getCurrentPosition() async {
    if (kIsWeb) {
      final webPos = await WebHelper.getCurrentPosition(highAccuracy: true);
      if (webPos != null) return webPos;
      final fallbackPos = await WebHelper.getCurrentPosition(highAccuracy: false);
      if (fallbackPos != null) return fallbackPos;
      return const LatLng(12.9716, 77.5946);
    }

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        // Location services are disabled
        return const LatLng(12.9716, 77.5946);
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return const LatLng(12.9716, 77.5946);
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return const LatLng(12.9716, 77.5946);
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 8),
        ),
      );
      return LatLng(position.latitude, position.longitude);
    } catch (e) {
      debugPrint("Error fetching native GPS location: $e");
      return const LatLng(12.9716, 77.5946);
    }
  }

  /// Watch live continuous GPS position stream with adaptive fallback
  static Stream<LatLng> watchPositionStream() {
    if (kIsWeb) {
      return WebHelper.watchPositionStream();
    }

    StreamController<LatLng> controller = StreamController<LatLng>.broadcast();

    // Check permission and subscribe
    () async {
      try {
        bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
        if (!serviceEnabled) return;

        LocationPermission permission = await Geolocator.checkPermission();
        if (permission == LocationPermission.denied) {
          permission = await Geolocator.requestPermission();
        }
        if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
          return;
        }

        const locationSettings = LocationSettings(
          accuracy: LocationAccuracy.bestForNavigation,
          distanceFilter: 1, // 1 meter updates for 0ms latency live tracking
        );

        Geolocator.getPositionStream(locationSettings: locationSettings).listen(
          (Position pos) {
            if (!controller.isClosed) {
              controller.add(LatLng(pos.latitude, pos.longitude));
            }
          },
          onError: (e) {
            debugPrint("GPS position stream error: $e");
          },
        );
      } catch (e) {
        debugPrint("Error initializing native GPS stream: $e");
      }
    }();

    return controller.stream;
  }
}
