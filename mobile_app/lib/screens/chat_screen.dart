import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/app_settings_modal.dart';
import '../utils/geolocation_helper.dart';
import '../widgets/chat_embedded_widgets.dart';

class ChatScreen extends StatefulWidget {
  final ValueChanged<Map<String, String>>? onPlanJourney;

  const ChatScreen({super.key, this.onPlanJourney});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _isLoading = false;
  String? _sessionId;

  final List<String> _initialPromptChips = [
    'Ola fare from Majestic to Indiranagar',
    'Nearest restaurants',
    'Hotels near Majestic',
    'Tourist places in Bangalore',
    'Nearest bus stop to Bangalore Palace',
    'Fuel cost: Whitefield to Electronic City by car',
    'Will it rain at 5 PM today?',
    'Traffic from MG Road to Hebbal?',
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(
      _ChatMessage(
        text: "Namaskara! 🙏 I am your Bengaluru Intelligent Transport Assistant. Ask me routes, fares, BMTC buses, Namma Metro, cab estimates, fuel costs, traffic status, or nearby restaurants, hotels, and tourist places!",
        isUser: false,
        timestamp: DateTime.now(),
        suggestedFollowups: [
          'Show routes to Majestic',
          'Metro vs Cab to Indiranagar',
          'Nearest restaurants',
          'Will it rain today?',
        ],
      ),
    );
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _sendMessage(String text) async {
    final msg = text.trim();
    if (msg.isEmpty || _isLoading) return;

    _textCtrl.clear();
    setState(() {
      _messages.add(_ChatMessage(text: msg, isUser: true, timestamp: DateTime.now()));
      _isLoading = true;
    });

    _scrollToBottom();

    // Collect lightweight history
    final history = _messages.map((m) => {
      'sender': m.isUser ? 'user' : 'bot',
      'text': m.text,
    }).toList();

    double? lat;
    double? lng;
    final lower = msg.toLowerCase();
    final needsLoc = lower.contains("near") ||
        lower.contains("around") ||
        lower.contains("from here") ||
        lower.contains("closest") ||
        lower.contains("here") ||
        lower.contains("current location") ||
        lower.contains("my location") ||
        lower.contains("where am i") ||
        lower.contains("restaurant") ||
        lower.contains("food") ||
        lower.contains("hotel") ||
        lower.contains("tourist") ||
        lower.contains("attraction") ||
        lower.contains("sightseeing") ||
        lower.contains("places");
    if (needsLoc) {
      try {
        final pos = await GeolocationHelper.getCurrentPosition().timeout(const Duration(seconds: 2), onTimeout: () => null);
        if (pos != null) {
          lat = pos.latitude;
          lng = pos.longitude;
        }
      } catch (_) {}
    }

    Map<String, dynamic>? res;
    try {
      res = await ApiService.queryChatbot(
        message: msg,
        history: history,
        sessionId: _sessionId,
        latitude: lat,
        longitude: lng,
      );
      if (res?['session_id'] != null) {
        _sessionId = res!['session_id'].toString();
      }
    } catch (e) {
      debugPrint('[ChatScreen] Error querying chatbot: $e');
    }

    if (!mounted) return;

    String? reply = res?['text']?.toString() ??
        res?['answer']?.toString() ??
        res?['response']?.toString() ??
        res?['message']?.toString();

    String? intent = res?['intent']?.toString();
    Map<String, dynamic>? params = res?['parameters'] as Map<String, dynamic>?;
    Map<String, dynamic>? embeddedData = res?['embedded_data'] as Map<String, dynamic>?;
    List<String> followups = (res?['suggested_followups'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];

    if (reply == null || reply.isEmpty) {
      final fallback = _generateTransitAssistantReply(msg);
      reply = fallback['text']?.toString() ?? "I am ready to help with Bengaluru transit! Ask about BMTC buses, Metro routes, cab fares, or weather.";
      intent = fallback['intent']?.toString();
      params = fallback['parameters'] as Map<String, dynamic>?;
      embeddedData = fallback['embedded_data'] as Map<String, dynamic>?;
      followups = (fallback['suggested_followups'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    }

    setState(() {
      _isLoading = false;
      _messages.add(
        _ChatMessage(
          text: reply ?? "I am ready to help with Bengaluru transit!",
          isUser: false,
          timestamp: DateTime.now(),
          intent: intent,
          parameters: params,
          embeddedData: embeddedData,
          suggestedFollowups: followups,
        ),
      );
    });

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent + 120,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _triggerPlanRoute(String source, String destination, String? mode) {
    if (widget.onPlanJourney != null) {
      final Map<String, String> data = {
        'source': source,
        'destination': destination,
      };
      if (mode != null) data['mode'] = mode;
      widget.onPlanJourney!(data);
      Navigator.of(context).maybePop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(7),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFF97316), Color(0xFF8B5CF6)],
                ),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text('🤖', style: TextStyle(fontSize: 16)),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Commuter Assistant', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                Row(
                  children: [
                    Icon(Icons.circle, color: Color(0xFF10B981), size: 8),
                    SizedBox(width: 4),
                    Text('All modes • Online', style: TextStyle(fontSize: 10, color: Color(0xFF10B981), fontWeight: FontWeight.bold)),
                  ],
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'App Settings',
            onPressed: () => showAppSettingsModal(context),
          ),
        ],
      ),
      body: Column(
        children: [
          // Prompt suggestion chips bar
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              children: _initialPromptChips.map((chip) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ActionChip(
                    backgroundColor: isDark ? const Color(0xFF1E202C) : const Color(0xFFF1F5F9),
                    side: BorderSide(color: AppTheme.getBorder(isDark)),
                    label: Text(chip, style: TextStyle(fontSize: 11, color: textColor)),
                    onPressed: () => _sendMessage(chip),
                  ),
                );
              }).toList(),
            ),
          ),
          const Divider(height: 1),

          // Message list
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(14),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildMessageItem(msg, isDark, textColor, mutedColor);
              },
            ),
          ),

          if (_isLoading)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              child: Row(
                children: [
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF7C3AED)),
                  ),
                  const SizedBox(width: 10),
                  Text('Thinking...', style: TextStyle(fontSize: 12, color: mutedColor, fontWeight: FontWeight.bold)),
                ],
              ),
            ),

          // Input Bar
          Container(
            padding: EdgeInsets.only(
              left: 14,
              right: 14,
              top: 8,
              bottom: MediaQuery.of(context).viewInsets.bottom + 12,
            ),
            decoration: BoxDecoration(
              color: cardBg,
              border: Border(top: BorderSide(color: AppTheme.getBorder(isDark))),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textCtrl,
                    decoration: InputDecoration(
                      hintText: 'Ask about routes, fares, buses, metro, fuel...',
                      hintStyle: TextStyle(fontSize: 13, color: mutedColor),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                    ),
                    onSubmitted: _sendMessage,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: const Color(0xFF7C3AED),
                    foregroundColor: Colors.white,
                  ),
                  onPressed: () => _sendMessage(_textCtrl.text),
                  icon: const Icon(Icons.send_rounded, size: 18),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageItem(_ChatMessage msg, bool isDark, Color textColor, Color mutedColor) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: msg.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Align(
            alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              padding: const EdgeInsets.all(14),
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
              decoration: BoxDecoration(
                color: msg.isUser
                    ? const Color(0xFFF97316)
                    : (isDark ? const Color(0xFF161822) : const Color(0xFFF8FAFC)),
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: msg.isUser ? const Radius.circular(2) : const Radius.circular(16),
                  bottomLeft: !msg.isUser ? const Radius.circular(2) : const Radius.circular(16),
                ),
                border: msg.isUser ? null : Border.all(color: AppTheme.getBorder(isDark)),
                boxShadow: msg.isUser
                    ? [BoxShadow(color: const Color(0xFFF97316).withValues(alpha: 0.25), blurRadius: 6, offset: const Offset(0, 2))]
                    : null,
              ),
              child: Text(
                msg.text,
                style: TextStyle(
                  fontSize: 13,
                  height: 1.45,
                  color: msg.isUser ? Colors.white : textColor,
                ),
              ),
            ),
          ),

          // Render Embedded Interactive Cards for Bot Responses
          if (!msg.isUser && msg.embeddedData != null) ...[
            const SizedBox(height: 6),
            _buildEmbeddedContent(msg, isDark, textColor, mutedColor),
          ],

          // Render Suggested Follow-up chips
          if (!msg.isUser && msg.suggestedFollowups.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: msg.suggestedFollowups.map((followup) {
                return InkWell(
                  onTap: () => _sendMessage(followup),
                  borderRadius: BorderRadius.circular(14),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: isDark ? const Color(0xFF1F2232) : const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      followup,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF2563EB)),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEmbeddedContent(_ChatMessage msg, bool isDark, Color textColor, Color mutedColor) {
    final embed = msg.embeddedData!;
    final intent = msg.intent;

    // 0. Multimodal Route Comparison Dashboard (Matching Website App.jsx)
    if (intent == 'journey_time' ||
        intent == 'journey_cost' ||
        intent == 'possible_ways' ||
        embed['type'] == 'comparison' ||
        embed['options'] != null) {
      return ChatComparisonDashboard(
        data: embed,
        onSelectRoute: (modeOrDest) {
          final src = msg.parameters?['source']?.toString() ?? embed['source']?.toString() ?? 'Majestic';
          final dst = msg.parameters?['destination']?.toString() ?? embed['destination']?.toString() ?? modeOrDest;
          final mode = (modeOrDest != dst) ? modeOrDest : (embed['mode']?.toString() ?? 'bmtc');
          _triggerPlanRoute(src, dst, mode);
        },
        onSendMessage: _sendMessage,
      );
    }

    // 1. Traffic Status Query Card (Matching Website 🔴/🟡/🟢)
    if (intent == 'traffic_query' || embed['type'] == 'traffic_query' || embed['congestion_level'] != null) {
      return ChatTrafficQueryCard(
        data: embed,
        onTap: () {
          final src = embed['source']?.toString() ?? msg.parameters?['source']?.toString() ?? 'Majestic';
          final dst = embed['destination']?.toString() ?? msg.parameters?['destination']?.toString() ?? 'Hebbal';
          _triggerPlanRoute(src, dst, 'car');
        },
      );
    }

    // 2. Nearest Transit Stops Card (BMTC & Metro)
    if (intent == 'nearest_stops' || embed['nearest'] != null) {
      return ChatNearestStopsCard(
        data: embed,
        onSelectStop: (stopName) {
          _triggerPlanRoute(stopName, 'Majestic', 'bmtc');
        },
      );
    }

    // 3. Weather Query Card
    if (intent == 'weather_query' || embed['type'] == 'weather') {
      return ChatWeatherCard(data: embed);
    }

    // 4. Nearby Places Suggestions Dashboard (Restaurants, Hotels, Tourist Attractions, Cafes)
    if (intent == 'nearby_pois' || embed['type'] == 'nearby_places' || embed['places'] != null) {
      return ChatNearbyPlacesDashboard(
        data: embed,
        onSelectPlace: (p) {
          final name = p['name']?.toString() ?? 'Place';
          final src = embed['location']?.toString() ?? msg.parameters?['source']?.toString() ?? 'Current Location';
          _triggerPlanRoute(src, name, 'multimodal');
        },
      );
    }

    // 2. POI Detail Card (Timings, Status, Fees, Direct BMTC Buses)
    if (intent == 'poi_detail' || embed['type'] == 'poi_detail' || embed['poi'] != null) {
      return _buildPoiDetailCard(embed, isDark, textColor, mutedColor);
    }

    // 3. Bus Timings Card
    if (intent == 'bus_schedule_query' || embed['type'] == 'bus_timings' || embed['buses'] != null) {
      return _buildBusTimingsCard(embed, isDark, textColor, mutedColor);
    }

    // 4. Detected Current Location Card
    if (intent == 'current_location' || embed['type'] == 'location') {
      return _buildLocationCard(embed, isDark, textColor, mutedColor);
    }

    // 5. Ride-Hailing Cost Estimate Card (Ola, Uber, Rapido, Namma Yatri)
    if (intent == 'ride_cost' || embed['providers'] != null) {
      final providers = embed['providers'] as Map<String, dynamic>? ?? {};
      return Container(
        width: MediaQuery.of(context).size.width * 0.85,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF1A1530) : const Color(0xFFFAF5FF),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF8B5CF6).withValues(alpha: 0.4)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.local_taxi_rounded, color: Color(0xFF8B5CF6), size: 16),
                SizedBox(width: 6),
                Text('RIDE-HAILING ESTIMATE', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF8B5CF6))),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (providers['ola'] != null)
                  _buildProviderPill('Ola', '🚕', '#f5c518', providers['ola'], textColor),
                if (providers['uber'] != null)
                  _buildProviderPill('Uber', '🚗', '#94a3b8', providers['uber'], textColor),
                if (providers['namma_yatri'] != null)
                  _buildProviderPill('Namma Yatri', '🛺', '#22c55e', providers['namma_yatri'], textColor),
                if (providers['rapido'] != null)
                  _buildProviderPill('Rapido', '🏍️', '#ea580c', providers['rapido'], textColor),
              ],
            ),
            if (embed['distance_km'] != null) ...[
              const SizedBox(height: 8),
              Text(
                '~${embed['distance_km']} km • ~${embed['duration_min'] ?? 25} min estimated drive',
                style: TextStyle(fontSize: 10, color: mutedColor, fontWeight: FontWeight.bold),
              ),
            ],
          ],
        ),
      );
    }

    // 6. Fuel Cost Estimate Card
    if (intent == 'fuel_cost' || (embed['cost'] != null && embed['fuel_litres'] != null)) {
      return Container(
        width: MediaQuery.of(context).size.width * 0.85,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF0F1A12) : const Color(0xFFF0FDF4),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF22C55E).withValues(alpha: 0.4)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.local_gas_station_rounded, color: Color(0xFF22C55E), size: 16),
                SizedBox(width: 6),
                Text('FUEL COST ESTIMATE', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF22C55E))),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('₹${embed['cost']}', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: textColor)),
                Text('${(embed['fuel_litres'] as num?)?.toStringAsFixed(2) ?? '2.10'} L', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Color(0xFF22C55E))),
              ],
            ),
          ],
        ),
      );
    }

    // 7. General Route Option Card (BMTC, Metro, Cab, Car, Multimodal)
    final mode = embed['mode']?.toString() ?? 'bmtc';
    final src = msg.parameters?['source']?.toString() ?? embed['from_stop']?.toString() ?? embed['source']?.toString() ?? 'Majestic';
    final dst = msg.parameters?['destination']?.toString() ?? embed['to_stop']?.toString() ?? embed['destination']?.toString() ?? 'Indiranagar';
    final cost = embed['cost']?.toString() ?? '25';
    final time = embed['time']?.toString() ?? '35';

    return InkWell(
      onTap: () => _triggerPlanRoute(src, dst, mode),
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width: MediaQuery.of(context).size.width * 0.85,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF1E1B2E) : const Color(0xFFFAF5FF),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.4), width: 1.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${AppTheme.getModeLabel(mode).toUpperCase()} ROUTE',
                  style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w900, color: Color(0xFF7C3AED)),
                ),
                Text(
                  '₹$cost',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: textColor),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '$src → $dst',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor),
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('⏱️ $time mins', style: TextStyle(fontSize: 11, color: mutedColor, fontWeight: FontWeight.bold)),
                const Row(
                  children: [
                    Text('Tap to plan route', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF7C3AED))),
                    Icon(Icons.arrow_forward_rounded, size: 12, color: Color(0xFF7C3AED)),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNearbyPlacesCard(Map<String, dynamic> embed, bool isDark, Color textColor, Color mutedColor) {
    final rawPlaces = embed['places'] as List<dynamic>? ?? [];
    final category = embed['category']?.toString().toLowerCase() ?? 'restaurant';
    final location = embed['location']?.toString() ?? 'Bengaluru';

    IconData headerIcon = Icons.restaurant_rounded;
    String titleText = 'RESTAURANTS & EATERIES';
    Color themeColor = const Color(0xFF10B981);

    if (category.contains('hotel') || category.contains('lodging')) {
      headerIcon = Icons.hotel_rounded;
      titleText = 'HOTELS & STAYS';
      themeColor = const Color(0xFF3B82F6);
    } else if (category.contains('attraction') || category.contains('tourist') || category.contains('place')) {
      headerIcon = Icons.landscape_rounded;
      titleText = 'TOURIST ATTRACTIONS';
      themeColor = const Color(0xFFF59E0B);
    } else if (category.contains('cafe')) {
      headerIcon = Icons.local_cafe_rounded;
      titleText = 'CAFES & COFFEE';
      themeColor = const Color(0xFFEC4899);
    }

    return Container(
      width: MediaQuery.of(context).size.width * 0.85,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF151922) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: themeColor.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(headerIcon, color: themeColor, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '$titleText NEAR ${location.toUpperCase()}',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: themeColor),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...rawPlaces.take(4).map((item) {
            final place = item as Map<String, dynamic>;
            final name = place['name']?.toString() ?? 'Place';
            final dist = place['distance_km'] != null ? '${place['distance_km']} km' : null;
            final rating = place['rating']?.toString();
            final address = place['address']?.toString() ?? 'Bengaluru';
            final specialty = place['specialty']?.toString() ?? place['cuisine']?.toString();

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1F2432) : Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          name,
                          style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: textColor),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (rating != null && rating != 'null')
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFEF3C7),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '⭐ $rating',
                            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF92400E)),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      if (dist != null) ...[
                        Text('📍 ~$dist', style: TextStyle(fontSize: 10.5, color: mutedColor, fontWeight: FontWeight.bold)),
                        const SizedBox(width: 8),
                      ],
                      if (specialty != null)
                        Expanded(
                          child: Text('• $specialty', style: TextStyle(fontSize: 10.5, color: mutedColor), maxLines: 1, overflow: TextOverflow.ellipsis),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          address,
                          style: TextStyle(fontSize: 10, color: mutedColor),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      InkWell(
                        onTap: () => _triggerPlanRoute('Majestic', name, 'bmtc'),
                        borderRadius: BorderRadius.circular(6),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text('Plan Route', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: themeColor)),
                              Icon(Icons.arrow_forward_rounded, size: 10, color: themeColor),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildPoiDetailCard(Map<String, dynamic> embed, bool isDark, Color textColor, Color mutedColor) {
    final poi = embed['poi'] as Map<String, dynamic>? ?? {};
    final name = poi['name']?.toString() ?? 'Landmark';
    final isOpen = embed['is_open'] == true;
    final statusText = embed['status']?.toString() ?? (isOpen ? 'OPEN NOW' : 'CLOSED');
    final openHours = poi['open_hours']?.toString() ?? '9:30 AM – 5:00 PM';
    final closedOn = poi['closed_on']?.toString() ?? 'None';
    final fee = poi['entry_fee_inr']?.toString() ?? '100';
    final busRoutes = (embed['bus_routes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    return Container(
      width: MediaQuery.of(context).size.width * 0.85,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1B1B28) : const Color(0xFFFFFBEB),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  name,
                  style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w900, color: textColor),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isOpen ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  isOpen ? '🟢 OPEN' : '🔴 CLOSED',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                    color: isOpen ? const Color(0xFF166534) : const Color(0xFF991B1B),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            statusText,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: isOpen ? const Color(0xFF16A34A) : const Color(0xFFDC2626),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(Icons.access_time_rounded, size: 12, color: Color(0xFFF59E0B)),
              const SizedBox(width: 4),
              Text('Timings: $openHours', style: TextStyle(fontSize: 11, color: textColor)),
            ],
          ),
          if (closedOn != 'None' && closedOn.isNotEmpty) ...[
            const SizedBox(height: 3),
            Row(
              children: [
                const Icon(Icons.calendar_today_rounded, size: 12, color: Color(0xFFF59E0B)),
                const SizedBox(width: 4),
                Text('Closed on: $closedOn', style: TextStyle(fontSize: 11, color: mutedColor)),
              ],
            ),
          ],
          const SizedBox(height: 3),
          Row(
            children: [
              const Icon(Icons.confirmation_number_outlined, size: 12, color: Color(0xFFF59E0B)),
              const SizedBox(width: 4),
              Text('Entry Fee: ₹$fee', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
            ],
          ),
          if (busRoutes.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('BMTC Bus Services:', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: mutedColor)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: busRoutes.map((r) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.3)),
                  ),
                  child: Text(r, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF7C3AED))),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 10),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFF59E0B),
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 32),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () => _triggerPlanRoute('Majestic', name, 'bmtc'),
            icon: const Icon(Icons.directions_bus_rounded, size: 14),
            label: Text('Plan Trip to $name', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildBusTimingsCard(Map<String, dynamic> embed, bool isDark, Color textColor, Color mutedColor) {
    final buses = embed['buses'] as List<dynamic>? ?? [];
    final src = embed['source']?.toString() ?? 'Starting Stop';
    final dst = embed['destination']?.toString() ?? 'Destination';

    return Container(
      width: MediaQuery.of(context).size.width * 0.85,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E2E) : const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.directions_bus_rounded, color: Color(0xFF10B981), size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'UPCOMING BMTC BUSES ($src ➔ $dst)',
                  style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w900, color: Color(0xFF10B981)),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...buses.take(4).map((b) {
            final route = b['route']?.toString() ?? 'BMTC';
            final dep = b['departure']?.toString() ?? 'Soon';
            final fare = b['fare'] != null ? '₹${b['fare']}' : '₹25';
            final time = b['time'] != null ? '${b['time']} min' : '45 min';
            final freq = b['frequency']?.toString() ?? 'Every 10-15 mins';

            return Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF282A36) : Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF7C3AED).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          route,
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Color(0xFF7C3AED)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Departs: $dep', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor)),
                          Text(freq, style: TextStyle(fontSize: 9.5, color: mutedColor)),
                        ],
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(fare, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: textColor)),
                      Text(time, style: TextStyle(fontSize: 9.5, color: mutedColor)),
                    ],
                  ),
                ],
              ),
            );
          }),
          const SizedBox(height: 4),
          InkWell(
            onTap: () => _triggerPlanRoute(src, dst, 'bmtc'),
            borderRadius: BorderRadius.circular(8),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 6),
              alignment: Alignment.center,
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Plan Full BMTC Route', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF10B981))),
                  SizedBox(width: 4),
                  Icon(Icons.arrow_forward_rounded, size: 12, color: Color(0xFF10B981)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLocationCard(Map<String, dynamic> embed, bool isDark, Color textColor, Color mutedColor) {
    final area = embed['area']?.toString() ?? 'Bengaluru';
    final nearestBmtc = embed['nearest_bmtc']?.toString() ?? 'BMTC Stop';
    final nearestMetro = embed['nearest_metro']?.toString();

    return Container(
      width: MediaQuery.of(context).size.width * 0.85,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF141F29) : const Color(0xFFF0F9FF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF0EA5E9).withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.my_location_rounded, color: Color(0xFF0EA5E9), size: 16),
              SizedBox(width: 6),
              Text('DETECTED CURRENT LOCATION', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w900, color: Color(0xFF0EA5E9))),
            ],
          ),
          const SizedBox(height: 6),
          Text(area, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: textColor)),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.directions_bus_outlined, size: 13, color: Color(0xFF0EA5E9)),
              const SizedBox(width: 4),
              Expanded(
                child: Text('Nearest Stop: $nearestBmtc', style: TextStyle(fontSize: 11, color: textColor)),
              ),
            ],
          ),
          if (nearestMetro != null && nearestMetro.isNotEmpty) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.subway_outlined, size: 13, color: Color(0xFF0EA5E9)),
                const SizedBox(width: 4),
                Expanded(
                  child: Text('Nearest Metro: $nearestMetro', style: TextStyle(fontSize: 11, color: textColor)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildProviderPill(String name, String icon, String hexColor, dynamic data, Color textColor) {
    String price = '₹120-180';
    if (data is List && data.isNotEmpty && data.first is Map) {
      final fMin = data.first['fare_min'];
      final fMax = data.first['fare_max'];
      if (fMin != null && fMax != null) price = '₹$fMin–$fMax';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF7C3AED).withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(icon, style: const TextStyle(fontSize: 12)),
          const SizedBox(width: 4),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(name, style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold)),
              Text(price, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: textColor)),
            ],
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _generateTransitAssistantReply(String query) {
    final q = query.toLowerCase().trim();

    // 1. Weather query
    if (q.contains('rain') || q.contains('weather') || q.contains('forecast') || q.contains('cloud') || q.contains('temp')) {
      return {
        'intent': 'weather_query',
        'text': 'The weather forecast in Bengaluru is currently clear and pleasant (~26°C). Road traffic and transit operations across BMTC Vajra buses and Namma Metro lines are running normally with no weather-induced delays.',
        'embedded_data': {
          'type': 'weather',
          'weather': 'clear',
          'time': 'Now',
          'temp': 26,
        },
        'suggested_followups': [
          'Show routes to Majestic',
          'Metro vs Cab to Indiranagar',
          'Ola fare from Majestic to Indiranagar',
        ],
      };
    }

    // 2. Cab / Auto / Ola / Uber query
    if (q.contains('ola') || q.contains('uber') || q.contains('rapido') || q.contains('yatri') || q.contains('cab') || q.contains('auto')) {
      String src = 'Majestic';
      String dst = 'Indiranagar';
      if (q.contains('to ')) {
        final parts = q.split('to ');
        if (parts.length > 1) dst = parts[1].trim();
      }
      if (q.contains('from ')) {
        final p = q.split('from ')[1].split(' to ')[0].trim();
        if (p.isNotEmpty) src = p;
      }
      return {
        'intent': 'cab_comparison',
        'text': 'Here are the estimated ride-hailing fares between $src and $dst across major Bengaluru providers:',
        'embedded_data': {
          'type': 'cabs',
          'source': src,
          'destination': dst,
          'fares': [
            {'provider': 'Namma Yatri', 'vehicle': 'Auto', 'fare': '₹85', 'eta': '3m'},
            {'provider': 'Rapido', 'vehicle': 'Auto', 'fare': '₹80', 'eta': '2m'},
            {'provider': 'Ola', 'vehicle': 'Mini', 'fare': '₹140', 'eta': '4m'},
            {'provider': 'Uber', 'vehicle': 'Go', 'fare': '₹145', 'eta': '4m'},
          ],
        },
        'suggested_followups': [
          'Compare with Metro',
          'BMTC bus route options',
          'Will it rain today?',
        ],
      };
    }

    // 3. Fuel / Vehicle query
    if (q.contains('fuel') || q.contains('petrol') || q.contains('diesel') || q.contains('mileage') || q.contains('car') || q.contains('vehicle')) {
      return {
        'intent': 'fuel_cost',
        'text': 'Estimated fuel cost for your personal vehicle drive across Bengaluru:',
        'embedded_data': {
          'type': 'fuel',
          'cost': '125',
          'distance': '14.2',
          'fuel_type': 'Petrol (₹102.86/L)',
          'mileage': '14 km/L',
        },
        'suggested_followups': [
          'Compare with BMTC bus',
          'Compare with Metro',
          'Nearest parking spot',
        ],
      };
    }

    // 4. Route query
    if (q.contains('to ') || q.contains('route') || q.contains('bus') || q.contains('metro') || q.contains('how to reach') || q.contains('majestic')) {
      String src = 'Majestic';
      String dst = 'Indiranagar';
      if (q.contains('to ')) {
        final parts = q.split('to ');
        if (parts.length > 1) dst = parts[1].trim();
      }
      if (q.contains('from ')) {
        final p = q.split('from ')[1].split(' to ')[0].trim();
        if (p.isNotEmpty) src = p;
      }
      return {
        'intent': 'journey_comparison',
        'text': 'Here are the optimal multimodal transit options from $src to $dst. BMTC buses and Namma Metro offer frequent service along this corridor.',
        'embedded_data': {
          'type': 'route',
          'source': src,
          'destination': dst,
          'mode': 'bmtc',
          'route_name': 'Direct Bus / Metro',
          'time': 32,
          'cost': 25,
          'transfers': 0,
        },
        'suggested_followups': [
          'Compare with cab',
          'Next bus timing',
          'Fastest route',
        ],
      };
    }

    // 5. Default General Transit Assistance
    return {
      'intent': 'general',
      'text': 'Namaskara! I am ready to help you navigate Bengaluru transit. You can ask for BMTC bus routes, Namma Metro schedules, Ola/Uber/Rapido fares, live weather reports, or fuel cost estimates.',
      'suggested_followups': [
        'Show routes to Majestic',
        'Metro vs Cab to Indiranagar',
        'Will it rain today?',
        'Ola fare from Majestic to Indiranagar',
      ],
    };
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? intent;
  final Map<String, dynamic>? parameters;
  final Map<String, dynamic>? embeddedData;
  final List<String> suggestedFollowups;

  _ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.intent,
    this.parameters,
    this.embeddedData,
    this.suggestedFollowups = const [],
  });
}
