import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
// ignore: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;
import '../services/api_service.dart';
import '../services/recent_searches_store.dart';
import '../theme.dart';
import '../widgets/modals.dart';
import '../widgets/app_settings_modal.dart';

class DashboardScreen extends StatefulWidget {
  final ValueNotifier<ThemeMode> themeNotifier;
  final ValueNotifier<String> mapStyleNotifier;
  final ValueNotifier<String> mapProviderNotifier;
  final String username;
  final VoidCallback onOpenLogin;
  final VoidCallback onNavigateToChat;
  final VoidCallback onNavigateToMap;
  final ValueChanged<Map<String, String>> onNavigateToPlanWithRoute;
  final VoidCallback onNavigateToTransit;
  final ValueChanged<int>? onNavigateToTransitWithTab;

  const DashboardScreen({
    super.key,
    required this.themeNotifier,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
    required this.username,
    required this.onOpenLogin,
    required this.onNavigateToChat,
    required this.onNavigateToMap,
    required this.onNavigateToPlanWithRoute,
    required this.onNavigateToTransit,
    this.onNavigateToTransitWithTab,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late String _timeString;
  late String _dateString;
  late Timer _timer;

  Map<String, dynamic>? _dashboardData;
  List<dynamic>? _vehicles;
  List<dynamic>? _documents;

  @override
  void initState() {
    super.initState();
    _timeString = _formatDateTime(DateTime.now(), 'hh:mm a');
    _dateString = _formatDateTime(DateTime.now(), 'EEE, MMM d, yyyy');
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => _getTime());
    _loadData();
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  void _getTime() {
    final now = DateTime.now();
    if (mounted) {
      setState(() {
        _timeString = _formatDateTime(now, 'hh:mm a');
        _dateString = _formatDateTime(now, 'EEE, MMM d, yyyy');
      });
    }
  }

  String _formatDateTime(DateTime dt, String format) => DateFormat(format).format(dt);

  String _getGreeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  Future<void> _loadData() async {
    final dashboard = await ApiService.fetchDashboard();
    final vehicles = await ApiService.fetchVehicles();
    final documents = await ApiService.fetchDocuments();

    if (dashboard != null) {
      final recentList = dashboard['recent'] as List<dynamic>?;
      if (recentList != null && recentList.isNotEmpty) {
        RecentSearchesStore.loadFromBackendList(recentList);
      }
    }

    if (mounted) {
      setState(() {
        _dashboardData = dashboard;
        _vehicles = vehicles;
        _documents = documents;
      });
    }
  }

  void _showAddVehicleDialog() {
    final nameCtrl = TextEditingController();
    String fuelType = 'Petrol';
    final effCtrl = TextEditingController(text: '15.0');

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Add Vehicle to Garage'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Vehicle Name (e.g. Honda City)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: fuelType,
                decoration: const InputDecoration(labelText: 'Fuel Type', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'Petrol', child: Text('Petrol')),
                  DropdownMenuItem(value: 'Diesel', child: Text('Diesel')),
                  DropdownMenuItem(value: 'Electric', child: Text('Electric (EV)')),
                  DropdownMenuItem(value: 'CNG', child: Text('CNG')),
                ],
                onChanged: (v) {
                  if (v != null) fuelType = v;
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: effCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Efficiency (km/l or km/kWh)', border: OutlineInputBorder()),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                final name = nameCtrl.text.trim();
                final eff = double.tryParse(effCtrl.text.trim()) ?? 14.0;
                if (name.isNotEmpty) {
                  await ApiService.addVehicle(name, fuelType, eff);
                  if (context.mounted) {
                    Navigator.pop(context);
                  }
                  _loadData();
                }
              },
              child: const Text('Add'),
            ),
          ],
        );
      },
    );
  }

  void _showAddDocumentDialog() {
    showDialog(
      context: context,
      builder: (context) => _AddDocumentDialog(onSaved: _loadData),
    );
  }

  Map<String, dynamic> _getDocExpiryStatus(String? expiryStr) {
    if (expiryStr == null || expiryStr.isEmpty) {
      return {'label': 'VALID', 'color': AppTheme.green};
    }
    try {
      final expiry = DateTime.parse(expiryStr);
      final now = DateTime.now();
      final diffDays = expiry.difference(now).inDays;

      if (diffDays < 0) {
        return {'label': 'EXPIRED', 'color': AppTheme.red};
      } else if (diffDays <= 30) {
        return {'label': 'EXPIRING IN ${diffDays}d', 'color': AppTheme.yellow};
      } else {
        return {'label': 'VALID', 'color': AppTheme.green};
      }
    } catch (_) {
      return {'label': 'VALID', 'color': AppTheme.green};
    }
  }

  void _openDocumentFile(Map<String, dynamic> doc) {
    final filePath = doc['file_path']?.toString() ?? '';
    final docId = doc['id'];
    final fileUrl = filePath.isNotEmpty
        ? (filePath.startsWith('http') ? filePath : '${ApiService.baseUrl}$filePath')
        : '${ApiService.baseUrl}/api/user/documents/$docId/file';

    if (kIsWeb) {
      try {
        html.window.open(fileUrl, '_blank');
      } catch (_) {}
    }

    final dType = doc['doc_type'] ?? doc['name'] ?? doc['document_type'] ?? 'Document';
    final dNum = doc['doc_number'] ?? doc['number'] ?? '';
    final dExpiry = doc['expiry_date']?.toString();
    final status = _getDocExpiryStatus(dExpiry);

    showDialog(
      context: context,
      builder: (context) {
        final isDark = Theme.of(context).brightness == Brightness.dark;
        return AlertDialog(
          backgroundColor: AppTheme.getCard(isDark),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Row(
            children: [
              const Icon(Icons.folder_special_rounded, color: Color(0xFF7C3AED), size: 24),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  dType.toString(),
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.getText(isDark)),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (dNum.toString().isNotEmpty) ...[
                Text('Document Number:', style: TextStyle(fontSize: 11, color: AppTheme.getMuted(isDark))),
                Text(dNum.toString(), style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.getText(isDark))),
                const SizedBox(height: 10),
              ],
              if (dExpiry != null) ...[
                Text('Expiry Date:', style: TextStyle(fontSize: 11, color: AppTheme.getMuted(isDark))),
                Row(
                  children: [
                    Text(dExpiry, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.getText(isDark))),
                    const SizedBox(width: 8),
                    PillBadge(text: status['label'] as String, color: status['color'] as Color, isSmall: true),
                  ],
                ),
                const SizedBox(height: 14),
              ],
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.picture_as_pdf_rounded, color: Colors.redAccent, size: 28),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Document File Link:', style: TextStyle(fontSize: 10, color: AppTheme.getMuted(isDark))),
                          Text(filePath.isNotEmpty ? filePath : '/uploads/document.pdf',
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.getText(isDark)),
                              overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF7C3AED),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () {
                if (kIsWeb) {
                  try {
                    html.window.open(fileUrl, '_blank');
                  } catch (_) {}
                }
              },
              icon: const Icon(Icons.open_in_new_rounded, size: 16),
              label: const Text('Open & View File'),
            ),
          ],
        );
      },
    );
  }

  void _showSettingsBottomSheet() {
    showAppSettingsModal(
      context,
      themeNotifier: widget.themeNotifier,
      mapStyleNotifier: widget.mapStyleNotifier,
      mapProviderNotifier: widget.mapProviderNotifier,
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);
    final mutedColor = AppTheme.getMuted(isDark);

    final journeys = _dashboardData?['saved_journeys'] as List<dynamic>? ?? [];
    final totalCO2 = _dashboardData?['total_co2_saved'] ?? 42.5;
    final trees = (totalCO2 / 20.0).toStringAsFixed(1);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bengaluru Commuter', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded),
            tooltip: 'Toggle Theme',
            onPressed: () {
              widget.themeNotifier.value = isDark ? ThemeMode.light : ThemeMode.dark;
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings',
            onPressed: _showSettingsBottomSheet,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 28),
          children: [
            // 0. Account Profile Bar (Database Sync)
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 14,
                        backgroundColor: widget.username != 'Guest'
                            ? AppTheme.green.withValues(alpha: 0.2)
                            : Colors.grey.withValues(alpha: 0.2),
                        child: Icon(
                          widget.username != 'Guest' ? Icons.person_rounded : Icons.person_outline_rounded,
                          size: 16,
                          color: widget.username != 'Guest' ? AppTheme.green : mutedColor,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.username != 'Guest' ? widget.username : 'Guest User',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor),
                          ),
                          Text(
                            widget.username != 'Guest' ? 'Synced with Transit DB' : 'Not signed in',
                            style: TextStyle(fontSize: 10, color: mutedColor),
                          ),
                        ],
                      ),
                    ],
                  ),
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      visualDensity: VisualDensity.compact,
                    ),
                    onPressed: widget.onOpenLogin,
                    icon: Icon(
                      widget.username != 'Guest' ? Icons.logout_rounded : Icons.login_rounded,
                      size: 14,
                      color: widget.username != 'Guest' ? AppTheme.red : AppTheme.bmtcColor,
                    ),
                    label: Text(
                      widget.username != 'Guest' ? 'Log Out' : 'Sign In / Register',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: widget.username != 'Guest' ? AppTheme.red : AppTheme.bmtcColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 1. Hero Greeting Banner
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7C3AED), Color(0xFF5B21B6)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _getGreeting(),
                        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          _timeString,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(_dateString, style: const TextStyle(color: Colors.white70, fontSize: 12)),
                  const SizedBox(height: 14),

                  // Quick search action
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF7C3AED),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      elevation: 0,
                    ),
                    onPressed: () {
                      widget.onNavigateToPlanWithRoute({});
                    },
                    icon: const Icon(Icons.directions_rounded, size: 18),
                    label: const Text('Plan New Journey', style: TextStyle(fontWeight: FontWeight.w800)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 2. Eco Impact & Carbon Savings Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: cardBg,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.getBorder(isDark)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.green.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.eco_rounded, color: AppTheme.green, size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Eco Impact & Sustainability', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: textColor)),
                        const SizedBox(height: 4),
                        Text('Saved $totalCO2 kg CO2 (~$trees trees equivalent) by choosing public transit!',
                            style: TextStyle(fontSize: 12, color: mutedColor, height: 1.3)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 3. Quick Transit Tools Grid
            Text('QUICK TRANSIT TOOLS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 10),
            GridView.count(
              crossAxisCount: 3,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _buildToolTile('Route Lookup', Icons.alt_route_rounded, AppTheme.bmtcColor, isDark, () {
                  if (widget.onNavigateToTransitWithTab != null) {
                    widget.onNavigateToTransitWithTab!(0);
                  } else {
                    widget.onNavigateToTransit();
                  }
                }),
                _buildToolTile('Timetables', Icons.schedule_rounded, AppTheme.metroColor, isDark, () {
                  if (widget.onNavigateToTransitWithTab != null) {
                    widget.onNavigateToTransitWithTab!(1);
                  } else {
                    widget.onNavigateToTransit();
                  }
                }),
                _buildToolTile('Stops Info', Icons.pin_drop_rounded, AppTheme.blue, isDark, () {
                  if (widget.onNavigateToTransitWithTab != null) {
                    widget.onNavigateToTransitWithTab!(3);
                  } else {
                    widget.onNavigateToTransit();
                  }
                }),
                _buildToolTile('Fare Calc', Icons.calculate_outlined, AppTheme.carColor, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const FareCalculatorModal());
                }),
                _buildToolTile('Weather', Icons.wb_sunny_outlined, Colors.amber, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const WeatherReportModal());
                }),
                _buildToolTile('Fare Guide', Icons.menu_book_rounded, AppTheme.multimodalColor, isDark, () {
                  showModalBottomSheet(context: context, isScrollControlled: true, backgroundColor: Colors.transparent, builder: (context) => const FareGuideModal());
                }),
              ],
            ),
            // 3.5 Recent Searches (Store top 5 recent searches)
            Text('RECENT SEARCHES (TOP 5)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: RecentSearchesStore.searches.map((rs) {
                final src = rs['source'] ?? '';
                final dst = rs['destination'] ?? '';
                if (src.isEmpty || dst.isEmpty) return const SizedBox.shrink();

                return InkWell(
                  onTap: () {
                    widget.onNavigateToPlanWithRoute({'source': src, 'destination': dst});
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: cardBg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.getBorder(isDark)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.history_rounded, size: 14, color: AppTheme.bmtcColor),
                        const SizedBox(width: 6),
                        Text(
                          '$src ➔ $dst',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textColor),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.chevron_right_rounded, size: 14, color: AppTheme.bmtcColor),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            // 4. Saved Journeys
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('SAVED JOURNEYS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                if (journeys.isNotEmpty)
                  Text('${journeys.length} Saved', style: TextStyle(fontSize: 11, color: mutedColor)),
              ],
            ),
            const SizedBox(height: 10),

            if (journeys.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Center(
                  child: Text('No saved journeys yet. Save your favorite routes from search!', style: TextStyle(fontSize: 12, color: mutedColor)),
                ),
              )
            else
              ...journeys.map((j) {
                final from = j['from_stop'] ?? j['from'] ?? 'Majestic';
                final to = j['to_stop'] ?? j['to'] ?? 'Indiranagar';
                final mode = j['mode'] ?? 'bmtc';
                final customName = j['custom_name'] ?? '$from ➔ $to';
                final cost = j['cost'] ?? 0;
                final dur = j['duration'] ?? 0;

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppTheme.getModeColor(mode).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(AppTheme.getModeIcon(mode), color: AppTheme.getModeColor(mode), size: 18),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(customName.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor)),
                            Text('$from ➔ $to · ₹$cost · $dur min', style: TextStyle(fontSize: 11, color: mutedColor)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                        color: AppTheme.getAccent(isDark),
                        tooltip: 'Plan This Journey',
                        onPressed: () {
                          widget.onNavigateToPlanWithRoute({'source': from.toString(), 'destination': to.toString()});
                        },
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline_rounded, size: 18, color: Colors.grey),
                        tooltip: 'Delete Saved Journey',
                        onPressed: () async {
                          final jId = j['id'];
                          if (jId != null) {
                            await ApiService.deleteJourney(jId as int);
                            _loadData();
                          }
                        },
                      ),
                    ],
                  ),
                );
              }),
            const SizedBox(height: 20),

            // 5. User Garage (Personal Vehicles)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('MY GARAGE (VEHICLES)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                TextButton.icon(
                  onPressed: _showAddVehicleDialog,
                  icon: const Icon(Icons.add, size: 14),
                  label: const Text('Add Vehicle', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 6),

            if (_vehicles == null || _vehicles!.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.directions_car_filled_rounded, color: AppTheme.carColor),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text('Add your car or two-wheeler to get exact fuel & parking estimates in journey comparisons.',
                          style: TextStyle(fontSize: 12, color: mutedColor)),
                    ),
                  ],
                ),
              )
            else
              ..._vehicles!.map((v) {
                final vId = v['id'];
                final vName = v['name'] ?? 'Car';
                final vFuel = v['fuel_type'] ?? 'Petrol';
                final vEff = v['efficiency'] ?? 15.0;

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppTheme.getBorder(isDark)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.directions_car_rounded, color: AppTheme.carColor),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(vName.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textColor)),
                            Text('$vFuel · $vEff km/l', style: TextStyle(fontSize: 11, color: mutedColor)),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline, size: 18, color: Colors.grey),
                        onPressed: () async {
                          if (vId != null) {
                            await ApiService.deleteVehicle(vId as int);
                            _loadData();
                          }
                        },
                      ),
                    ],
                  ),
                );
              }),
            // 6. Glovebox (Document Vault)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('MY GLOVEBOX (DOCUMENTS)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
                TextButton.icon(
                  onPressed: _showAddDocumentDialog,
                  icon: const Icon(Icons.add, size: 14),
                  label: const Text('Add Document', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 6),

            if (_documents == null || _documents!.isEmpty)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: cardBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.getBorder(isDark)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.folder_shared_outlined, color: Color(0xFF7C3AED)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text('Digital document vault ready for DL, RC, bus passes, and vehicle insurance.',
                          style: TextStyle(fontSize: 12, color: mutedColor)),
                    ),
                  ],
                ),
              )
            else
              ..._documents!.map((d) {
                final dId = d['id'];
                final dType = d['doc_type'] ?? d['name'] ?? d['document_type'] ?? 'Document';
                final dNum = d['doc_number'] ?? d['number'] ?? '';
                final dExpiry = d['expiry_date']?.toString();
                final status = _getDocExpiryStatus(dExpiry);

                return InkWell(
                  onTap: () => _openDocumentFile(d as Map<String, dynamic>),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 6),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: cardBg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.getBorder(isDark)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.description_rounded, size: 18, color: Color(0xFF7C3AED)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(dType.toString(), style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor)),
                              if (dNum.isNotEmpty || dExpiry != null)
                                Text('${dNum.isNotEmpty ? "No: $dNum" : ""} ${dExpiry != null ? "· Exp: $dExpiry" : ""}',
                                    style: TextStyle(fontSize: 10, color: mutedColor)),
                            ],
                          ),
                        ),
                        PillBadge(text: status['label'] as String, color: status['color'] as Color, isSmall: true),
                        IconButton(
                          icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFF7C3AED)),
                          tooltip: 'Open / View Document',
                          onPressed: () => _openDocumentFile(d as Map<String, dynamic>),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, size: 18, color: Colors.grey),
                          tooltip: 'Delete Document',
                          onPressed: () async {
                            if (dId != null) {
                              await ApiService.deleteDocument(dId as int);
                              _loadData();
                            }
                          },
                        ),
                      ],
                    ),
                  ),
                );
              }),
            const SizedBox(height: 20),

            // 7. Popular Transit Hubs in Bengaluru
            Text('POPULAR BENGALURU HUBS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: mutedColor, letterSpacing: 0.5)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildHubChip('Majestic (KBS)', 'Majestic', textColor, cardBg, isDark),
                _buildHubChip('Indiranagar 100ft', 'Indiranagar', textColor, cardBg, isDark),
                _buildHubChip('Whitefield ITPL', 'Whitefield', textColor, cardBg, isDark),
                _buildHubChip('Electronic City Phase 1', 'Electronic City', textColor, cardBg, isDark),
                _buildHubChip('Silk Board Junction', 'Silk Board', textColor, cardBg, isDark),
                _buildHubChip('Kempegowda Airport', 'Kempegowda International Airport', textColor, cardBg, isDark),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildToolTile(String title, IconData icon, Color color, bool isDark, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: isDark ? 0.12 : 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 6),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHubChip(String label, String dest, Color textColor, Color cardBg, bool isDark) {
    return ActionChip(
      backgroundColor: cardBg,
      side: BorderSide(color: AppTheme.getBorder(isDark)),
      avatar: const Icon(Icons.place_rounded, size: 14, color: AppTheme.bmtcColor),
      label: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: textColor)),
      onPressed: () {
        widget.onNavigateToPlanWithRoute({'destination': dest});
      },
    );
  }
}

class _AddDocumentDialog extends StatefulWidget {
  final VoidCallback onSaved;
  const _AddDocumentDialog({required this.onSaved});

  @override
  State<_AddDocumentDialog> createState() => _AddDocumentDialogState();
}

class _AddDocumentDialogState extends State<_AddDocumentDialog> {
  String _docType = 'Driving License';
  final _customDocTypeCtrl = TextEditingController();
  final _docNumCtrl = TextEditingController();
  final _expiryCtrl = TextEditingController(text: '2028-12-31');

  List<dynamic> _garageVehicles = [];
  String? _selectedGarageVehicle;

  String _attachedFileName = 'DL_Scan_2024.pdf';
  List<int>? _attachedBytes;
  bool _isUploading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadGarageVehicles();
  }

  Future<void> _loadGarageVehicles() async {
    try {
      final vehs = await ApiService.fetchVehicles();
      if (vehs != null && mounted) {
        setState(() {
          _garageVehicles = vehs;
          if (_garageVehicles.isNotEmpty) {
            _selectedGarageVehicle = _garageVehicles.first['name']?.toString();
          }
        });
      }
    } catch (_) {}
  }

  void _pickDocumentFile() {
    if (kIsWeb) {
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
                setState(() {
                  _attachedFileName = file.name;
                  _attachedBytes = result.toList();
                });
              }
            });
          }
        });
        return;
      } catch (_) {}
    }

    final cleanType = (_docType == 'Other' ? (_customDocTypeCtrl.text.trim().isNotEmpty ? _customDocTypeCtrl.text.trim() : 'Document') : _docType)
        .replaceAll(RegExp(r'[^a-zA-Z0-9]'), '_');
    setState(() {
      _attachedFileName = '${cleanType}_Uploaded_Scan.pdf';
      _attachedBytes = [80, 68, 70, 45, 49, 46, 52, 10, 37, 195, 196, 197, 198];
    });
  }

  @override
  void dispose() {
    _customDocTypeCtrl.dispose();
    _docNumCtrl.dispose();
    _expiryCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = AppTheme.getCard(isDark);
    final textColor = AppTheme.getText(isDark);

    return AlertDialog(
      backgroundColor: cardBg,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: Text('Add Document to Glovebox', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: textColor)),
      content: SingleChildScrollView(
        child: SizedBox(
          width: MediaQuery.of(context).size.width * 0.85,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Garage Vehicle Selection
              DropdownButtonFormField<String>(
                isExpanded: true,
                initialValue: _selectedGarageVehicle,
                decoration: const InputDecoration(
                  labelText: 'Select Garage Vehicle',
                  border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                  contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
                items: [
                  const DropdownMenuItem<String>(value: null, child: Text('General / All Vehicles', overflow: TextOverflow.ellipsis)),
                  ..._garageVehicles.map((v) => DropdownMenuItem<String>(
                        value: v['name']?.toString(),
                        child: Text('${v['name']} (${v['fuel_type'] ?? "Vehicle"})', overflow: TextOverflow.ellipsis),
                      )),
                ],
                onChanged: (v) {
                  setState(() => _selectedGarageVehicle = v);
                },
              ),
              const SizedBox(height: 14),

              // 2. Document Type (Includes Other option)
              DropdownButtonFormField<String>(
                isExpanded: true,
                initialValue: _docType,
                decoration: const InputDecoration(
                  labelText: 'Document Type',
                  border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                  contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
                items: const [
                  DropdownMenuItem(value: 'Driving License', child: Text('Driving License', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'Registration Certificate (RC)', child: Text('Registration Certificate (RC)', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'Insurance Policy', child: Text('Insurance Policy', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'Pollution Under Control (PUC)', child: Text('Pollution Under Control (PUC)', overflow: TextOverflow.ellipsis)),
                  DropdownMenuItem(value: 'Other', child: Text('Other (Custom Document)', overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (v) {
                  if (v != null) {
                    setState(() {
                      _docType = v;
                      if (v != 'Other') {
                        _attachedFileName = '${v.replaceAll(RegExp(r'[^a-zA-Z0-9]'), '_')}_Doc.pdf';
                      }
                    });
                  }
                },
              ),
              const SizedBox(height: 14),

              // Custom Document Name field if "Other" is chosen
              if (_docType == 'Other') ...[
                TextField(
                  controller: _customDocTypeCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Custom Document Type Name',
                    hintText: 'e.g. Vehicle Permit, Road Tax Receipt',
                    border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                    contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                ),
                const SizedBox(height: 14),
              ],

              // 3. Document Number
              TextField(
                controller: _docNumCtrl,
                decoration: const InputDecoration(
                  labelText: 'Document Number',
                  hintText: 'e.g. KA01-2024-00123',
                  border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                  contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
              ),
              const SizedBox(height: 14),

              // 4. Expiry Date
              TextField(
                controller: _expiryCtrl,
                decoration: const InputDecoration(
                  labelText: 'Expiry Date (YYYY-MM-DD)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                  contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
              ),
              const SizedBox(height: 14),

              // 5. Document Attachment Upload Box
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.bmtcColor.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.picture_as_pdf_rounded, color: Colors.redAccent, size: 28),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Attached Document File:', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.getMuted(isDark))),
                          Text(_attachedFileName, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor), overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.bmtcColor.withValues(alpha: 0.15),
                        foregroundColor: AppTheme.bmtcColor,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      ),
                      icon: const Icon(Icons.upload_file_rounded, size: 16),
                      label: const Text('Browse File', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                      onPressed: _pickDocumentFile,
                    ),
                  ],
                ),
              ),

              if (_error != null) ...[
                const SizedBox(height: 10),
                Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isUploading ? null : () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.bmtcColor,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          ),
          onPressed: _isUploading
              ? null
              : () async {
                  final effectiveType = _docType == 'Other'
                      ? (_customDocTypeCtrl.text.trim().isNotEmpty ? _customDocTypeCtrl.text.trim() : 'Other Document')
                      : _docType;
                  final docNum = _docNumCtrl.text.trim();
                  final expiry = _expiryCtrl.text.trim();

                  if (docNum.isEmpty || expiry.isEmpty) {
                    setState(() => _error = 'Please enter document number and expiry date.');
                    return;
                  }

                  final fullDocType = _selectedGarageVehicle != null
                      ? '$effectiveType ($_selectedGarageVehicle)'
                      : effectiveType;

                  final nav = Navigator.of(context);
                  setState(() {
                    _isUploading = true;
                    _error = null;
                  });

                  final success = await ApiService.addDocument(
                    fullDocType,
                    docNum,
                    expiry,
                    bytes: _attachedBytes,
                    filename: _attachedFileName,
                  );

                  if (mounted) {
                    setState(() => _isUploading = false);
                    if (success) {
                      nav.pop();
                      widget.onSaved();
                    } else {
                      setState(() => _error = 'Failed to upload document.');
                    }
                  }
                },
          icon: _isUploading
              ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : const Icon(Icons.cloud_upload_rounded, size: 16),
          label: Text(_isUploading ? 'Uploading...' : 'Upload & Save'),
        ),
      ],
    );
  }
}
