import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  final ValueNotifier<ThemeMode> themeNotifier;
  final ValueNotifier<String> mapStyleNotifier;
  final ValueNotifier<String> mapProviderNotifier;
  final VoidCallback onNavigateToChat;
  final VoidCallback onNavigateToMap;
  final VoidCallback onNavigateToPlan;
  final VoidCallback onNavigateToTransit;

  const DashboardScreen({
    super.key,
    required this.themeNotifier,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
    required this.onNavigateToChat,
    required this.onNavigateToMap,
    required this.onNavigateToPlan,
    required this.onNavigateToTransit,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late String _timeString;
  late String _dateString;
  late Timer _timer;

  // Live Database States
  Map<String, dynamic>? _dashboardData;
  List<dynamic>? _vehicles;
  List<dynamic>? _documents;
  bool _isLoading = true;

  @override
  void initState() {
    _timeString = _formatDateTime(DateTime.now(), 'hh:mm a');
    _dateString = _formatDateTime(DateTime.now(), 'EEE, MMM d, yyyy');
    _timer = Timer.periodic(const Duration(seconds: 1), (Timer t) => _getTime());
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    final dashboard = await ApiService.fetchDashboard();
    final vehicles = await ApiService.fetchVehicles();
    final documents = await ApiService.fetchDocuments();

    if (mounted) {
      setState(() {
        _dashboardData = dashboard;
        _vehicles = vehicles;
        _documents = documents;
        _isLoading = false;
      });
    }
  }

  void _getTime() {
    final DateTime now = DateTime.now();
    final String formattedTime = _formatDateTime(now, 'hh:mm a');
    final String formattedDate = _formatDateTime(now, 'EEE, MMM d, yyyy');
    if (mounted) {
      setState(() {
        _timeString = formattedTime;
        _dateString = formattedDate;
      });
    }
  }

  String _formatDateTime(DateTime dateTime, String format) {
    return DateFormat(format).format(dateTime);
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  void _showSettingsBottomSheet(BuildContext context) {
    final urlController = TextEditingController(text: ApiService.baseUrl);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: isDark ? const Color(0xFF262935) : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 50,
                      height: 5,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade400,
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Application Settings',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 20),

                  // 1. Backend Server BaseURL
                  const Text('FastAPI Backend URL', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: urlController,
                    decoration: InputDecoration(
                      hintText: 'http://127.0.0.1:8000',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      suffixIcon: IconButton(
                        icon: const Icon(Icons.save),
                        onPressed: () {
                          ApiService.baseUrl = urlController.text.trim();
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Backend BaseURL saved: ${ApiService.baseUrl}')),
                          );
                        },
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // 2. Interface Theme Toggler
                  const Text('App Theme Mode', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.light_mode),
                          label: const Text('Light'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: widget.themeNotifier.value == ThemeMode.light
                                ? const Color(0xFF7C5CFF)
                                : Colors.grey.shade300,
                            foregroundColor: widget.themeNotifier.value == ThemeMode.light
                                ? Colors.white
                                : Colors.black87,
                          ),
                          onPressed: () {
                            setModalState(() {
                              widget.themeNotifier.value = ThemeMode.light;
                            });
                          },
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.dark_mode),
                          label: const Text('Dark'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: widget.themeNotifier.value == ThemeMode.dark
                                ? const Color(0xFF7C5CFF)
                                : Colors.grey.shade300,
                            foregroundColor: widget.themeNotifier.value == ThemeMode.dark
                                ? Colors.white
                                : Colors.black87,
                          ),
                          onPressed: () {
                            setModalState(() {
                              widget.themeNotifier.value = ThemeMode.dark;
                            });
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 3. Map Style Grid Selector
                  const Text('Map Style Overlay', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  ValueListenableBuilder<String>(
                    valueListenable: widget.mapStyleNotifier,
                    builder: (context, styleVal, _) {
                      return GridView.count(
                        shrinkWrap: true,
                        crossAxisCount: 2,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                        childAspectRatio: 2.8,
                        physics: const NeverScrollableScrollPhysics(),
                        children: ['standard', 'dark', 'satellite', 'terrain'].map((style) {
                          final isSelected = styleVal == style;
                          return ChoiceChip(
                            label: Text(style.toUpperCase()),
                            selected: isSelected,
                            onSelected: (val) {
                              if (val) {
                                widget.mapStyleNotifier.value = style;
                              }
                            },
                          );
                        }).toList(),
                      );
                    },
                  ),
                  const SizedBox(height: 20),

                  // 4. Map Provider Toggle
                  const Text('Map Service Provider', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  ValueListenableBuilder<String>(
                    valueListenable: widget.mapProviderNotifier,
                    builder: (context, providerVal, _) {
                      return SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'google', label: Text('Google Maps'), icon: Icon(Icons.map)),
                          ButtonSegment(value: 'osm', label: Text('OpenStreetMap'), icon: Icon(Icons.public)),
                        ],
                        selected: {providerVal},
                        onSelectionChanged: (set) {
                          widget.mapProviderNotifier.value = set.first;
                        },
                      );
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _addVehicleDialog() {
    final nameController = TextEditingController();
    final fuelController = TextEditingController(text: 'Petrol');
    final effController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        final navigator = Navigator.of(context);
        return AlertDialog(
          title: const Text('Add Vehicle'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Vehicle Name (e.g. Pulsar 160)'),
              ),
              TextField(
                controller: fuelController,
                decoration: const InputDecoration(labelText: 'Fuel Type (Petrol/Diesel/EV)'),
              ),
              TextField(
                controller: effController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Efficiency (km/l or km/kWh)'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => navigator.pop(),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                final name = nameController.text.trim();
                final fuel = fuelController.text.trim();
                final eff = double.tryParse(effController.text) ?? 15.0;
                if (name.isNotEmpty) {
                  final success = await ApiService.addVehicle(name, fuel, eff);
                  if (success) {
                    _loadData();
                  }
                }
                navigator.pop();
              },
              child: const Text('Add'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _deleteVehicle(int id) async {
    final success = await ApiService.deleteVehicle(id);
    if (success) {
      _loadData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accentPurple = const Color(0xFF7C5CFF);
    final accentGreen = const Color(0xFF10B981);

    // Extract stats or render placeholders
    final statsList = _dashboardData?['stats'] as List<dynamic>? ?? [
      {"label": "Journeys", "val": "0", "color": "#f97316"},
      {"label": "Saved", "val": "₹0", "color": "#8b5cf6"},
      {"label": "Time saved", "val": "0 hr", "color": "#f59e0b"},
      {"label": "Avg cost", "val": "₹0", "color": "#10b981"}
    ];

    final recentSearches = _dashboardData?['recent'] as List<dynamic>? ?? [];
    final savedPlaces = _dashboardData?['saved'] as List<dynamic>? ?? [];

    return Scaffold(
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. Header (Greeting, Weather, Date/Time card)
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: isDark
                              ? [const Color(0xFF312E81), const Color(0xFF1E1B4B)]
                              : [const Color(0xFF6366F1), const Color(0xFF4F46E5)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: accentPurple.withOpacity(0.2),
                            blurRadius: 8,
                            offset: const Offset(0, 4),
                          )
                        ],
                      ),
                      padding: const EdgeInsets.all(18),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _getGreeting(),
                                  style: const TextStyle(
                                    fontSize: 15,
                                    color: Colors.white70,
                                  ),
                                ),
                                Text(
                                  ApiService.loggedInUsername ?? 'Harsha',
                                  style: const TextStyle(
                                    fontSize: 26,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '🌦️ 24°C • Scattered Drizzle',
                                  style: TextStyle(
                                    fontSize: 15,
                                    color: isDark ? const Color(0xFF34D399) : const Color(0xFFA7F3D0),
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                _timeString,
                                style: const TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              Text(
                                _dateString,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.white60,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // 2. Stats Grid (Matching Website)
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 2.2,
                      children: statsList.map((stat) {
                        final label = stat['label'] ?? '';
                        final val = stat['val'] ?? '0';
                        final colorHex = stat['color'] ?? '#7C5CFF';
                        final color = Color(int.parse(colorHex.replaceFirst('#', '0xFF')));

                        return Card(
                          color: isDark ? const Color(0xFF262935) : Colors.white,
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          child: Padding(
                            padding: const EdgeInsets.all(10.0),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 18,
                                  backgroundColor: color.withOpacity(0.15),
                                  child: Icon(_getIconForLabel(label), color: color, size: 18),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        val,
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: isDark ? Colors.white : Colors.black87,
                                        ),
                                      ),
                                      Text(
                                        label,
                                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 20),

                    // 3. Quick Actions
                    const Text(
                      'Quick Actions',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 10),
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      childAspectRatio: 1.0,
                      children: [
                        _buildQuickActionCard(
                          context,
                          icon: Icons.directions_outlined,
                          label: 'Plan Journey',
                          color: Colors.blue,
                          onTap: widget.onNavigateToPlan,
                        ),
                        _buildQuickActionCard(
                          context,
                          icon: Icons.grid_view_outlined,
                          label: 'Transit Tools',
                          color: Colors.deepOrange,
                          onTap: widget.onNavigateToTransit,
                        ),
                        _buildQuickActionCard(
                          context,
                          icon: Icons.chat_bubble_outline,
                          label: 'Commute Chat',
                          color: accentPurple,
                          onTap: widget.onNavigateToChat,
                        ),
                        _buildQuickActionCard(
                          context,
                          icon: Icons.map_outlined,
                          label: 'Explore Map',
                          color: accentGreen,
                          onTap: widget.onNavigateToMap,
                        ),
                        _buildQuickActionCard(
                          context,
                          icon: Icons.settings_outlined,
                          label: 'Settings',
                          color: Colors.orange,
                          onTap: () => _showSettingsBottomSheet(context),
                        ),
                      ],
                    ),
                    const SizedBox(height: 25),

                    // 4. Recent Searches
                    _buildSectionHeader('Recent Searches'),
                    const SizedBox(height: 10),
                    if (recentSearches.isEmpty)
                      _buildEmptyCard('No recent searches yet.')
                    else
                      _buildStatusCard(
                        context: context,
                        indicatorColor: Colors.grey,
                        child: Column(
                          children: recentSearches.map((r) {
                            return ListTile(
                              leading: const Icon(Icons.history, color: Colors.grey),
                              title: Text(
                                '${r['from']} → ${r['to']}',
                                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                              ),
                              subtitle: Text(r['date'] ?? ''),
                            );
                          }).toList(),
                        ),
                      ),
                    const SizedBox(height: 20),

                    // 5. Saved Places / Routes
                    _buildSectionHeader('Saved Places'),
                    const SizedBox(height: 10),
                    if (savedPlaces.isEmpty)
                      _buildEmptyCard('No saved places yet.')
                    else
                      _buildStatusCard(
                        context: context,
                        indicatorColor: accentPurple,
                        child: Column(
                          children: savedPlaces.map((s) {
                            return ListTile(
                              leading: const Icon(Icons.star, color: Colors.amber),
                              title: Text(
                                s['custom_name'] ?? '${s['from']} → ${s['to']}',
                                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                              ),
                              subtitle: Text('${s['from']} → ${s['to']} • ${s['mode'].toString().toUpperCase()} (₹${s['cost']})'),
                            );
                          }).toList(),
                        ),
                      ),
                    const SizedBox(height: 20),

                    // 6. My Garage
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildSectionHeader('My Garage'),
                        IconButton(
                          icon: const Icon(Icons.add, color: Color(0xFF7C5CFF)),
                          onPressed: _addVehicleDialog,
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    if (_vehicles == null || _vehicles!.isEmpty)
                      _buildEmptyCard('No vehicles in your garage.')
                    else
                      _buildStatusCard(
                        context: context,
                        indicatorColor: accentGreen,
                        child: Column(
                          children: _vehicles!.map((v) {
                            return ListTile(
                              leading: const Icon(Icons.electric_car, color: Colors.blue),
                              title: Text(v['name'] ?? 'Vehicle', style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Text('${v['fuel_type']} • ${v['efficiency']} km/l'),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                                onPressed: () => _deleteVehicle(v['id']),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    const SizedBox(height: 20),

                    // 7. Digital Glovebox
                    _buildSectionHeader('Digital Glovebox'),
                    const SizedBox(height: 10),
                    if (_documents == null || _documents!.isEmpty)
                      _buildEmptyCard('No documents uploaded yet.\nSecure DL, insurance & RC here.')
                    else
                      _buildStatusCard(
                        context: context,
                        indicatorColor: Colors.blue,
                        child: Column(
                          children: _documents!.map((doc) {
                            return ListTile(
                              leading: const Icon(Icons.description, color: Colors.blue),
                              title: Text(doc['doc_type'] ?? 'Document', style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Text('No: ${doc['doc_number']} • Expiry: ${doc['expiry_date']}'),
                            );
                          }).toList(),
                        ),
                      ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildEmptyCard(String text) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Card(
      color: isDark ? const Color(0xFF262935) : Colors.white,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        child: Center(
          child: Text(
            text,
            style: const TextStyle(color: Colors.grey, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }

  IconData _getIconForLabel(String label) {
    switch (label.toLowerCase()) {
      case 'journeys':
        return Icons.map_outlined;
      case 'saved':
        return Icons.savings_outlined;
      case 'time saved':
        return Icons.access_time;
      case 'avg cost':
        return Icons.payment;
      default:
        return Icons.info_outline;
    }
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildStatusCard({
    required BuildContext context,
    required Widget child,
    required Color indicatorColor,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    return Card(
      color: cardBgColor,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 6,
              color: indicatorColor,
            ),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActionCard(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBgColor = isDark ? const Color(0xFF262935) : Colors.white;

    return Card(
      color: cardBgColor,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 28, color: color),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
