import 'package:flutter/foundation.dart';

class MapThemeService {
  static final ValueNotifier<String> mapStyleNotifier = ValueNotifier<String>('standard');
  static final ValueNotifier<String> mapProviderNotifier = ValueNotifier<String>('google');

  static String get mapStyle => mapStyleNotifier.value;
  static set mapStyle(String val) => mapStyleNotifier.value = val;

  static String get mapProvider => mapProviderNotifier.value;
  static set mapProvider(String val) => mapProviderNotifier.value = val;
}
