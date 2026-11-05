import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'tts_helper.dart';

/// Navigation mode for voice alert cadence
enum VoiceNavMode {
  bus,
  metro,
  personalVehicle,
  walking,
}

/// Advanced, noise-free voice guidance and alert engine for BMTC transit,
/// walking, and personal vehicles.
///
/// Cadence Rules:
/// 1. Bus / Metro Mode:
///    - NEVER gives distance-based alerts every few meters.
///    - Gives announcements ONLY on Stop Arrival / Departure.
///    - Escalates frequency & urgency at destination approach:
///        * 3 stops away: "Destination is 3 stops away. Prepare your belongings."
///        * 2 stops away: "Destination is 2 stops away. Prepare to get down."
///        * 1 stop away: "Next stop is your destination! Move to exit."
///        * Destination: "Arrived at destination. Exit safely."
///        * Passed: "Warning: You have passed your destination!"
///
/// 2. Personal Vehicle (Car/Bike) & Walking Mode:
///    - Distance throttled to 200m / 500m thresholds.
///    - Long straight: Confirmation at 500m intervals.
///    - Approaching turn / maneuver:
///        * 500m ahead: "In 500 meters, prepare to..."
///        * 200m ahead: "In 200 meters, turn..."
///        * 30m: "Turn now..."
///    - Minimum 15-second gap between general messages to avoid spamming.
class VoiceNavigationEngine {
  final VoiceNavMode mode;
  final String destinationName;

  // Transit tracking state
  final Set<String> _announcedStopKeys = {};
  int _lastAnnouncedRemainingStops = -1;

  // Distance tracking state (Vehicle / Walk)
  double _lastAlertMeters = -1.0;
  DateTime? _lastSpokenTime;
  int _lastSpokenStepIndex = -1;

  bool isVoiceEnabled;

  VoiceNavigationEngine({
    required this.mode,
    required this.destinationName,
    this.isVoiceEnabled = true,
  });

  /// Reset engine state when switching buses or starting a new leg
  void resetState() {
    _announcedStopKeys.clear();
    _lastAnnouncedRemainingStops = -1;
    _lastAlertMeters = -1.0;
    _lastSpokenTime = null;
    _lastSpokenStepIndex = -1;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // A. TRANSIT (BUS & METRO) STOP ALERTS
  // ───────────────────────────────────────────────────────────────────────────

  /// Evaluates transit stop proximity and announces only when appropriate.
  /// Does NOT trigger on distance jitter.
  Future<void> onTransitStopUpdated({
    required int currentStopIndex,
    required String currentStopName,
    required String? nextStopName,
    required int remainingStops,
    required bool hasPassedDestination,
  }) async {
    if (!isVoiceEnabled) return;

    final String modeLabel = mode == VoiceNavMode.metro ? "station" : "stop";
    final String modeLabelPlural = mode == VoiceNavMode.metro ? "stations" : "stops";
    final String cleanDest = destinationName.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();
    final String cleanStop = currentStopName.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();

    String? messageToSpeak;
    String? alertKey;

    // 1. Critical Alert: Passed Destination
    if (hasPassedDestination) {
      alertKey = 'PASSED_$cleanDest';
      messageToSpeak = 'Warning: You appear to have passed your destination, $cleanDest. Please alight at the next stop.';
    }
    // 2. Arrived at Destination
    else if (remainingStops == 0) {
      alertKey = 'ARRIVED_$cleanDest';
      messageToSpeak = 'You have arrived at your destination, $cleanDest. Please check your belongings and exit safely.';
    }
    // 3. One stop away (Next stop is destination) - High Urgency
    else if (remainingStops == 1) {
      alertKey = '1_STOP_$cleanDest';
      messageToSpeak = 'Attention: The next $modeLabel is your destination, $cleanDest! Please prepare to alight now.';
    }
    // 4. Two stops away - Medium Urgency
    else if (remainingStops == 2) {
      alertKey = '2_STOPS_$cleanDest';
      messageToSpeak = 'Notice: Your destination, $cleanDest, is two $modeLabelPlural away. Please prepare to get down.';
    }
    // 5. Three stops away - Initial Alert
    else if (remainingStops == 3) {
      alertKey = '3_STOPS_$cleanDest';
      messageToSpeak = 'Attention: Your destination, $cleanDest, is three $modeLabelPlural away.';
    }
    // 6. Regular Stop Arrival (Announce current stop & next stop once)
    else if (cleanStop.isNotEmpty) {
      final stopArrivalKey = 'STOP_$cleanStop';
      if (!_announcedStopKeys.contains(stopArrivalKey)) {
        alertKey = stopArrivalKey;
        if (nextStopName != null && nextStopName.isNotEmpty) {
          final cleanNext = nextStopName.replaceAll(RegExp(r'\s*\([^)]*\)'), '').trim();
          messageToSpeak = 'Now arriving at $cleanStop. Next $modeLabel is $cleanNext.';
        } else {
          messageToSpeak = 'Now arriving at $cleanStop.';
        }
      }
    }

    // Speak and mark announced
    if (alertKey != null && messageToSpeak != null && !_announcedStopKeys.contains(alertKey)) {
      _announcedStopKeys.add(alertKey);
      _lastAnnouncedRemainingStops = remainingStops;
      await TtsHelper.speak(messageToSpeak);
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // B. ROAD (CAR / BIKE / WALK) DISTANCE & MANEUVER ALERTS
  // ───────────────────────────────────────────────────────────────────────────

  /// Evaluates distance to turn or milestone and triggers guidance at
  /// 500m, 200m, or turn point. Strictly throttled to prevent spamming.
  Future<void> onRoadDistanceUpdated({
    required double distanceToManeuverMeters,
    required String maneuverInstruction,
    required int stepIndex,
    double? totalRemainingMeters,
  }) async {
    if (!isVoiceEnabled) return;

    final now = DateTime.now();
    if (_lastSpokenTime != null && now.difference(_lastSpokenTime!).inSeconds < 12) {
      // Minimum 12-second throttle between messages to prevent spamming
      return;
    }

    final d = distanceToManeuverMeters;
    String? messageToSpeak;
    String? distanceKey;

    final isWalk = mode == VoiceNavMode.walking;
    final vehicleTerm = isWalk ? "walk" : "continue";

    // 1. Immediate Maneuver (< 30 meters)
    if (d <= 30 && _lastSpokenStepIndex != stepIndex) {
      distanceKey = 'NOW_$stepIndex';
      messageToSpeak = maneuverInstruction;
      _lastSpokenStepIndex = stepIndex;
    }
    // 2. Approaching Maneuver at 200 Meters
    else if (d <= 230 && d >= 170) {
      distanceKey = '200M_$stepIndex';
      messageToSpeak = 'In 200 meters, $maneuverInstruction';
    }
    // 3. Approaching Maneuver at 500 Meters
    else if (d <= 550 && d >= 450) {
      distanceKey = '500M_$stepIndex';
      messageToSpeak = 'In 500 meters, prepare to $maneuverInstruction';
    }
    // 4. Long straight stretch confirmation (Every ~500m interval)
    else if (totalRemainingMeters != null && totalRemainingMeters > 600) {
      if (_lastAlertMeters < 0 || (_lastAlertMeters - totalRemainingMeters) >= 500) {
        distanceKey = 'CRUISE_${(totalRemainingMeters / 500).floor()}';
        final kmStr = (totalRemainingMeters / 1000.0).toStringAsFixed(1);
        messageToSpeak = '$vehicleTerm on route towards $destinationName for $kmStr kilometers.';
        _lastAlertMeters = totalRemainingMeters;
      }
    }

    if (distanceKey != null && messageToSpeak != null && !_announcedStopKeys.contains(distanceKey)) {
      _announcedStopKeys.add(distanceKey);
      _lastSpokenTime = now;
      await TtsHelper.speak(messageToSpeak);
    }
  }
}

