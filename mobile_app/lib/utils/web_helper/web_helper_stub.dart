import 'dart:async';
import 'dart:io';
import 'package:latlong2/latlong.dart';

class WebHelper {
  static void openUrl(String url) {
    try {
      if (Platform.isWindows) {
        Process.run('cmd', ['/c', 'start', '', url]);
      } else if (Platform.isMacOS) {
        Process.run('open', [url]);
      } else if (Platform.isLinux) {
        Process.run('xdg-open', [url]);
      }
    } catch (_) {}
  }

  static void triggerFileUpload(Function(String filename, List<int> bytes) onFileSelected) {}

  static String? getLocalStorage(String key) => null;

  static void setLocalStorage(String key, String value) {}

  static Future<LatLng?> getCurrentPosition({bool highAccuracy = true}) async => null;

  static Stream<LatLng> watchPositionStream() => const Stream.empty();
}
