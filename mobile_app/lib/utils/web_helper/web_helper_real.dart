import 'dart:async';
// ignore: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;
import 'dart:typed_data';
import 'package:latlong2/latlong.dart';

class WebHelper {
  static void openUrl(String url) {
    try {
      html.window.open(url, '_blank');
    } catch (_) {}
  }

  static void triggerFileUpload(Function(String filename, List<int> bytes) onFileSelected) {
    try {
      final uploadInput = html.FileUploadInputElement()..accept = '.pdf,.png,.jpg,.jpeg,.doc,.docx';
      uploadInput.click();
      uploadInput.onChange.listen((e) {
        final files = uploadInput.files;
        if (files != null && files.isNotEmpty) {
          final file = files[0];
          final reader = html.FileReader();
          reader.readAsArrayBuffer(file);
          reader.onLoadEnd.listen((e) {
            final result = reader.result;
            if (result is Uint8List) {
              onFileSelected(file.name, result.toList());
            }
          });
        }
      });
    } catch (_) {}
  }

  static String? getLocalStorage(String key) {
    try {
      return html.window.localStorage[key];
    } catch (_) {
      return null;
    }
  }

  static void setLocalStorage(String key, String value) {
    try {
      html.window.localStorage[key] = value;
    } catch (_) {}
  }

  static Future<LatLng?> getCurrentPosition({bool highAccuracy = true}) async {
    try {
      final pos = await html.window.navigator.geolocation
          .getCurrentPosition(
            enableHighAccuracy: highAccuracy,
            timeout: const Duration(seconds: 2),
            maximumAge: const Duration(seconds: 1),
          );
      final lat = pos.coords?.latitude?.toDouble();
      final lng = pos.coords?.longitude?.toDouble();
      if (lat != null && lng != null) {
        return LatLng(lat, lng);
      }
    } catch (_) {}
    return null;
  }

  static Stream<LatLng> watchPositionStream() {
    final controller = StreamController<LatLng>.broadcast();
    try {
      final watchStream = html.window.navigator.geolocation.watchPosition(
        enableHighAccuracy: false,
        maximumAge: const Duration(seconds: 1),
      );
      watchStream.listen((pos) {
        final lat = pos.coords?.latitude?.toDouble();
        final lng = pos.coords?.longitude?.toDouble();
        if (lat != null && lng != null && !controller.isClosed) {
          controller.add(LatLng(lat, lng));
        }
      });
    } catch (_) {}
    return controller.stream;
  }
}
