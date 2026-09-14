import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

class TtsHelper {
  static final FlutterTts _tts = FlutterTts();
  static bool _initialized = false;
  static String? _lastSpoken;

  static Future<void> init() async {
    if (_initialized) return;
    try {
      await _tts.setLanguage("en-IN");
      await _tts.setPitch(1.0);
      await _tts.setSpeechRate(0.48);
      _initialized = true;
    } catch (e) {
      debugPrint("TTS init error: $e");
    }
  }

  static Future<void> speak(String message) async {
    if (message.trim().isEmpty || message == _lastSpoken) return;
    _lastSpoken = message;
    try {
      await init();
      await _tts.stop();
      await _tts.speak(message);
    } catch (e) {
      debugPrint("TTS speak error: $e");
    }
  }

  static Future<void> stop() async {
    try {
      await _tts.stop();
    } catch (_) {}
  }
}
