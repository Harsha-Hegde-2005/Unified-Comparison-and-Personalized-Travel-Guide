import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [
    {
      'sender': 'bot',
      'text': 'Hello! I am your Commuter Assistant. I can help you plan your journey, find options matching your budget, check rain forecast impact, or compare transit vs. driving.\n\nTry asking:\n• *How long does it take from Majestic to Silk Board?*\n• *nearest restaurants*\n• *nearest stops*',
      'embedded_data': null,
    }
  ];
  bool _isLoading = false;

  void _sendMessage([String? preCannedText]) async {
    final text = preCannedText ?? _messageController.text.trim();
    if (text.isEmpty) return;

    if (preCannedText == null) {
      _messageController.clear();
    }

    setState(() {
      _messages.add({'sender': 'user', 'text': text, 'embedded_data': null});
      _isLoading = true;
    });
    _scrollToBottom();

    // Map history to the structure FastAPI expects: [{'sender': 'user'|'bot', 'text': '...'}]
    final history = _messages.map((m) {
      return {
        'sender': m['sender'],
        'text': m['text'],
      };
    }).toList();

    // Call the API Service
    final response = await ApiService.queryChatbot(
      message: text,
      history: history,
      latitude: 12.9716, // Majestic coordinates
      longitude: 77.5946,
    );

    setState(() {
      _isLoading = false;
      if (response != null) {
        _messages.add({
          'sender': 'bot',
          'text': response['text'] ?? 'Sorry, I got an empty response.',
          'embedded_data': response['embedded_data'],
        });
      } else {
        _messages.add({
          'sender': 'bot',
          'text': 'Sorry, I am unable to connect to the backend server. Please verify your FastAPI backend settings.',
          'embedded_data': null,
        });
      }
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;
    final primaryPurple = const Color(0xFF7C5CFF);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Commuter Assistant Chat', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: cardBgColor,
        elevation: 1,
      ),
      body: Column(
        children: [
          // 1. Messages Area
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['sender'] == 'user';
                return _buildMessageBubble(msg, isUser);
              },
            ),
          ),

          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8.0),
              child: SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF7C5CFF)),
              ),
            ),

          // 2. Pre-Canned Query Chips
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(vertical: 6),
            color: Colors.transparent,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                _buildPreCannedChip('nearest stops', Icons.directions_bus),
                _buildPreCannedChip('nearest restaurants', Icons.restaurant),
                _buildPreCannedChip('nearest malls', Icons.local_mall),
                _buildPreCannedChip('plan a trip Majestic to Indiranagar', Icons.map),
              ],
            ),
          ),

          // 3. Message Input Bar
          Container(
            padding: const EdgeInsets.all(10),
            color: cardBgColor,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: 'Ask travel queries here...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(30)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: primaryPurple,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: () => _sendMessage(),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreCannedChip(String query, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: ActionChip(
        avatar: Icon(icon, size: 16),
        label: Text(query),
        onPressed: () => _sendMessage(query),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> msg, bool isUser) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final alignment = isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final bubbleColor = isUser
        ? const Color(0xFF7C5CFF)
        : (isDark ? const Color(0xFF262935) : const Color(0xFFE2E8F0));
    final textColor = isUser ? Colors.white : (isDark ? Colors.white : Colors.black87);

    return Column(
      crossAxisAlignment: alignment,
      children: [
        Container(
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: bubbleColor,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: isUser ? const Radius.circular(16) : Radius.zero,
              bottomRight: isUser ? Radius.zero : const Radius.circular(16),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _parseCustomMarkdown(msg['text'], textColor),
              if (msg['embedded_data'] != null) ...[
                const SizedBox(height: 10),
                _buildEmbeddedDataView(msg['embedded_data']),
              ]
            ],
          ),
        ),
      ],
    );
  }

  // Custom regex markdown parser for bullet lists, bold text, and warnings
  Widget _parseCustomMarkdown(String text, Color textColor) {
    final lines = text.split('\n');
    List<Widget> children = [];

    for (var line in lines) {
      if (line.isEmpty) {
        children.add(const SizedBox(height: 4));
        continue;
      }

      var cleanLine = line.trim();
      var style = TextStyle(color: textColor, fontSize: 14);

      if (cleanLine.startsWith('### ')) {
        cleanLine = cleanLine.replaceFirst('### ', '');
        style = TextStyle(color: textColor, fontSize: 17, fontWeight: FontWeight.bold);
      } else if (cleanLine.startsWith('**') && cleanLine.endsWith('**')) {
        cleanLine = cleanLine.replaceAll('**', '');
        style = TextStyle(color: textColor, fontSize: 14, fontWeight: FontWeight.bold);
      }

      // Detect weather warning or warning indicators
      if (cleanLine.startsWith('☔') || cleanLine.startsWith('⚠️') || cleanLine.startsWith('🚗')) {
        children.add(
          Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange.withOpacity(0.1),
              border: Border.all(color: Colors.orange.withOpacity(0.3)),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(cleanLine, style: style.copyWith(color: Colors.orange.shade800)),
          ),
        );
        continue;
      }

      // Check for bold parts in bullet points (e.g. "• **BMTC Bus** to Lalbagh")
      if (cleanLine.startsWith('•') || cleanLine.startsWith('-')) {
        cleanLine = cleanLine.substring(1).trim();
        children.add(
          Padding(
            padding: const EdgeInsets.only(left: 8.0, bottom: 4.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('• ', style: TextStyle(color: textColor, fontWeight: FontWeight.bold)),
                Expanded(
                  child: Text(cleanLine, style: style),
                ),
              ],
            ),
          ),
        );
      } else {
        children.add(Text(cleanLine, style: style));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  Widget _buildComparisonView(List<dynamic> options) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '🔄 Travel Mode Comparisons',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        ...options.map((opt) {
          final mode = opt['mode']?.toString() ?? '';
          final time = opt['time'] ?? 0;
          final cost = opt['cost'] ?? 0;
          final transfers = opt['transfers'] ?? 0;
          final co2 = opt['co2_kg'] ?? 0.0;
          final walking = opt['walking_distance'] ?? 0.0;

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 6),
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: const Color(0xFF7C5CFF).withOpacity(0.1),
                child: Icon(_getIconForMode(mode), color: const Color(0xFF7C5CFF)),
              ),
              title: Text(
                _getLabelForMode(mode),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              subtitle: Text(
                '⏱️ $time mins • 💵 ₹$cost\nTransfers: $transfers • CO2: ${co2}kg • Walk: ${walking}km',
                style: const TextStyle(fontSize: 12),
              ),
              isThreeLine: true,
            ),
          );
        }).toList(),
      ],
    );
  }

  Widget _buildNearbyPlacesView(List<dynamic> places, String location, String category) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📍 Nearby ${category.toUpperCase()}s close to $location',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        ...places.map((place) {
          final name = place['name'] ?? 'POI';
          final address = place['address'] ?? '';
          final dist = place['distance_meters'] ?? 0;

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            child: ListTile(
              leading: const Icon(Icons.place, color: Colors.redAccent),
              title: Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              subtitle: Text('$address (${dist}m away)', style: const TextStyle(fontSize: 11)),
            ),
          );
        }).toList(),
      ],
    );
  }

  IconData _getIconForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
      case 'bus':
        return Icons.directions_bus;
      case 'metro':
        return Icons.subway;
      case 'multimodal':
        return Icons.directions_run;
      case 'bike':
      case 'rapido':
        return Icons.motorcycle;
      case 'car':
      case 'ola':
      case 'uber':
        return Icons.local_taxi;
      default:
        return Icons.directions_transit;
    }
  }

  String _getLabelForMode(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
        return 'BMTC Bus Service';
      case 'metro':
        return 'Namma Metro Line';
      case 'multimodal':
        return 'Multimodal Transit (Bus + Metro)';
      case 'bike':
        return 'Personal Two-Wheeler';
      case 'car':
        return 'Personal Four-Wheeler';
      case 'ola':
        return 'Ola Cabs';
      case 'uber':
        return 'Uber Taxi';
      case 'rapido':
        return 'Rapido Bike Taxi';
      case 'namma_yatri':
        return 'Namma Yatri Auto';
      default:
        return mode.toUpperCase();
    }
  }

  Widget _buildEmbeddedDataView(Map<String, dynamic> embedded) {
    // 1. Check for 'type' == 'comparison'
    if (embedded['type'] == 'comparison' && embedded.containsKey('options')) {
      return _buildComparisonView(embedded['options'] as List<dynamic>);
    }

    // 2. Check for 'type' == 'nearby_places'
    if (embedded['type'] == 'nearby_places' && embedded.containsKey('places')) {
      return _buildNearbyPlacesView(
        embedded['places'] as List<dynamic>,
        embedded['location'] ?? 'me',
        embedded['category'] ?? 'stops',
      );
    }

    // 3. Check if it is an itinerary (multi-stop day-trip plan)
    if (embedded.containsKey('itinerary')) {
      final itinerary = embedded['itinerary'] as List<dynamic>;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '🗂️ Timed Travel Schedule',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, decoration: TextDecoration.underline),
          ),
          const SizedBox(height: 6),
          ...itinerary.map((leg) {
            return Card(
              margin: const EdgeInsets.symmetric(vertical: 4),
              color: Colors.black.withOpacity(0.04),
              child: ListTile(
                dense: true,
                title: Text(
                  '${leg['from']} ➡️ ${leg['to']} via ${leg['mode']?.toString().toUpperCase()}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: Text('⏱️ ${leg['time']} mins | 💵 ₹${leg['cost']} | ☔ ${leg['weather']}'),
              ),
            );
          }),
        ],
      );
    }

    // 4. Check if it's a general single modal response (mode comparison list)
    if (embedded.containsKey('available') && embedded.containsKey('route_info')) {
      final buses = embedded['route_info'] as List<dynamic>;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('🚌 Available Bus Schedules:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          ...buses.map((bus) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 2.0),
              child: Text('• Route ${bus['route']}: ${bus['departure']} (takes ${bus['time']} mins)'),
            );
          }),
        ],
      );
    }

    return const SizedBox.shrink();
  }
}
