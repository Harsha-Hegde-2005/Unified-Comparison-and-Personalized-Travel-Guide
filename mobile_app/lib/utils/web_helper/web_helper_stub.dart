import 'dart:async';
import 'package:latlong2/latlong.dart';

class WebHelper {
  static void openUrl(String url) {}

  static void triggerFileUpload(Function(String filename, List<int> bytes) onFileSelected) {}

  static String? getLocalStorage(String key) => null;

  static void setLocalStorage(String key, String value) {}

  static Future<LatLng?> getCurrentPosition({bool highAccuracy = true}) async => null;

  static Stream<LatLng> watchPositionStream() => const Stream.empty();
}
