// ignore_for_file: deprecated_member_use
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'web_helper/web_helper.dart';

enum LocationCheckStatus {
  success,
  serviceDisabled,
  permissionDenied,
  permissionPermanentlyDenied,
  error,
}

class LocationResult {
  final LocationCheckStatus status;
  final LatLng? position;
  final String? message;

  const LocationResult({
    required this.status,
    this.position,
    this.message,
  });
}

class GeolocationHelper {
  /// Fetch current GPS position with full status checks (service enabled, permissions, error)
  static Future<LocationResult> getPositionWithStatus() async {
    if (kIsWeb) {
      final webPos = await WebHelper.getCurrentPosition(highAccuracy: true);
      if (webPos != null) {
        return LocationResult(status: LocationCheckStatus.success, position: webPos);
      }
      final fallbackPos = await WebHelper.getCurrentPosition(highAccuracy: false);
      if (fallbackPos != null) {
        return LocationResult(status: LocationCheckStatus.success, position: fallbackPos);
      }
      return const LocationResult(status: LocationCheckStatus.error, message: 'Could not obtain location in browser');
    }

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return const LocationResult(
          status: LocationCheckStatus.serviceDisabled,
          message: 'Location services are disabled on your device. Please turn on GPS.',
        );
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return const LocationResult(
            status: LocationCheckStatus.permissionDenied,
            message: 'Location permission was denied.',
          );
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return const LocationResult(
          status: LocationCheckStatus.permissionPermanentlyDenied,
          message: 'Location permissions are permanently denied. Please enable them in App Settings.',
        );
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );
      return LocationResult(
        status: LocationCheckStatus.success,
        position: LatLng(position.latitude, position.longitude),
      );
    } catch (e) {
      debugPrint("Error fetching native GPS location: $e");
      return LocationResult(
        status: LocationCheckStatus.error,
        message: e.toString(),
      );
    }
  }

  /// Fetch current single GPS position - returns null if disabled or denied (no silent fake coords)
  static Future<LatLng?> getCurrentPosition() async {
    final res = await getPositionWithStatus();
    return res.position;
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

  /// Calculate straight-line distance in km between two coordinates
  static double distanceBetween(double startLatitude, double startLongitude, double endLatitude, double endLongitude) {
    final double distMeters = Geolocator.distanceBetween(startLatitude, startLongitude, endLatitude, endLongitude);
    return distMeters / 1000.0;
  }
}
